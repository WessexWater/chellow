from datetime import datetime as Datetime, timedelta as Timedelta
from decimal import Decimal
from io import BytesIO

from dateutil.relativedelta import relativedelta

from pypdf import PdfReader

from sqlalchemy import null, or_, select

from werkzeug.exceptions import BadRequest

import chellow.e.duos
from chellow.models import Contract, RateScript
from chellow.national_grid import api_get
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


def hh(ds, rate_period="monthly", est_kw=None):
    for hh in ds.hh_data:
        if hh["ct-is-month-end"]:
            _process_triad_hh(ds, rate_period, est_kw, hh)


def _find_triad_rate(ds, date, polarity, gsp_group_code):
    trt = ds.non_core_rate("triad_rates", date)["triad_gbp_per_gsp_kw"][polarity][
        gsp_group_code
    ]
    if isinstance(trt, Decimal):
        rt = trt
    elif polarity == "import":
        rt = trt["HHTariff(Floored)_£/kW"]
    elif polarity == "export":
        rt = trt["EET(Floored)_£/kW"]
    return float(rt)


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

            fdt = dt
            while fdt < financial_year_start:
                fdt += relativedelta(years=1)

            while fdt.weekday() != dt.weekday():
                fdt += relativedelta(days=1)

            for d in ds.get_data_sources(fdt, fdt, financial_year_start):
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
    rate = _find_triad_rate(ds, month_start, polarity, gsp_group_code)

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

            rate = _find_triad_rate(ds, rs.start_date, polarity, gsp_group_code)

            tot_rate += (finish_month - start_month + 1) * rate

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


GSP_LOOKUP = {
    1: "_P",
    2: "_N",
    3: "_F",
    4: "_G",
    5: "_M",
    6: "_D",
    7: "_B",
    8: "_E",
    9: "_A",
    10: "_K",
    11: "_J",
    12: "_C",
    13: "_H",
    14: "_L",
}


def _parse_varying_date(date_str):
    if "-" in date_str:
        pattern = "%Y-%m-%d"
    elif "/" in date_str:
        pattern = "%d/%m/%Y"
    else:
        raise BadRequest(f"The date {date_str} is not recognized.")
    return Datetime.strptime(date_str, pattern)


def national_grid_import(sess, log, set_progress, s):
    log("Starting to check for new TNUoS TRIAD Tariffs")

    contract = Contract.find_non_core_by_name(sess, "triad_rates")
    if contract is None:
        contract = Contract.insert_non_core(
            sess, "triad_rates", "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )
    for polarity, datafile in (
        ("import", "6abe8416-149c-4c78-b65b-059eea19957a"),
        ("export", "af4501a0-6b96-4088-926c-7c7b0c499b08"),
    ):
        params = {"sql": f"""SELECT * FROM "{datafile}" """}
        res_j = api_get(s, "datastore_search_sql", params=params)
        for record in res_j["result"]["records"]:
            fy_year = int(record["Year_FY"]) - 1
            fy_start = to_utc(ct_datetime(fy_year, 4, 1))
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

            rs_script = rs.make_script()
            try:
                tr = rs_script["triad_gbp_per_gsp_kw"]
            except KeyError:
                tr = rs_script["triad_gbp_per_gsp_kw"] = {}

            try:
                rates = tr[polarity]
            except KeyError:
                rates = tr[polarity] = {}

            record_key = GSP_LOOKUP[record["Zone_No"]]
            record_published_date = _parse_varying_date(record["Published_Date"])

            rate = rates.get(record_key)
            if (
                rate is None
                or _parse_varying_date(rate["Published_Date"]) < record_published_date
            ):
                rates[record_key] = record
                rs.update(rs_script)
                sess.commit()

    log("Finished TNUoS TRIAD Tariffs")
    sess.commit()


def _find_triad_dates(file_name, file_like):
    dates = []
    rate_script = {"a_file_name": file_name, "triad_dates": dates}

    reader = PdfReader(file_like)
    in_table = False
    for page in reader.pages:
        for line in page.extract_text().splitlines():
            if in_table:
                date_str, period_str, _ = line.split()
                date = Datetime.strptime(date_str, "%d/%m/%Y")
                delta = Timedelta(minutes=30) * (int(period_str) - 1)
                dates.append(to_utc(to_ct(date + delta)))
                if len(dates) == 3:
                    in_table = False
            else:
                if "Demand (MW)" in line:
                    in_table = True

    return rate_script


def rate_server_import(sess, log, set_progress, s, paths):
    log("Starting to check for new TNUoS triad date PDFs")

    year_entries = {}
    for path, url in paths:
        if len(path) == 4:
            year, utility, rate_type, file_name = path
            if utility == "electricity" and rate_type == "tnuos":
                try:
                    fl_entries = year_entries[year]
                except KeyError:
                    fl_entries = year_entries[year] = {}

                fl_entries[file_name] = url

    for year, year_pdfs in sorted(year_entries.items()):
        year_start = to_utc(ct_datetime(year, 4, 1))
        contract = Contract.get_non_core_by_name(sess, "triad_dates")
        if year_start < contract.start_rate_script.start_date:
            continue
        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == year_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, year_start, {})

        if len(year_pdfs) > 0:
            file_name, url = sorted(year_pdfs.items())[-1]

            rs_script = rs.make_script()
            if rs_script.get("a_file_name") != file_name:
                rs.update(_find_triad_dates(file_name, BytesIO(download(s, url))))
                log(f"Updated triad dates rate script for {hh_format(year_start)}")

    log("Finished TNUoS triad dates PDFs")
    sess.commit()
