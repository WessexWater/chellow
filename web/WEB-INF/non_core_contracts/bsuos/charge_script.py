from net.sf.chellow.monad import Monad
import sys
from java.lang import System
import xlrd
import types
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import joinedload_all
import datetime
import pytz
from pytz import timezone
from net.sf.chellow.monad import Monad
import traceback
import threading
import collections
from sqlalchemy import or_
import httplib

Monad.getUtils()['impt'](globals(), 'db', 'utils')

RateScript, Contract = db.RateScript, db.Contract
HH, hh_after, UserException = utils.HH, utils.hh_after, utils.UserException

def hh(data_source):
    rate_set = data_source.supplier_rate_sets['bsuos-rate']
    bill = data_source.supplier_bill
    try:
        bsuos_cache = data_source.caches['bsuos']
    except KeyError:
        data_source.caches['bsuos'] = {}
        bsuos_cache = data_source.caches['bsuos']

    for h in data_source.hh_data:
        try:
            h['bsuos-gbp-per-kwh'] = bsuos_rate = bsuos_cache[h['start-date']]
        except KeyError:
            for rscript in data_source.sess.query(RateScript).filter(RateScript.contract_id==db_id, RateScript.start_date<=data_source.finish_date, or_(RateScript.finish_date==None, RateScript.finish_date>=data_source.start_date)):
                if rscript.start_date < data_source.start_date:
                    chunk_start = data_source.start_date
                else:
                    chunk_start = rscript.start_date

                if hh_after(rscript.finish_date, data_source.finish_date):
                    chunk_finish = data_source.finish_date
                else:
                    chunk_finish = rscript.finish_date

                ns = {}
                exec(rscript.script, ns)
                rates = ns['rates_gbp_per_mwh']()
                dt = chunk_start
                if isinstance(rates, types.FunctionType):
                    transform_func = rates
                    base_year = (rscript.start_date - HH).year
                    while dt <= chunk_finish:
                        cd = dt.replace(year=base_year)
                        if cd >= rscript.start_date:
                            cd = dt.replace(year=base_year - 1)
                        rates = data_source.hh_rate(db_id, cd, 'rates_gbp_per_mwh')
                        bsuos_cache[dt] = float(transform_func(rates[dt.strftime("%d %H:%M Z")])) / 1000
                        dt += HH
                else:
                    while dt <= chunk_finish:
                        try:
                            bsuos_cache[dt] = float(rates[dt.strftime("%d %H:%M Z")]) / 1000
                        except KeyError:
                            raise UserException("For the BSUoS rate script at " + hh_format(dt) + " the rate cannot be found.")
                        dt += HH
            h['bsuos-gbp-per-kwh'] = bsuos_rate = bsuos_cache[h['start-date']]

        bill['bsuos-kwh'] += h['nbp-kwh']
        h['bsuos-gbp'] = h['nbp-kwh'] * bsuos_rate
        bill['bsuos-gbp'] += h['bsuos-gbp']
        rate_set.add(bsuos_rate)


def key_format(dt):
    return dt.strftime("%d %H:%M Z")


bsuos_importer = None

class BsuosImporter(threading.Thread):
    def __init__(self):
        super(BsuosImporter, self).__init__()
        self.lock = threading.RLock()
        self.messages = collections.deque()
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.PROXY_HOST_KEY = 'proxy.host'
        self.PROXY_PORT_KEY = 'proxy.port'

    def stop(self):
        self.stopped.set()
        self.going.set()

    def go(self):
        self.going.set()

    def is_locked(self):
        if self.lock.acquire(False):
            self.lock.release()
            return False
        else:
            return True

    def log(self, message):
        self.messages.appendleft(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " + message)
        if len(self.messages) > 100:
            self.messages.pop()

    

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = None
                try:
                    sess = db.session()
                    self.log("Starting to check BSUoS rates.")
                    contract = Contract.get_non_core_by_name(sess, 'bsuos')
                    latest_rate_script = sess.query(RateScript). \
                        filter(RateScript.contract_id==contract.id). \
                        order_by(RateScript.start_date.desc()).first()
                    latest_rate_script_id = latest_rate_script.id
                    latest_rate_script_text = latest_rate_script.script

                    latest_rate_start = latest_rate_script.start_date
                    this_month_start = datetime.datetime(
                        latest_rate_start.year, latest_rate_start.month, 1,
                        tzinfo=pytz.utc)
                    next_month_start = this_month_start + \
                        relativedelta(months=1)
                    now = datetime.datetime.now(pytz.utc)
                    if now > next_month_start and \
                            contract.make_properties().get('enabled', False):
                        self.log(
                            "Checking to see if data is available from " +
                            str(this_month_start) + " to " +
                            str(next_month_start - HH) + " on Elexon Portal.")
                        config = Contract.get_non_core_by_name(
                            sess, 'configuration')
                        props = config.make_properties()

                        conn = httplib.HTTPConnection("www2.nationalgrid.com")
                        conn.request(
                            "GET", "/WorkArea/DownloadAsset.aspx?id=32719")

                        res = conn.getresponse()
                        self.log(
                            "Received " + str(res.status) + " " + res.reason)
                        data = res.read()
                        book = xlrd.open_workbook(file_contents=data)
                        sheet = book.sheet_by_index(0)

                        ct_tz = pytz.timezone('Europe/London')

                        month_bsuos = {}
                        for row_index in range(1, sheet.nrows):
                            row = sheet.row(row_index)
                            raw_date = datetime.datetime(
                                *xlrd.xldate_as_tuple(
                                    row[0].value, book.datemode))
                            hh_date_ct = ct_tz.localize(raw_date)
                            hh_date = pytz.utc.normalize(
                                hh_date_ct.astimezone(pytz.utc))
                            hh_date += relativedelta(
                                minutes=30*int(row[1].value))
                            if not hh_date < this_month_start and \
                                    hh_date < next_month_start:
                                month_bsuos[key_format(hh_date)] = row[2].value

                        if key_format(next_month_start - HH) in month_bsuos:
                            self.log("The whole month's data is there.")
                            script = \
                                "def rates_gbp_per_mwh():\n    return {\n" + \
                                ',\n'.join("'" + k + "': " +
                                str(month_bsuos[k]) for k in \
                                    sorted(month_bsuos.keys())) + "}"
                            db.set_read_write(sess)
                            contract = Contract.get_non_core_by_name(
                                sess, 'bsuos')
                            contract.insert_rate_script(
                                sess, next_month_start,
                                latest_rate_script_text)
                            rs = RateScript.get_by_id(
                                sess, latest_rate_script_id)
                            contract.update_rate_script(
                                sess, rs, rs.start_date, rs.finish_date,
                                script)
                            sess.commit()
                            self.log("Added new rate script.")
                        else:
                            self.log(
                                "There isn't a whole month there yet. The "
                                "last date is " +
                                sorted(month_bsuos.keys())[-1])
                except:
                    self.log("Outer problem " + traceback.format_exc())
                    if sess is not None:
                        sess.rollback()
                finally:
                    try:
                        if sess is not None:
                            sess.close()
                    finally:
                        self.lock.release()
                        self.log("Finished checking BSUoS rates.")

            self.going.wait(30 * 60)
            self.going.clear()


def get_bsuos_importer():
    return bsuos_importer

def startup():
    global bsuos_importer
    bsuos_importer = BsuosImporter()
    bsuos_importer.start()

def shutdown():
    if bsuos_importer is not None:
        bsuos_importer.stop()
        if bsuos_importer.isAlive():
            raise UserException(
                "Can't shut down BSUoS importer, it's still running.")
