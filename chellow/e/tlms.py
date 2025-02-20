import csv
from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta

from sqlalchemy import or_, select
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

from zish import dumps, loads

from chellow.models import Contract, RateScript
from chellow.utils import HH, ct_datetime, hh_format, hh_range, to_ct, to_utc


RUNS = ["DF", "RF", "R3", "R2", "R1", "SF", "II"]


def key_format(dt):
    return dt.strftime("%d %H:%M")


def hh(data_source, run="DF"):
    gsp_group_code = data_source.gsp_group_code
    use_runs = RUNS[RUNS.index(run) :]

    try:
        cache = data_source.caches["tlms"]
    except KeyError:
        cache = data_source.caches["tlms"] = {}

    for h in data_source.hh_data:
        try:
            h["tlm"] = tlm = cache[h["start-date"]][gsp_group_code][run]
        except KeyError:
            h_start = h["start-date"]
            vals = data_source.non_core_rate("tlms", h_start, exact=True)
            if vals is None:
                vals = data_source.non_core_rate("tlms", h["hist-start"])

            rates = vals["tlms"]

            key = key_format(h_start)
            try:
                rate = rates[key]
            except KeyError:
                rate = sorted(rates.items())[-1][1]

            try:
                gsp_rate = rate[gsp_group_code]
            except KeyError:
                gsp_rate = sorted(rate.items())[-1][1]

            tlm = None
            for use_run in use_runs:
                try:
                    h["tlm"] = tlm = float(gsp_rate[use_run]["off_taking"])
                    break
                except KeyError:
                    pass

            if tlm is None:
                h["tlm"] = tlm = float(sorted(gsp_rate.items())[-1][1]["off_taking"])

            try:
                rates_cache = cache[h["start-date"]]
            except KeyError:
                rates_cache = cache[h["start-date"]] = {}

            try:
                gsp_cache = rates_cache[gsp_group_code]
            except KeyError:
                gsp_cache = rates_cache[gsp_group_code] = {}

            gsp_cache[run] = tlm

        h["nbp-kwh"] = h["gsp-kwh"] * tlm


def _find_complete_date(caches, sess, contract, cache):
    for rs in sess.scalars(
        select(RateScript)
        .where(RateScript.contract == contract, RateScript.finish_date != null())
        .order_by(RateScript.start_date.desc())
    ):
        rates = rs.make_script()
        rates["id"] = rs.id
        cache["rate_scripts"].append(rates)
        timestamps = cache["timestamps"]
        tlms = rates["tlms"]
        complete = True
        for dt in hh_range(caches, rs.start_date, rs.finish_date):
            timestamps[dt] = rates
            key = key_format(dt)
            if key in tlms:
                gps = tlms[key]
                for group in GSP_GROUP_LOOKUP.values():
                    if not (group in gps and "DF" in gps[group]):
                        complete = False
            else:
                complete = False

        if complete:
            return rs.finish_date


def elexon_import(sess, log, set_progress, s, scripting_key):
    cache = {"rate_scripts": [], "timestamps": {}}
    caches = {}
    log("Starting to check TLMs.")
    contract_name = "tlms"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess,
            contract_name,
            "",
            {"enabled": True},
            to_utc(ct_datetime(1997, 1, 1)),
            to_utc(ct_datetime(1997, 1, 31, 23, 30)),
            {"tlms": {}},
        )
        sess.commit()
    contract_props = contract.make_properties()
    if contract_props.get("enabled", False):

        params = {"key": scripting_key}
        url_str = "https://downloads.elexonportal.co.uk/file/download/TLM_FILE"
        complete_date = _find_complete_date(caches, sess, contract, cache)
        log(f"Found complete up to {complete_date}")

        sess.rollback()  # Avoid long-running transaction
        r = s.get(url_str, params=params, timeout=120)
        parser = csv.reader(
            (x.decode() for x in r.iter_lines()), delimiter=",", quotechar='"'
        )
        log(f"Opened {url_str}?key={scripting_key}.")

        next(parser, None)
        for values in parser:
            if len(values) == 0:
                continue

            set_progress(values[0])

            if values[3] == "":
                for zone in GSP_GROUP_LOOKUP.keys():
                    values[3] = zone
                    _process_line(
                        cache, sess, contract, log, values, complete_date, caches
                    )
            else:
                _process_line(cache, sess, contract, log, values, complete_date, caches)

        for rscript in cache["rate_scripts"]:
            rs = sess.scalars(
                select(RateScript).where(RateScript.id == rscript["id"])
            ).one()
            rs.script = dumps({"tlms": rscript["tlms"]})
            sess.commit()

    else:
        log(
            "The importer is disabled. Set 'enabled' to 'true' in the "
            "properties to enable it."
        )
    log("Finished checking TLMs.")


GSP_GROUP_LOOKUP = {
    "1": "_A",
    "2": "_B",
    "3": "_C",
    "4": "_D",
    "5": "_E",
    "6": "_F",
    "7": "_G",
    "8": "_H",
    "9": "_J",
    "10": "_K",
    "11": "_L",
    "12": "_M",
    "13": "_N",
    "14": "_P",
}


def _process_line(cache, sess, contract, log_func, values, complete_date, caches):
    hh_date_ct = to_ct(Datetime.strptime(values[0], "%d/%m/%Y"))
    hh_date = to_utc(hh_date_ct)
    hh_date += relativedelta(minutes=30 * (int(values[2]) - 1))
    if complete_date is not None and hh_date <= complete_date:
        return
    run = values[1]
    gsp_group_code = GSP_GROUP_LOOKUP[values[3]]
    off_taking_str = values[4]

    try:
        off_taking = Decimal(off_taking_str)
    except InvalidOperation as e:
        raise BadRequest(
            f"Problem parsing 'off-taking' field '{off_taking_str}' in the row "
            f"{values}. {e}"
        )

    delivering = Decimal(values[5])

    key = key_format(hh_date)
    try:
        cache["timestamps"][hh_date]["tlms"][key][gsp_group_code][run]
    except KeyError:
        try:
            rate = cache["timestamps"][hh_date]
        except KeyError:

            rs = (
                sess.query(RateScript)
                .filter(
                    RateScript.contract == contract,
                    RateScript.start_date <= hh_date,
                    or_(
                        RateScript.finish_date == null(),
                        RateScript.finish_date >= hh_date,
                    ),
                )
                .first()
            )
            assert rs is None
            while rs is None:
                log_func(f"There's no rate script at {hh_format(hh_date)}.")
                latest_rs = (
                    sess.query(RateScript)
                    .filter(RateScript.contract == contract)
                    .order_by(RateScript.start_date.desc())
                    .first()
                )
                contract.update_rate_script(
                    sess,
                    latest_rs,
                    latest_rs.start_date,
                    latest_rs.start_date + relativedelta(months=2) - HH,
                    loads(latest_rs.script),
                )
                new_rs_start = latest_rs.start_date + relativedelta(months=1)
                new_rs = contract.insert_rate_script(sess, new_rs_start, {})
                rt = {"tlms": {}, "id": new_rs.id}
                cache["rate_scripts"].append(rt)
                for h in hh_range(caches, new_rs.start_date, new_rs.finish_date):
                    cache["timestamps"][h] = rt
                sess.commit()
                log_func(f"Added a rate script starting at {hh_format(new_rs_start)}.")

                rs = (
                    sess.query(RateScript)
                    .filter(
                        RateScript.contract == contract,
                        RateScript.start_date <= hh_date,
                        or_(
                            RateScript.finish_date == null(),
                            RateScript.finish_date >= hh_date,
                        ),
                    )
                    .first()
                )

            rate = cache["timestamps"][hh_date]

        try:
            existing = rate["tlms"][key]
        except KeyError:
            existing = rate["tlms"][key] = {}

        try:
            group = existing[gsp_group_code]
        except KeyError:
            group = existing[gsp_group_code] = {}

        group[run] = {"off_taking": off_taking, "delivering": delivering}

        log_func(
            f"Found rate at {hh_format(hh_date)} for GSP Group {gsp_group_code} "
            f"and run {run}."
        )
