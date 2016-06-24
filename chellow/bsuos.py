import xlrd
from dateutil.relativedelta import relativedelta
import datetime
import pytz
import traceback
import threading
import collections
from chellow.models import (
    RateScript, Contract, Session, set_read_write, get_non_core_contract_id)
from chellow.utils import HH, hh_format
import chellow.scenario
from werkzeug.exceptions import BadRequest
import atexit
import requests


create_future_func = chellow.scenario.make_create_future_func_monthly(
    'bsuos', ['rates_gbp_per_mwh'])


def hh(data_source):
    rate_set = data_source.supplier_rate_sets['bsuos-rate']
    bill = data_source.supplier_bill

    try:
        bsuos_cache = data_source.caches['bsuos']
    except KeyError:
        data_source.caches['bsuos'] = {}
        bsuos_cache = data_source.caches['bsuos']

        try:
            future_funcs = data_source.caches['future_funcs']
        except KeyError:
            future_funcs = {}
            data_source.caches['future_funcs'] = future_funcs

        db_id = get_non_core_contract_id('bsuos')
        try:
            future_funcs[db_id]
        except KeyError:
            future_funcs[db_id] = {
                'start_date': None, 'func': create_future_func(1, 0)}

    for h in data_source.hh_data:
        try:
            h['bsuos-gbp-per-kwh'] = bsuos_rate = bsuos_cache[h['start-date']]
        except KeyError:
            h_start = h['start-date']
            db_id = get_non_core_contract_id('bsuos')
            rates = data_source.hh_rate(db_id, h_start, 'rates_gbp_per_mwh')
            try:
                h['bsuos-gbp-per-kwh'] = bsuos_rate = bsuos_cache[h_start] = \
                    float(rates[h_start.strftime("%d %H:%M Z")]) / 1000
            except KeyError:
                raise BadRequest(
                    "For the BSUoS rate script at " + hh_format(h_start) +
                    " the rate cannot be found.")
            except TypeError as e:
                raise BadRequest(
                    "For the BSUoS rate script at " + hh_format(h_start) +
                    " the rate 'rates_gbp_per_mwh' has the problem: " + str(e))

        bill['bsuos-kwh'] += h['nbp-kwh']
        h['bsuos-gbp'] = h['nbp-kwh'] * bsuos_rate
        bill['bsuos-gbp'] += h['bsuos-gbp']
        rate_set.add(bsuos_rate)


def key_format(dt):
    return dt.strftime("%d %H:%M Z")


bsuos_importer = None


class BsuosImporter(threading.Thread):
    def __init__(self):
        super(BsuosImporter, self).__init__(name="BSUoS Importer")
        self.lock = threading.RLock()
        self.messages = collections.deque()
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
            datetime.datetime.utcnow().replace(
                tzinfo=pytz.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " +
            message)
        if len(self.messages) > 100:
            self.messages.pop()

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = None
                try:
                    sess = Session()
                    self.log("Starting to check BSUoS rates.")
                    contract = Contract.get_non_core_by_name(sess, 'bsuos')
                    latest_rs = sess.query(RateScript).filter(
                        RateScript.contract == contract).order_by(
                        RateScript.start_date.desc()).first()
                    latest_rs_id = latest_rs.id
                    this_month_start = latest_rs.start_date + \
                        relativedelta(months=1)
                    next_month_start = this_month_start + \
                        relativedelta(months=1)
                    now = datetime.datetime.now(pytz.utc)
                    if contract.make_properties().get('enabled', False):

                        if now > next_month_start:
                            self.log(
                                "Checking to see if data is available from " +
                                str(this_month_start) + " to " +
                                str(next_month_start - HH) +
                                " on the National Grid website.")
                            res = requests.get(
                                'http://www2.nationalgrid.com/'
                                'WorkArea/DownloadAsset.aspx?id=32719')
                            self.log(
                                "Received " + str(res.status_code) + " " +
                                res.reason)
                            book = xlrd.open_workbook(file_contents=res.txt)
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
                                    month_bsuos[key_format(hh_date)] = \
                                        row[2].value

                            if key_format(next_month_start - HH) in \
                                    month_bsuos:
                                self.log("The whole month's data is there.")
                                script = "def rates_gbp_per_mwh():\n    " \
                                    "return {\n" + ',\n'.join(
                                        "'" + k + "': " + str(month_bsuos[k])
                                        for k in sorted(
                                            month_bsuos.keys())) + "}"
                                set_read_write(sess)
                                contract = Contract.get_non_core_by_name(
                                    sess, 'bsuos')
                                rs = RateScript.get_by_id(sess, latest_rs_id)
                                contract.update_rate_script(
                                    sess, rs, rs.start_date,
                                    rs.start_date + relativedelta(months=2) -
                                    HH, rs.script)
                                sess.flush()
                                contract.insert_rate_script(
                                    sess,
                                    rs.start_date + relativedelta(months=1),
                                    script)
                                sess.commit()
                                self.log("Added new rate script.")
                            else:
                                self.log(
                                    "There isn't a whole month there yet. The "
                                    "last date is " +
                                    sorted(month_bsuos.keys())[-1])
                    else:
                        self.log(
                            "The automatic importer is disabled. To "
                            "enable it, edit the contract properties to "
                            "set 'enabled' to True.")
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
