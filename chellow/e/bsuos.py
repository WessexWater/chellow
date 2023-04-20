import atexit
import collections
import csv
import threading
import traceback
from datetime import datetime as Datetime
from decimal import Decimal
from io import BytesIO

from dateutil.relativedelta import relativedelta

from pypdf import PdfReader

import requests

from sqlalchemy import or_, select
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
            db_id = get_non_core_contract_id("bsuos")

            rates = data_source.hh_rate(db_id, h_start)

            if h_start >= to_utc(ct_datetime(2023, 4, 1)):
                bsuos_price = float(rates["rate_gbp_per_mwh"])
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
                sess = self.global_alert = s = None
                try:
                    sess = Session()
                    self.log("Starting to check BSUoS rates.")
                    contract = Contract.get_non_core_by_name(sess, "bsuos")
                    props = contract.make_properties()
                    s = requests.Session()
                    s.verify = False
                    if props.get("enabled", False):
                        urls = set(props.get("urls", []))
                        if props.get("discover_urls", False):
                            sess.rollback()  # Avoid long-running transaction
                            urls.update(_discover_urls(self.log, s))

                        url_list = sorted(urls)
                        self.log(f"List of URLs to process: {url_list}")
                        for url in url_list:
                            _process_url(self.log, sess, url, contract, s)
                    else:
                        self.log(
                            "The automatic importer is disabled. To enable it, edit "
                            "the contract properties to set 'enabled' to True."
                        )
                except BaseException:
                    self.log(f"Outer problem {traceback.format_exc()}")
                    self.global_alert = (
                        f"There's a problem with the "
                        f"<a href='/non_core_contracts/{contract.id}'>BSUoS automatic "
                        f"importer</a>."
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
            filetype = fields["filename"].strip('"').split(".")[-1]

    return filetype


def _process_url(logger, sess, url, contract, s):
    logger(f"Checking to see if there's any new data at {url}")
    sess.rollback()  # Avoid long-running transaction
    res = s.get(url)
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


def _discover_urls(logger, s):
    host = "https://www.nationalgrideso.com"
    page = (
        f"{host}/industry-information/charging/"
        "balancing-services-use-system-bsuos-charges"
    )
    logger(f"Searching for URLs on {page}")
    urls = set()
    res = s.get(page)
    src = res.text

    for pref in ("RF", "SF", "II"):
        pidx = src.find(f'" target="_blank">Current {pref} BSUoS Data ')
        aidx = src.rfind('<a href="', 0, pidx)
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


def find_rate(file_name, file_like, rate_index):
    rate_script = {"a_file_name": file_name}
    rates = []

    reader = PdfReader(file_like)
    for page in reader.pages:
        for line in page.extract_text().splitlines():
            if line.startswith("BSUoS Tariff £/MWh"):
                for token in line.split():
                    if token[0] == "£" and token[1] != "/":
                        rates.append(Decimal(token[1:]))

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
                rs_1.update(find_rate(file_name, BytesIO(download(s, url)), 0))
                log(f"Updated BSUoS rate script for {hh_format(year_start)}")

            rs_2_script = rs_2.make_script()
            if rs_2_script.get("a_file_name") != file_name:
                rs_2.update(find_rate(file_name, BytesIO(download(s, url)), 1))
                log(f"Updated BSUoS rate script for {hh_format(oct_start)}")

    log("Finished BSUoS spreadsheets")
    sess.commit()
