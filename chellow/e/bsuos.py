import atexit
import collections
import csv
import json
import threading
import traceback
from datetime import datetime as Datetime
from decimal import Decimal
from io import BytesIO

from dateutil.relativedelta import relativedelta


import requests

from sqlalchemy import or_, select
from sqlalchemy.sql.expression import null

from zish import dumps, loads

from chellow.models import Contract, RateScript, Session
from chellow.national_grid import api_get
from chellow.rate_server import download
from chellow.utils import HH, ct_datetime, hh_format, to_ct, to_utc, utc_datetime_now

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
                try:
                    bprice = rates["rate_gbp_per_mwh"]
                except KeyError:
                    bprice = rates["forecast_rate_gbp_per_mwh"]
                bsuos_price = float(bprice)

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


bsuos_importer = None


def _save_cache(sess, cache):
    for yr, yr_cache in cache.items():
        for month, (rs, rates, rts) in tuple(yr_cache.items()):
            rs.script = dumps(rates)
            sess.commit()
            del yr_cache[month]


BASE_URL = "https://data.nationalgrideso.com/backend/dataset/"
PATHS = (
    "d6a4bf54-c63f-4014-a716-49fd3878ca52/resource/"
    "0eda5e28-1dc6-48da-8663-c00e12f2a1e2/download/current_ii_bsuos_data-11.csv",
    "d6a4bf54-c63f-4014-a716-49fd3878ca52/resource/"
    "f0060fd0-1fc9-4288-a0b3-4af9b592b0cf/download/current_sf_bsuos_data.csv",
    "d6a4bf54-c63f-4014-a716-49fd3878ca52/resource/"
    "26b0f410-27d4-448a-9437-45277818b838/download/current_rf_bsuos_data.csv",
)


class BsuosImporter(threading.Thread):
    def __init__(self):
        super(BsuosImporter, self).__init__(name="BSUoS Importer")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=500)
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.PROXY_HOST_KEY = "proxy.host"
        self.PROXY_PORT_KEY = "proxy.port"

    def stop(self):
        self.stopped.set()
        self.going.set()
        self.join()

    def go(self):
        self.going.set()

    def is_locked(self):
        if self.lock.acquire(False):
            self.lock.release()
            return False
        else:
            return True

    def log(self, message):
        self.messages.appendleft(
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message
        )

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                self.global_alert = s = None
                with Session() as sess:
                    try:
                        self.log("Starting to check BSUoS rates.")
                        contract = Contract.get_non_core_by_name(sess, "bsuos")
                        props = contract.make_properties()
                        s = requests.Session()
                        s.verify = False
                        if props.get("enabled", False):
                            for path in PATHS:
                                _process_url(
                                    self.log, sess, f"{BASE_URL}{path}", contract, s
                                )
                        else:
                            self.log(
                                "The automatic importer is disabled. To enable it, "
                                "edit the contract properties to set 'enabled' to True."
                            )
                        self.log("Finished checking BSUoS rates.")
                    except BaseException:
                        self.log(f"Outer problem {traceback.format_exc()}")
                        self.global_alert = (
                            f"There's a problem with the "
                            f"<a href='/non_core_contracts/{contract.id}'>BSUoS "
                            f"automatic importer</a>."
                        )
                        sess.rollback()
                    finally:
                        self.lock.release()

            self.going.wait(60 * 60 * 24)
            self.going.clear()


def _process_url(logger, sess, url, contract, s):
    logger(f"Checking to see if there's any new data at {url}")
    sess.rollback()  # Avoid long-running transaction
    res = s.get(url)
    logger(f"Received {res.status_code} {res.reason}")
    cache = {}
    parsed_rows = []

    reader = csv.reader(res.text.splitlines())
    next(reader)  # Skip titles

    for row in reader:
        date_str = row[0].strip()
        len_date_str = len(date_str)
        if len_date_str == 0:
            continue
        elif len_date_str == 19:
            sep_char = date_str[13]
            date_format = f"%Y-%m-%dT%H{sep_char}%M:%S"
        elif len_date_str == 20:
            date_format = "%Y-%m-%d-T%H:%M:%S"
        else:
            date_format = "%d-%m-%y"

        date = Datetime.strptime(date_str, date_format)
        period_str = row[1]
        period = int(period_str)
        price_str = row[2]
        price = Decimal(price_str)
        run = row[5]
        parsed_rows.append((date, period, price, run))

    for date, period, price, run in parsed_rows:
        hh_date_ct = to_ct(date)
        hh_date_ct += relativedelta(minutes=30 * (period - 1))
        hh_date = to_utc(hh_date_ct)
        if hh_date >= to_utc(ct_datetime(2023, 4, 1)):
            continue

        try:
            rs, rates, rts = cache[hh_date.year][hh_date.month]
        except KeyError:
            _save_cache(sess, cache)

            try:
                yr_cache = cache[hh_date.year]
            except KeyError:
                yr_cache = cache[hh_date.year] = {}

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
            while rs is None:
                logger(f"There's no rate script at {hh_format(hh_date)}.")
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
                contract.insert_rate_script(sess, new_rs_start, {})
                sess.commit()
                logger(f"Added a rate script starting at {hh_format(new_rs_start)}.")

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

            rates = loads(rs.script)
            try:
                rts = rates["rates_gbp_per_mwh"]
            except KeyError:
                rts = rates["rates_gbp_per_mwh"] = {}
            yr_cache[hh_date.month] = rs, rates, rts

        key = key_format(hh_date)
        try:
            existing = rts[key]
        except KeyError:
            existing = rts[key] = {}

        if run not in existing:
            existing[run] = price
            logger(f"Added rate at {hh_format(hh_date)} for run {run}.")

    _save_cache(sess, cache)


def get_importer():
    return bsuos_importer


def startup():
    global bsuos_importer
    bsuos_importer = BsuosImporter()
    bsuos_importer.start()


@atexit.register
def shutdown():
    if bsuos_importer is not None:
        bsuos_importer.stop()


def find_rate(file_name, file_like, rate_index):
    rate_script = {"a_file_name": file_name}
    rates = []
    for rate_str in json.load(file_like)["rates"]:
        rates.append(Decimal(rate_str))

    rate_script["rate_gbp_per_mwh"] = rates[rate_index]
    return rate_script


def rate_server_import(sess, log, set_progress, s, paths):
    log("Starting to check for new BSUoS spreadsheets")

    year_entries = {}
    for path, url in paths:
        if len(path) == 4:
            year_str, utility, rate_type, file_name = path
            if utility == "electricity" and rate_type == "bsuos":
                year = int(year_str)
                try:
                    fl_entries = year_entries[year]
                except KeyError:
                    fl_entries = year_entries[year] = {}

                fl_entries[file_name] = url

    for year, year_pdfs in sorted(year_entries.items()):
        year_start = to_utc(ct_datetime(year, 4, 1))
        oct_start = to_utc(ct_datetime(year, 10, 1))
        contract = Contract.get_non_core_by_name(sess, "bsuos")
        if year_start < contract.start_rate_script.start_date:
            continue
        rs_1 = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == year_start,
            )
        ).scalar_one_or_none()
        if rs_1 is None:
            rs_1 = contract.insert_rate_script(sess, year_start, {})

        rs_2 = sess.execute(
            select(RateScript).where(
                RateScript.contract == contract,
                RateScript.start_date == oct_start,
            )
        ).scalar_one_or_none()
        if rs_2 is None:
            rs_2 = contract.insert_rate_script(sess, oct_start, {})

        if len(year_pdfs) > 0:
            file_name, url = sorted(year_pdfs.items())[-1]

            rs_1_script = rs_1.make_script()
            if rs_1_script.get("a_file_name") != file_name:
                log(
                    f"Found new file {file_name} for rate script starting "
                    f"{hh_format(year_start)}"
                )
                rs_1.update(find_rate(file_name, BytesIO(download(s, url)), 0))
                log(f"Updated BSUoS rate script for {hh_format(year_start)}")

            rs_2_script = rs_2.make_script()
            if rs_2_script.get("a_file_name") != file_name:
                log(
                    f"Found new file {file_name} for rate script starting "
                    f"{hh_format(oct_start)}"
                )
                rs_2.update(find_rate(file_name, BytesIO(download(s, url)), 1))
                log(f"Updated BSUoS rate script for {hh_format(oct_start)}")

    log("Finished BSUoS spreadsheets")
    sess.commit()


def national_grid_import(sess, log, set_progress, s):
    log("Starting to check for new BSUoS forecast")

    CONTRACT_NAME = "bsuos"
    contract = Contract.find_non_core_by_name(sess, CONTRACT_NAME)
    if contract is None:
        contract = Contract.insert_non_core(
            sess, CONTRACT_NAME, "", {}, to_utc(ct_datetime(1996, 4, 1)), None, {}
        )

    block = None

    params = {
        "sql": """SELECT * FROM  "578b493e-db5c-41e3-8b52-f91c5f80389c" """
        """ORDER BY "_id" ASC LIMIT 100 """
    }
    res_j = api_get(s, "datastore_search_sql", params=params)
    for record in res_j["result"]["records"]:
        month_start_ct = to_ct(Datetime.strptime(record["Month"], "%b-%y"))
        if month_start_ct.month in (4, 10):
            block = {"start_date": to_utc(month_start_ct), "cost": 0, "vol": 0}

        if block is not None:
            block["cost"] += sum(
                float(record[t])
                for t in (
                    "Balancing Costs (Central) £m",
                    "Estimated Internal BSUoS & ESO Incentive £m",
                    "ALoMCP £m",
                    "CMP381 Deferred Costs £m",
                    "Winter Contingency Cost (Central) £m",
                    "Winter Security of Supply Cost (£m)",
                )
            )
            block["vol"] += float(record["Estimated BSUoS Volume (TWh)"])

            if month_start_ct.month in (3, 9):
                rs = sess.execute(
                    select(RateScript).where(
                        RateScript.contract == contract,
                        RateScript.start_date == block["start_date"],
                    )
                ).scalar_one_or_none()
                if rs is None:
                    rs = contract.insert_rate_script(sess, block["start_date"], {})

                rs_script = rs.make_script()
                rs_script["forecast_rate_gbp_per_mwh"] = block["cost"] / block["vol"]
                rs.update(rs_script)
                sess.commit()

    log("Finished BSUoS forecast")
    sess.commit()
