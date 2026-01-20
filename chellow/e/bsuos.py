from sqlalchemy import select

from chellow.e.neso import csv_latest, parse_date
from chellow.models import Contract, RateScript
from chellow.utils import ct_datetime, to_utc

MAXIMA = [
    {
        "maximum": 15,
        "start": to_utc(ct_datetime(2020, 6, 25)),
        "finish": to_utc(ct_datetime(2020, 8, 31, 23, 30)),
        "reference": "CMP345",
    },
    {
        "maximum": 20,
        "start": to_utc(ct_datetime(2022, 1, 17)),
        "finish": to_utc(ct_datetime(2022, 3, 31, 23, 30)),
        "reference": "CMP381",
    },
    {
        "maximum": 40,
        "start": to_utc(ct_datetime(2022, 10, 6)),
        "finish": to_utc(ct_datetime(2023, 3, 31, 23, 30)),
        "reference": "CMP395",
    },
]


def hh(data_source, run="RF"):
    try:
        bsuos_cache = data_source.caches["bsuos"][run]
    except KeyError:
        try:
            top_cache = data_source.caches["bsuos"]
        except KeyError:
            top_cache = data_source.caches["bsuos"] = {}

        try:
            bsuos_cache = top_cache[run]
        except KeyError:
            bsuos_cache = top_cache[run] = {}

    for h in data_source.hh_data:
        try:
            h["bsuos-rate"] = bsuos_rate = bsuos_cache[h["start-date"]]
        except KeyError:
            h_start = h["start-date"]

            rates = data_source.non_core_rate("bsuos", h_start)

            if h_start >= to_utc(ct_datetime(2023, 4, 1)):
                bsuos_price = float(rates["record"]["Fixed Tariff £/MWh"])
            else:
                bsuos_rates = rates["rates_gbp_per_mwh"]

                maxi = None
                for max_dict in MAXIMA:
                    if max_dict["start"] <= h_start <= max_dict["finish"]:
                        maxi = max_dict["maximum"]
                        break

                try:
                    bsuos_price_dict = bsuos_rates[key_format(h_start)]
                    bsuos_price = _find_price(run, bsuos_price_dict, maxi)
                except KeyError:
                    ds = bsuos_rates.values()
                    bsuos_price = sum(_find_price(run, d, maxi) for d in ds) / len(ds)

            h["bsuos-rate"] = bsuos_rate = bsuos_cache[h_start] = bsuos_price / 1000

        h["bsuos-kwh"] = h["nbp-kwh"]
        h["bsuos-gbp"] = h["nbp-kwh"] * bsuos_rate


def _find_price(run, prices, maxi):
    try:
        price = prices[run]
    except KeyError:
        try:
            price = prices["RF"]
        except KeyError:
            try:
                price = prices["SF"]
            except KeyError:
                price = prices["II"]

    float_price = float(price)
    return float_price if maxi is None else min(float_price, maxi)


def key_format(dt):
    return dt.strftime("%d %H:%M")


CONTRACT_NAME = "bsuos"


def neso_import(sess, log, set_progress):
    log("Starting to check for new BSUoS rates")

    CONTRACT_NAME = "bsuos"
    contract = Contract.find_non_core_by_name(sess, CONTRACT_NAME)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, CONTRACT_NAME, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )
    state = contract.make_state()
    last_import_date = state.get("last_import_date")

    for record in csv_latest("bsuos-fixed-tariffs", last_import_date):
        #   "Publication": "Final",
        #   "Fixed Tariff Title": "Fixed Tariff 1",
        #   "Published Date": "2023-01-31",
        #   "Fixed Tariff Start Date": "2023-04-01",
        #   "Fixed Tariff End Date": "2023-09-30",
        #   "Fixed Tariff £/MWh": "13.41",

        tariff_start = parse_date(record["Fixed Tariff Start Date"])
        rs = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == tariff_start,
            )
        ).scalar_one_or_none()
        if rs is None:
            rs = contract.insert_rate_script(sess, tariff_start, {})

        rs_script = rs.make_script()
        try:
            rs_record = rs_script["record"]
        except KeyError:
            rs_record = rs_script["record"] = {}

        record_published_date = parse_date(record["Published Date"])

        if (
            "Published Date" not in rs_record
            or parse_date(rs_record["Published Date"]) < record_published_date
        ):
            rs_script["record"] = record
            rs.update(rs_script)
            sess.commit()

    log("Finished Checking for BSUoS Tariffs")
    sess.commit()
