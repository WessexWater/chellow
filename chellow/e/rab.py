from datetime import datetime as Datetime
from decimal import Decimal


from sqlalchemy import select

from chellow.e.lcc import api_records
from chellow.models import Contract, RateScript
from chellow.utils import ct_datetime, to_ct, to_utc


def hh(data_source):
    try:
        rab_cache = data_source.caches["rab"]
    except KeyError:
        rab_cache = data_source.caches["rab"] = {}

    for h in data_source.hh_data:
        try:
            h["rab"] = rab_cache[h["start-date"]]
        except KeyError:
            h_start = h["start-date"]
            rate_str = data_source.non_core_rate("rab_forecast_ilr_tra", h_start)[
                "record"
            ]["Interim_Levy_Rate_GBP_MWh"]
            if rate_str == "":
                base_rate_dec = Decimal("0")
            else:
                base_rate_dec = Decimal(rate_str) / Decimal(1000)

            base_rate = float(base_rate_dec)

            h["rab"] = rab_cache[h_start] = {
                "interim": base_rate,
            }


def lcc_import(sess, log, set_progress, s):
    import_forecast_ilr_tra(sess, log, set_progress, s)


def _parse_date(date_str):
    return to_utc(to_ct(Datetime.strptime(date_str[:10], "%Y-%m-%d")))


def import_forecast_ilr_tra(sess, log, set_progress, s):
    log("Starting to check for new LCC RAB Forecast ILR TRA")

    contract_name = "rab_forecast_ilr_tra"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, contract_name, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )

    for record in api_records(log, s, "1231fbb3-93ee-4a33-87a9-f15bb377346d"):
        period_start_str = record["Month"]
        if len(period_start_str) == 0:
            continue
        period_start = _parse_date(period_start_str)

        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == period_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, period_start, {})

        rs_script = rs.make_script()
        rs_script["record"] = record
        rs.update(rs_script)
        sess.commit()
    log("Finished LCC RAB Forecast ILR TRA")
