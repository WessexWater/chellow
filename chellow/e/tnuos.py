from decimal import Decimal, InvalidOperation
from io import BytesIO

from dateutil.relativedelta import relativedelta

from openpyxl import load_workbook

from sqlalchemy import null, or_, select

from werkzeug.exceptions import BadRequest

import chellow.e.computer
import chellow.e.duos
from chellow.models import Contract, RateScript
from chellow.rate_server import download
from chellow.utils import (
    c_months_u,
    ct_datetime,
    hh_after,
    hh_format,
    hh_min,
    to_ct,
    to_utc,
)

BANDED_START = to_utc(ct_datetime(2023, 4, 1))


def hh(ds, rate_period="monthly", est_kw=None):

    for hh in ds.hh_data:
        if hh["start-date"] >= BANDED_START:
            if hh["ct-decimal-hour"] == 12:
                _process_banded_hh(ds, hh)
        else:
            if hh["ct-is-month-end"]:
                _process_triad_hh(ds, rate_period, est_kw, hh)


def _process_banded_hh(ds, hh):
    rates = ds.non_core_rate("tnuos", hh["start-date"])
    lookup = rates["lookup"]
    band = lookup[hh["duos-description"]]
    hh["tnuos-band"] = band
    rate = float(rates["bands"][band])
    if band == "Unmetered":
        hh["tnuos-gbp"] = rate / 100 * ds.sc / 365
    else:
        hh["tnuos-gbp"] = rate


def _process_triad_hh(ds, rate_period, est_kw, hh):
    month_start, month_finish = next(
        c_months_u(start_year=hh["ct-year"], start_month=hh["ct-month"])
    )

    month_start_ct = to_ct(month_start)
    if month_start_ct.month > 3:
        year = month_start_ct.year
    else:
        year = month_start_ct.year - 1
    financial_year_start = to_utc(ct_datetime(year, 4, 1))
    last_financial_year_start = to_utc(ct_datetime(year - 1, 4, 1))
    financial_year_finish = to_utc(ct_datetime(year + 1, 3, 31, 23, 30))

    est_triad_kws = []
    earliest_triad = None
    for dt in ds.non_core_rate("triad_dates", last_financial_year_start)["triad_dates"]:
        triad_hh = None
        earliest_triad = hh_min(earliest_triad, dt)
        try:
            d = next(ds.get_data_sources(dt, dt, financial_year_start))
            chellow.e.duos.duos_vb(d)
            triad_hh = d.hh_data[0]

            while dt < financial_year_start:
                dt += relativedelta(years=1)

            for d in ds.get_data_sources(dt, dt, financial_year_start):
                chellow.e.duos.duos_vb(d)
                datum = d.hh_data[0]
                triad_hh["laf"] = datum["laf"]
                triad_hh["gsp-kw"] = datum["laf"] * triad_hh["msp-kw"]
        except StopIteration:
            triad_hh = {
                "hist-start": dt,
                "msp-kw": 0,
                "start-date": dt,
                "status": "before start of MPAN",
                "laf": 1,
                "gsp-kw": 0,
            }
        est_triad_kws.append(triad_hh)

    if ds.site is None:
        era = ds.supply.find_era_at(ds.sess, earliest_triad)
        if (
            era is None
            or era.get_channel(ds.sess, ds.is_import, "ACTIVE") is None
            and est_kw is None
        ):
            est_kw = 0.85 * max(datum["msp-kwh"] for datum in ds.hh_data) * 2
        if est_kw is not None:
            for est_datum in est_triad_kws:
                est_datum["msp-kw"] = est_kw
                est_datum["gsp-kw"] = est_datum["msp-kw"] * est_datum["laf"]

    gsp_kw = 0
    for i, triad_hh in enumerate(est_triad_kws):
        triad_prefix = "triad-estimate-" + str(i + 1)
        hh[triad_prefix + "-date"] = triad_hh["hist-start"]
        hh[triad_prefix + "-msp-kw"] = triad_hh["msp-kw"]
        hh[triad_prefix + "-status"] = triad_hh["status"]
        hh[triad_prefix + "-laf"] = triad_hh["laf"]
        hh[triad_prefix + "-gsp-kw"] = triad_hh["gsp-kw"]
        gsp_kw += triad_hh["gsp-kw"]

    hh["triad-estimate-gsp-kw"] = gsp_kw / 3
    polarity = "import" if ds.llfc.is_import else "export"
    gsp_group_code = ds.gsp_group_code
    rate = float(
        ds.non_core_rate("tnuos", month_start)["triad_gbp_per_gsp_kw"][polarity][
            gsp_group_code
        ]
    )

    hh["triad-estimate-rate"] = rate

    est_triad_gbp = hh["triad-estimate-rate"] * hh["triad-estimate-gsp-kw"]

    if rate_period == "monthly":
        total_intervals = 12

        est_intervals = 1
        hh["triad-estimate-months"] = est_intervals
    else:
        dt = financial_year_start
        total_intervals = 0
        while dt <= financial_year_finish:
            total_intervals += 1
            dt += relativedelta(days=1)

        est_intervals = 0
        for d in ds.get_data_sources(month_start, month_finish):
            for h in d.hh_data:
                if h["ct-decimal-hour"] == 0:
                    est_intervals += 1

        hh["triad-estimate-days"] = est_intervals

    hh["triad-estimate-gbp"] = est_triad_gbp / total_intervals * est_intervals

    if hh["ct-month"] == 3:
        triad_kws = []
        for t_date in ds.non_core_rate("triad_dates", month_start)["triad_dates"]:
            try:
                d = next(ds.get_data_sources(t_date, t_date))
                if (
                    ds.supplier_contract is None
                    or d.supplier_contract == ds.supplier_contract
                ):
                    chellow.e.duos.duos_vb(d)
                    thh = d.hh_data[0]
                else:
                    thh = {
                        "hist-start": t_date,
                        "msp-kw": 0,
                        "start-date": t_date,
                        "status": "before contract",
                        "laf": "before contract",
                        "gsp-kw": 0,
                    }
            except StopIteration:
                thh = {
                    "hist-start": t_date,
                    "msp-kw": 0,
                    "start-date": t_date,
                    "status": "before start of supply",
                    "laf": "before start of supply",
                    "gsp-kw": 0,
                }

            while t_date < financial_year_start:
                t_date += relativedelta(years=1)

            try:
                d = next(ds.get_data_sources(t_date, t_date))
                if (
                    ds.supplier_contract is None
                    or d.supplier_contract == ds.supplier_contract
                ):
                    chellow.e.duos.duos_vb(d)
                    thh["laf"] = d.hh_data[0]["laf"]
                    thh["gsp-kw"] = thh["laf"] * thh["msp-kw"]
            except StopIteration:
                pass

            triad_kws.append(thh)
        gsp_kw = 0

        for i, triad_hh in enumerate(triad_kws):
            pref = "triad-actual-" + str(i + 1)
            hh[pref + "-date"] = triad_hh["start-date"]
            hh[pref + "-msp-kw"] = triad_hh["msp-kw"]
            hh[pref + "-status"] = triad_hh["status"]
            hh[pref + "-laf"] = triad_hh["laf"]
            hh[pref + "-gsp-kw"] = triad_hh["gsp-kw"]
            gsp_kw += triad_hh["gsp-kw"]

        hh["triad-actual-gsp-kw"] = gsp_kw / 3
        polarity = "import" if ds.llfc.is_import else "export"
        gsp_group_code = ds.gsp_group_code
        tot_rate = 0
        for rs in ds.sess.execute(
            select(RateScript)
            .join(Contract, RateScript.contract_id == Contract.id)
            .where(
                Contract.name == "tnuos",
                RateScript.start_date <= financial_year_finish,
                or_(
                    RateScript.finish_date == null(),
                    RateScript.finish_date >= financial_year_start,
                ),
            )
        ).scalars():
            start_month = to_ct(rs.start_date).month
            if start_month < 4:
                start_month += 12

            if rs.finish_date is None:
                finish_month = 3
            else:
                finish_month = to_ct(rs.finish_date).month

            if finish_month < 4:
                finish_month += 12

            rt = ds.non_core_rate("tnuos", rs.start_date)["triad_gbp_per_gsp_kw"][
                polarity
            ][gsp_group_code]
            tot_rate += (finish_month - start_month + 1) * float(rt)

        rate = tot_rate / 12
        hh["triad-actual-rate"] = rate

        hh["triad-actual-gbp"] = hh["triad-actual-rate"] * hh["triad-actual-gsp-kw"]

        era = ds.supply.find_era_at(ds.sess, month_finish)
        est_intervals = 0

        interval = (
            relativedelta(months=1)
            if rate_period == "monthly"
            else relativedelta(days=1)
        )

        dt = month_finish
        while era is not None and dt > financial_year_start:
            est_intervals += 1
            dt -= interval
            if hh_after(dt, era.finish_date):
                era = ds.supply.find_era_at(ds.sess, dt)

        if rate_period == "monthly":
            hh["triad-all-estimates-months"] = est_intervals
        else:
            hh["triad-all-estimates-days"] = est_intervals
        hh["triad-all-estimates-gbp"] = (
            est_triad_gbp / total_intervals * est_intervals * -1
        )


def get_cell(sheet, col, row):
    try:
        coordinates = f"{col}{row}"
        return sheet[coordinates]
    except IndexError:
        raise BadRequest(f"Can't find the cell {coordinates} on sheet {sheet}.")


def get_int(sheet, col, row):
    return int(get_cell(sheet, col, row).value)


def get_dec(sheet, col, row):
    cell = get_cell(sheet, col, row)
    try:
        return Decimal(str(cell.value))
    except InvalidOperation as e:
        raise BadRequest(f"Problem parsing the number at {cell.coordinate}. {e}")


def get_str(sheet, col, row):
    return get_cell(sheet, col, row).value.strip()


def get_value(row, idx):
    val = row[idx].value
    if isinstance(val, str):
        return val.strip()
    else:
        return val


def find_bands(file_like):
    book = load_workbook(file_like, data_only=True)

    tabs = {sheet.title.strip(): sheet for sheet in book.worksheets}

    tab_name = "T10"
    try:
        sheet = tabs[tab_name]
    except KeyError:
        raise BadRequest(f"Can't find the tab named '{tab_name}'")

    bands = {}

    in_bands = False
    for row in range(1, len(sheet["B"]) + 1):
        val = get_cell(sheet, "B", row).value
        val_0 = None if val is None else " ".join(val.split())
        if in_bands:
            if val_0 is None or len(val_0) == 0 or val_0 == "Demand Residual (£m)":
                in_bands = False
            elif val_0 != "Unmetered demand":
                bands[val_0] = get_dec(sheet, "E", row)

        elif val_0 == "Band":
            in_bands = True

    return bands


def rate_server_import(sess, s, paths, logger):
    logger("Starting to check for new TNUoS spreadsheets")
    year_entries = {}
    for path, url in paths:
        if len(path) == 4:

            year_str, utility, rate_type, file_name = path
            year = int(year_str)

            if utility == "electricity" and rate_type == "tnuos":

                try:
                    fl_entries = year_entries[year]
                except KeyError:
                    fl_entries = year_entries[year] = {}

                fl_entries[file_name] = url

    contract = Contract.get_non_core_by_name(sess, "tnuos")
    for year, fl_entries in sorted(year_entries.items()):
        fy_start = to_utc(ct_datetime(year, 4, 1))
        if fy_start < contract.start_rate_script.start_date:
            continue

        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == fy_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, fy_start, {})

        file_name, url = sorted(fl_entries.items())[-1]

        rs_script = rs.make_script()
        if rs_script.get("a_file_name") != file_name:
            try:
                fl = BytesIO(download(s, url))
                try:
                    bands = find_bands(fl)
                except BadRequest as e:
                    raise BadRequest(
                        f"Problem with file '{file_name}': {e.description}"
                    )
                rs_script["bands"] = bands
                rs_script["a_file_name"] = file_name
                rs.update(rs_script)
                logger(f"Updated TNUoS rate script for " f"{hh_format(fy_start)}")
            except BadRequest as e:
                raise BadRequest(f"Problem with year {year}: {e.description}")

    logger("Finished TNUoS spreadsheets")
    sess.commit()
