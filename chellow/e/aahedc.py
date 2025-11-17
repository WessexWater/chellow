from decimal import Decimal

from sqlalchemy import select

from chellow.models import Contract, RateScript
from chellow.national_grid import api_get
from chellow.utils import ct_datetime, to_utc


def hh(supply_source):
    try:
        aahedc_cache = supply_source.caches["aahedc"]
    except KeyError:
        aahedc_cache = supply_source.caches["aahedc"] = {}

    for hh in supply_source.hh_data:
        hh["aahedc-kwh"] = hh["gsp-kwh"]
        try:
            rate = aahedc_cache[hh["start-date"]]
        except KeyError:
            hh_start = hh["start-date"]
            rates = supply_source.non_core_rate("aahedc", hh_start)
            rate = aahedc_cache[hh_start] = float(rates["aahedc_gbp_per_gsp_kwh"])

        hh["aahedc-rate"] = rate
        hh["aahedc-gbp"] = hh["gsp-kwh"] * rate


def national_grid_import(sess, log, set_progress, s):
    log("Starting to check for new AAHEDC rates")

    contract_name = "aahedc"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, contract_name, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )

    params = {"sql": """SELECT * FROM "ffd29cc8-3c55-4e83-aa0e-73212d4fedba" """}
    res_j = api_get(s, "datastore_search_sql", params=params)
    for record in res_j["result"]["records"]:
        # {
        #   "_full_text": "'-07':4 '-15':5 '0.012247':7 '0.028 '2026':2 'final':1",
        #   "Published Date": "2025-07-15",
        #   "AAHEDC tariff excluding the Shetland Assistance Amount in p/kwh":
        #   "0.028737",
        #   "Shetland Tariff in p/kwh": "0.012247",
        #   "Year FY": 2026,
        #   "Publication Type": "Final",
        #   "_id": 7,
        #   "Total Scheme Tariff in p/kwh": "0.040984"
        # }

        fy_year = int(record["Year FY"]) - 1
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
            rs_record = rs_script["record"]
        except KeyError:
            rs_record = rs_script["record"] = {}

        record_published_date = record["Published Date"]

        if (
            "Published Date" not in rs_record
            or rs_record["Published Date"] < record_published_date
        ):
            rs_script["record"] = record
            rs_script["aahedc_gbp_per_gsp_kwh"] = Decimal(
                record["Total Scheme Tariff in p/kwh"]
            ) / Decimal("100")
            rs.update(rs_script)
            sess.commit()

    log("Finished Checking for AAHEDC Tariffs")
    sess.commit()
