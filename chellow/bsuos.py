import atexit
import collections
import csv
import threading
import traceback
from datetime import datetime as Datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta

import requests

from sqlalchemy import or_
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

import xlrd

from zish import dumps, loads

from chellow.models import (
    Contract,
    RateScript,
    Session,
    get_non_core_contract_id,
)
from chellow.utils import HH, hh_format, to_ct, to_utc, utc_datetime_now


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
            db_id = get_non_core_contract_id("bsuos")

            rates = data_source.hh_rate(db_id, h_start)["rates_gbp_per_mwh"]

            try:
                bsuos_price_dict = rates[key_format(h_start)]
                bsuos_price = _find_price(run, bsuos_price_dict)
            except KeyError:
                ds = rates.values()
                bsuos_price = sum(_find_price(run, d) for d in ds) / len(ds)

            h["bsuos-rate"] = bsuos_rate = bsuos_cache[h_start] = (
                float(bsuos_price) / 1000
            )

        h["bsuos-kwh"] = h["nbp-kwh"]
        h["bsuos-gbp"] = h["nbp-kwh"] * bsuos_rate


def _find_price(run, prices):
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
    return price


def key_format(dt):
    return dt.strftime("%d %H:%M")


bsuos_importer = None


def _save_cache(sess, cache):
    for yr, yr_cache in cache.items():
        for month, (rs, rates, rts) in tuple(yr_cache.items()):
            rs.script = dumps(rates)
            sess.commit()
            del yr_cache[month]


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
                sess = self.global_alert = None
                try:
                    sess = Session()
                    self.log("Starting to check BSUoS rates.")
                    contract = Contract.get_non_core_by_name(sess, "bsuos")
                    props = contract.make_properties()
                    if props.get("enabled", False):
                        urls = set(props.get("urls", []))
                        if props.get("discover_urls", False):
                            urls.update(_discover_urls(self.log))

                        url_list = sorted(urls)
                        self.log(f"List of URLs to process: {url_list}")
                        for url in url_list:
                            _process_url(self.log, sess, url, contract)
                    else:
                        self.log(
                            "The automatic importer is disabled. To enable it, edit "
                            "the contract properties to set 'enabled' to True."
                        )
                except BaseException:
                    self.log(f"Outer problem {traceback.format_exc()}")
                    self.global_alert = (
                        "There's a problem with the BSUoS automatic importer."
                    )
                    sess.rollback()
                finally:
                    if sess is not None:
                        sess.close()
                    self.lock.release()
                    self.log("Finished checking BSUoS rates.")

            self.going.wait(60 * 60 * 24)
            self.going.clear()


def _find_file_type(disp):
    # Content-Disposition: form-data; name="fieldName"; filename="filename.jpg"
    filetype = "csv"
    if disp is not None:
        fields = dict(v.strip().lower().split("=") for v in disp.split(";") if "=" in v)
        if "filename" in fields:
            filetype = fields["filename"].split(".")[-1][:-1]

    return filetype


def _process_url(logger, sess, url, contract):
    logger(f"Checking to see if there's any new data at {url}")
    res = requests.get(url)
    content_disposition = res.headers.get("Content-Disposition")
    logger(f"Received {res.status_code} {res.reason} {content_disposition}")
    cache = {}
    parsed_rows = []

    filetype = _find_file_type(content_disposition)
    if filetype == "csv":
        reader = csv.reader(res.text.splitlines())
        next(reader)  # Skip titles

        for row in reader:
            date_str = row[0]
            date = Datetime.strptime(date_str, "%d/%m/%Y")
            period_str = row[1]
            period = int(period_str)
            price_str = row[2]
            price = Decimal(price_str)
            run = row[5]
            parsed_rows.append((date, period, price, run))

    elif filetype == "xls":
        book = xlrd.open_workbook(file_contents=res.content)
        sheet = book.sheet_by_index(0)

        for row_index in range(1, sheet.nrows):
            row = sheet.row(row_index)

            date_val = row[0].value
            if isinstance(date_val, float):
                date = Datetime(*xlrd.xldate_as_tuple(date_val, book.datemode))
            elif isinstance(date_val, str):
                separator = date_val[2]
                fmat = separator.join(("%d", "%m", "%Y"))
                date = Datetime.strptime(date_val, fmat)
            else:
                raise BadRequest(f"Type of date field {date_val} not recognized.")

            period = int(row[1].value)
            price = Decimal(str(row[2].value))
            run = row[5].value
            parsed_rows.append((date, period, price, run))
    else:
        raise BadRequest(f"The file extension {filetype} is not recognised.")

    for date, period, price, run in parsed_rows:
        hh_date_ct = to_ct(date)
        hh_date_ct += relativedelta(minutes=30 * (period - 1))
        hh_date = to_utc(hh_date_ct)

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


def _discover_urls(logger):
    host = "https://www.nationalgrideso.com"
    page = (
        f"{host}/industry-information/charging/"
        "balancing-services-use-system-bsuos-charges"
    )
    logger(f"Searching for URLs on {page}")
    urls = set()
    res = requests.get(page)
    src = res.text
    for pref in (
        '" title="Current II BSUoS Data"',
        '" title="Current RF BSUoS Data"',
        '" title="Current SF BSUoS Data"',
    ):
        pidx = src.find(pref)
        aidx = src.rfind("<", 0, pidx)
        urls.add(host + src[aidx + 9 : pidx])
    return urls


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
