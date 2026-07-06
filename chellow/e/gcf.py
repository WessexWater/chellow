import csv
from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta


from sqlalchemy import select
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

from zish import dumps

from chellow.e.elexon import download_file
from chellow.models import Contract, GspGroup, RateScript
from chellow.utils import (
    ct_datetime,
    date_format,
    hh_range,
    to_ct,
    to_utc,
)

RUNS = ["DF", "RF", "R3", "R2", "R1", "SF", "II"]


def key_format(dt):
    return date_format(dt)[-8:]


def hh(data_source, run="DF"):
    gsp_group_code = data_source.gsp_group_code
    use_runs = RUNS[RUNS.index(run) :]

    try:
        cache = data_source.caches["gcfs"]
    except KeyError:
        cache = data_source.caches["gcfs"] = {}

    for h in data_source.hh_data:
        try:
            h["gcf"] = gcf = cache[h["start-date"]][gsp_group_code][run]
        except KeyError:
            h_start = h["start-date"]
            vals = data_source.non_core_rate("gcfs", h_start, exact=True)
            if vals is None:
                vals = data_source.non_core_rate("gcfs", h["hist-start"])

            rates = vals["gcfs"]

            key = key_format(h_start)
            try:
                rate = rates[key]
            except KeyError:
                rate = sorted(rates.items())[-1][1]

            try:
                gsp_rate = rate[gsp_group_code]
            except KeyError:
                gsp_rate = sorted(rate.items())[-1][1]

            polarity = "import" if data_source.is_import else "export"
            gcf = None
            for use_run in use_runs:
                try:
                    h["gcf"] = gcf = float(gsp_rate[use_run][polarity])
                    break
                except KeyError:
                    pass

            if gcf is None:
                h["gcf"] = gcf = float(sorted(gsp_rate.items())[-1][1][polarity])

            try:
                rates_cache = cache[h["start-date"]]
            except KeyError:
                rates_cache = cache[h["start-date"]] = {}

            try:
                gsp_cache = rates_cache[gsp_group_code]
            except KeyError:
                gsp_cache = rates_cache[gsp_group_code] = {}

            gsp_cache[run] = gcf


def _find_complete_date(caches, sess, contract):
    gcf_data = {}
    complete_date = None
    gsp_group_codes = [g.code for g in sess.scalars(select(GspGroup))]
    for rs in sess.scalars(
        select(RateScript)
        .where(RateScript.contract == contract, RateScript.finish_date != null())
        .order_by(RateScript.start_date.desc())
    ):
        rates = rs.make_script()
        try:
            gcfs = rates["gcfs"]
        except KeyError:
            break

        complete = True
        for dt in hh_range(caches, rs.start_date, rs.finish_date):
            key = key_format(dt)
            if key in gcfs:
                gps = gcfs[key]
                gcf_data[dt] = gps

                for group in gsp_group_codes:
                    if group in gps:
                        gp = gps[group]
                        if "DF" in gp:
                            vals = gp["DF"]
                            if "export" not in vals or "import" not in vals:
                                complete = False
                        else:
                            complete = False
                    else:
                        complete = False

            else:
                complete = False

        if complete:
            complete_date = rs.finish_date
            break

    return complete_date, gcf_data


def elexon_import(sess, log, set_progress, scripting_key):
    import_gcfs(sess, log, set_progress, scripting_key)


def _gcf_months(gcf_data):
    month_start, gcfs = None, {}
    for dt, vals in sorted(gcf_data.items()):
        dt_ct = to_ct(dt)
        dt_month_start = to_utc(ct_datetime(dt_ct.year, dt_ct.month))
        if dt_month_start != month_start:
            if len(gcfs) > 0:
                yield month_start, gcfs
            month_start, gcfs = dt_month_start, {}
        gcfs[dt] = vals

    if len(gcfs) > 0:
        yield month_start, gcfs


def import_gcfs(sess, log, set_progress, scripting_key):
    caches = {}
    log("Starting to check GCFs.")
    contract_name = "gcfs"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess,
            contract_name,
            "",
            {"enabled": True},
            to_utc(ct_datetime(1996, 4, 1)),
            None,
            {"gcfs": {}},
        )
        sess.commit()
    contract_props = contract.make_properties()
    if contract_props.get("enabled", True):
        complete_date, gcf_data = _find_complete_date(caches, sess, contract)
        log(f"Found complete up to {complete_date}")

        sess.rollback()  # Avoid long-running transaction
        r = download_file(log, scripting_key, "GSPGROUPCORRECTIONFACTORFILE")
        parser = csv.reader(
            (x.decode() for x in r.iter_lines()), delimiter=",", quotechar='"'
        )

        next(parser, None)
        for values in parser:
            if len(values) == 0:
                continue

            set_progress(values[0])

            if len(values) > 5:
                _process_line(
                    caches, sess, contract, log, complete_date, gcf_data, values
                )

        for month_start, gcfs in _gcf_months(gcf_data):
            rs = sess.scalars(
                select(RateScript).where(
                    RateScript.contract == contract,
                    RateScript.start_date == month_start,
                )
            ).one_or_none()
            if rs is None:
                rs = contract.insert_rate_script(sess, month_start, {})

            rs.script = dumps({"gcfs": {key_format(d): v for d, v in gcfs.items()}})
            sess.commit()
    else:
        log(
            "The importer is disabled. Set 'enabled' to 'true' in the "
            "properties to enable it."
        )
    log("Finished checking GCFs.")


def _process_line(caches, sess, contract, log_func, complete_date, gcf_data, values):
    hh_date_str = values[0]
    run = values[1]
    settlement_period = int(values[2])
    gsp_group_code = values[3]
    gcf_type = values[4]
    gcf_str = values[5]

    if "-" in hh_date_str:
        fmt = "%Y-%m-%d"
    else:
        fmt = "%d/%m/%Y"
    hh_date_ct = to_ct(Datetime.strptime(hh_date_str, fmt))
    hh_date_ct += relativedelta(minutes=30 * (settlement_period - 1))
    hh_date = to_utc(hh_date_ct)

    if complete_date is not None and hh_date <= complete_date:
        return
    if gsp_group_code is None:
        return

    try:
        gcf = Decimal(gcf_str)
    except InvalidOperation as e:
        raise BadRequest(
            f"Problem parsing 'gcf' field '{gcf_str}' in the row {values}. {e}"
        )

    try:
        existing = gcf_data[hh_date]
    except KeyError:
        existing = gcf_data[hh_date] = {}

    try:
        group = existing[gsp_group_code]
    except KeyError:
        group = existing[gsp_group_code] = {}

    try:
        group_run = group[run]
    except KeyError:
        group_run = group[run] = {}

    if gcf_type in ("legacy_gcf", "mhhs_import_gcf"):
        group_run["import"] = gcf
    elif gcf_type in ("legacy_gcf", "mhhs_export_gcf"):
        group_run["export"] = gcf
    else:
        raise BadRequest(f"The gcf_type {gcf_type} is not recognised.")
