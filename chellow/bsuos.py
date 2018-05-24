import xlrd
from dateutil.relativedelta import relativedelta
from datetime import datetime as Datetime
import traceback
import threading
import collections
from chellow.models import (
    RateScript, Contract, Session, get_non_core_contract_id)
from chellow.utils import hh_format, utc_datetime_now, to_utc, to_ct, HH
from werkzeug.exceptions import BadRequest
import atexit
import requests
from zish import loads, dumps
from decimal import Decimal
from sqlalchemy import or_
from sqlalchemy.sql.expression import null


def hh(data_source, run='RF'):
    rate_set = data_source.supplier_rate_sets['bsuos-rate']

    try:
        bsuos_cache = data_source.caches['bsuos'][run]
    except KeyError:
        try:
            top_cache = data_source.caches['bsuos']
        except KeyError:
            top_cache = data_source.caches['bsuos'] = {}

        try:
            bsuos_cache = top_cache[run]
        except KeyError:
            bsuos_cache = top_cache[run] = {}

    for h in data_source.hh_data:
        try:
            h['bsuos-gbp-per-kwh'] = bsuos_rate = bsuos_cache[h['start-date']]
        except KeyError:
            h_start = h['start-date']
            db_id = get_non_core_contract_id('bsuos')

            rates = data_source.hh_rate(db_id, h_start)['rates_gbp_per_mwh']

            try:
                bsuos_prices = rates[key_format(h_start)]
            except KeyError:
                bsuos_prices = sorted(rates.items())[-1][1]

            try:
                bsuos_price = bsuos_prices[run]
            except KeyError:
                try:
                    bsuos_price = bsuos_prices['RF']
                except KeyError:
                    try:
                        bsuos_price = bsuos_prices['SF']
                    except KeyError:
                        bsuos_price = bsuos_prices['II']

            h['bsuos-gbp-per-kwh'] = bsuos_rate = bsuos_cache[h_start] = float(
                bsuos_price) / 1000

        h['bsuos-gbp'] = h['nbp-kwh'] * bsuos_rate
        rate_set.add(bsuos_rate)


def key_format(dt):
    return dt.strftime("%d %H:%M")


bsuos_importer = None


class BsuosImporter(threading.Thread):
    def __init__(self):
        super(BsuosImporter, self).__init__(name="BSUoS Importer")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=500)
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.PROXY_HOST_KEY = 'proxy.host'
        self.PROXY_PORT_KEY = 'proxy.port'

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
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message)

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = self.global_alert = None
                caches = {}
                try:
                    sess = Session()
                    self.log("Starting to check BSUoS rates.")
                    contract = Contract.get_non_core_by_name(sess, 'bsuos')
                    props = contract.make_properties()
                    if props.get('enabled', False):
                        urls = set()
                        if props.get('discover_urls', False):
                            res = requests.get(
                                'https://www.nationalgrid.com/uk/electricity/'
                                'charging-and-methodology/'
                                'balancing-services-use-system-bsuos-charges')
                            src = res.text
                            for pref in (
                                    'Current_II%20_BSUoS_Data_',
                                    'Current_RF_BSUoS_Data_',
                                    'Current_SF_BSUoS_Data_'):
                                idx_start = src.find(pref)
                                idx_quote = src.find('"', idx_start)
                                title = src[idx_start:idx_quote]
                                urls.add(
                                    'https://www.nationalgrid.com/'
                                    'sites/default/files/documents/' + title)

                        urls.update(set(props.get('urls', [])))
                        url_list = sorted(urls)
                        self.log(
                            "List of URLs to process: " + str(url_list))
                        for url in url_list:
                            self.process_url(sess, caches, url, contract)
                    else:
                        self.log(
                            "The automatic importer is disabled. To "
                            "enable it, edit the contract properties to "
                            "set 'enabled' to True.")
                except BaseException:
                    self.log("Outer problem " + traceback.format_exc())
                    self.global_alert = \
                        "There's a problem with the BSUoS automatic importer."
                    sess.rollback()
                finally:
                    if sess is not None:
                        sess.close()
                    self.lock.release()
                    self.log("Finished checking BSUoS rates.")

            self.going.wait(60 * 60 * 24)
            self.going.clear()

    def process_url(self, sess, caches, url, contract):
        self.log("Checking to see if there's any new data at " + url)
        res = requests.get(url)
        self.log("Received " + str(res.status_code) + " " + res.reason)
        book = xlrd.open_workbook(file_contents=res.content)
        sheet = book.sheet_by_index(0)

        for row_index in range(1, sheet.nrows):
            row = sheet.row(row_index)

            raw_date_val = row[0].value
            if isinstance(raw_date_val, float):
                raw_date = Datetime(
                    *xlrd.xldate_as_tuple(raw_date_val, book.datemode))
            elif isinstance(raw_date_val, str):
                raw_date = Datetime.strptime(raw_date_val, "%d/%m/%Y")
            else:
                raise BadRequest(
                    "Type of date field " + str(raw_date_val) +
                    " not recognized.")

            hh_date_ct = to_ct(raw_date)
            hh_date_ct += relativedelta(
                minutes=30*(int(row[1].value) - 1))
            hh_date = to_utc(hh_date_ct)
            price = Decimal(str(row[2].value))
            run = row[5].value

            try:
                rs, rates = \
                    caches['bsuos']['scripts'][hh_date.year][hh_date.month]
            except KeyError:
                try:
                    bsuos_cache = caches['bsuos']
                except KeyError:
                    bsuos_cache = caches['bsuos'] = {}

                try:
                    script_cache = bsuos_cache['scripts']
                except KeyError:
                    script_cache = bsuos_cache['scripts'] = {}

                try:
                    yr_cache = script_cache[hh_date.year]
                except KeyError:
                    yr_cache = script_cache[hh_date.year] = {}

                rs = sess.query(RateScript).filter(
                    RateScript.contract == contract,
                    RateScript.start_date <= hh_date, or_(
                        RateScript.finish_date == null(),
                        RateScript.finish_date >= hh_date)).first()
                while rs is None:
                    self.log(
                        "There's no rate script at " + hh_format(hh_date) +
                        ".")
                    latest_rs = sess.query(RateScript).filter(
                        RateScript.contract == contract).order_by(
                        RateScript.start_date.desc()).first()
                    contract.update_rate_script(
                        sess, latest_rs, latest_rs.start_date,
                        latest_rs.start_date + relativedelta(months=2) - HH,
                        loads(latest_rs.script))
                    new_rs_start = latest_rs.start_date + relativedelta(
                        months=1)
                    contract.insert_rate_script(sess, new_rs_start, {})
                    sess.commit()
                    self.log(
                        "Added a rate script starting at " +
                        hh_format(new_rs_start) + ".")

                    rs = sess.query(RateScript).filter(
                        RateScript.contract == contract,
                        RateScript.start_date <= hh_date, or_(
                            RateScript.finish_date == null(),
                            RateScript.finish_date >= hh_date)).first()

                rates = loads(rs.script)
                yr_cache[hh_date.month] = rs, rates

            try:
                rts = rates['rates_gbp_per_mwh']
            except KeyError:
                rts = rates['rates_gbp_per_mwh'] = {}

            key = key_format(hh_date)
            try:
                existing = rts[key]
            except KeyError:
                existing = rts[key] = {}

            if run not in existing:
                existing[run] = price
                rs.script = dumps(rates)
                self.log(
                    "Added rate at " + hh_format(hh_date) + " for run " + run +
                    ".")

        sess.commit()
        book = sheet = None


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
