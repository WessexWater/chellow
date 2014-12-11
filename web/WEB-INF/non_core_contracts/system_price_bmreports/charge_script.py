from net.sf.chellow.monad import Monad
from xml.dom.minidom import Node, parse
import types
import collections
import pytz
import threading
import datetime
import traceback
from dateutil.relativedelta import relativedelta
import urllib2
import db
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils')
RateScript, Contract = db.RateScript, db.Contract
UserException, HH, hh_format = utils.UserException, utils.HH, utils.hh_format
db_id = globals()['db_id']


def identity_func(x):
    return x


def hh(ds):
    rate_sets = ds.supplier_rate_sets
    try:
        system_price_cache = ds.caches['system_price']
    except KeyError:
        ds.caches['system_price'] = {}
        system_price_cache = ds.caches['system_price']

    for hh in ds.hh_data:
        try:
            prices = system_price_cache[hh['start-date']]
        except KeyError:
            prices = {}
            date_str = hh['start-date'].strftime("%d %H:%M Z")
            for pref in ['ssp', 'sbp']:
                transform_func = identity_func
                rate = ds.hh_rate(db_id, hh['start-date'], pref + 's')
                dt = hh['start-date']
                while isinstance(rate, types.FunctionType):
                    transform_func = rate
                    dt -= relativedelta(years=1)
                    rate = ds.hh_rate(db_id, dt, pref + 's')

                if isinstance(rate, dict):
                    rate = transform_func(rate)
                    prices[pref + '-gbp-per-kwh'] = float(rate[date_str]) / \
                        1000
                else:
                    raise UserException(
                        "Type returned by " + pref + "s at " + hh_format(dt) +
                        " must be function or dictionary.")
            system_price_cache[hh['start-date']] = prices

        hh.update(prices)
        hh['ssp-gbp'] = hh['nbp-kwh'] * hh['ssp-gbp-per-kwh']
        hh['sbp-gbp'] = hh['nbp-kwh'] * hh['sbp-gbp-per-kwh']
        rate_sets['ssp'].add(hh['ssp-gbp-per-kwh'])
        rate_sets['sbp'].add(hh['sbp-gbp-per-kwh'])


system_price_importer = None


class SystemPriceImporter(threading.Thread):
    def __init__(self):
        super(SystemPriceImporter, self).__init__()
        self.lock = threading.RLock()
        self.messages = collections.deque()
        self.stopped = threading.Event()
        self.going = threading.Event()

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
        self.messages.appendleft(
            datetime.datetime.utcnow().replace(tzinfo=pytz.utc).strftime(
                "%Y-%m-%d %H:%M:%S") + " - " + message)
        if len(self.messages) > 1000:
            self.messages.pop()

    def hhs(self, n_day_start, utc_month=None):
        day_url = "http://www.bmreports.com/bsp/additional/" + \
            "soapfunctions.php?element=SYSPRICE&dT=" + \
            n_day_start.strftime("%Y-%m-%d")

        self.log("Downloading data from " + day_url)
        ct_tz = pytz.timezone('Europe/London')

        f = urllib2.urlopen(day_url)
        dom = parse(f)

        prices = {}
        ct_day_start = ct_tz.localize(n_day_start)
        hh_start = pytz.utc.normalize(ct_day_start.astimezone(pytz.utc))

        for elem in dom.getElementsByTagName('ELEMENT'):
            vals = {}
            for elem_child in elem.childNodes:
                if elem_child.nodeType == Node.ELEMENT_NODE:
                    vals[elem_child.tagName] = elem_child.firstChild.nodeValue

            if utc_month is None or utc_month == hh_start.month:
                prices[hh_start.strftime("%d %H:%M Z")] = {
                    'ssp': vals['SSP'], 'sbp': vals['SBP']}
            hh_start += HH
        return prices

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = None
                try:
                    self.log("Starting to check system prices.")
                    sess = db.session()
                    contract = Contract.get_non_core_by_name(
                        sess, 'system_price_bmreports')

                    latest_rs = sess.query(RateScript).filter(
                        RateScript.contract == contract).order_by(
                        RateScript.start_date.desc()).first()
                    latest_rs_id = latest_rs.id

                    next_month_start = latest_rs.start_date + \
                        relativedelta(months=1)
                    next_month_finish = next_month_start + \
                        relativedelta(months=1) - HH

                    now = datetime.datetime.now(pytz.utc)

                    if contract.make_properties().get('enabled', False):
                        self.log("Is it after " + str(next_month_finish) + "?")
                        if now > next_month_finish:
                            n_stop_date = datetime.datetime(
                                next_month_finish.year,
                                next_month_finish.month,
                                next_month_finish.day) + relativedelta(days=1)

                            self.log(
                                "Checking to see if data is available on " +
                                str(n_stop_date) + " on bmreports.com.")

                            prices = self.hhs(n_stop_date)
                            if len(prices) == 0:
                                self.log(
                                    "Data isn't available on the "
                                    "bmreports.com yet.")
                            else:
                                self.log(
                                    "Starting to download data from "
                                    "bmreports.com.")
                                prices = {}
                                n_day_start = datetime.datetime(
                                    next_month_start.year,
                                    next_month_start.month,
                                    next_month_start.day) - relativedelta(
                                    days=1)
                                self.log(
                                    "Next month start " +
                                    str(next_month_start) + " n day start " +
                                    str(n_day_start))

                                while n_day_start <= n_stop_date:
                                    prices.update(
                                        self.hhs(
                                            n_day_start,
                                            next_month_start.month))
                                    n_day_start += relativedelta(days=1)

                                self.log(
                                    "Finished downloading data from "
                                    "bmreports.com.")
                                script = "def ssps():\n    return {\n" + \
                                    ',\n'.join(
                                        "'" + k + "': " +
                                        prices[k]['ssp'] for k in sorted(
                                            prices.keys())) + \
                                    "}\n\n\ndef sbps():\n    return {\n" + \
                                    ',\n'.join(
                                        "'" + k + "': " +
                                        prices[k]['sbp'] for k in sorted(
                                            prices.keys())) + "}"
                                db.set_read_write(sess)
                                contract = Contract.get_non_core_by_name(
                                    sess, 'system_price_bmreports')
                                latest_rs = RateScript.get_by_id(
                                    sess, latest_rs_id)
                                contract.update_rate_script(
                                    sess, latest_rs, latest_rs.start_date,
                                    next_month_finish, latest_rs.script)
                                contract.insert_rate_script(
                                    sess, next_month_start, script)
                                sess.commit()
                                self.log("Added new rate script.")
                        else:
                            self.log(
                                "Hasn't reached the end of the month yet.")

                    else:
                        self.log(
                            "The automatic importer is disabled. To enable "
                            "it, edit the contract properties to set "
                            "'enabled' to True.")

                except:
                    self.log("Outer problem " + traceback.format_exc())
                    sess.rollback()
                finally:
                    try:
                        if sess is not None:
                            sess.close()
                    finally:
                        self.lock.release()
                        self.log("Finished checking system prices.")

            self.going.wait(30 * 60)
            self.going.clear()


def get_importer():
    return system_price_importer


def startup():
    global system_price_importer
    system_price_importer = SystemPriceImporter()
    system_price_importer.start()


def shutdown():
    if system_price_importer is not None:
        system_price_importer.stop()
        if system_price_importer.isAlive():
            raise UserException(
                "Can't shut down System Price importer, it's still running.")
