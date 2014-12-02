from net.sf.chellow.monad import Monad
import sys
import types
import collections
import pytz
import threading
import datetime
import traceback
from dateutil.relativedelta import relativedelta
import urllib2
import csv

Monad.getUtils()['impt'](globals(), 'db', 'utils')
Contract, RateScript = db.Contract, db.RateScript
HH, UserException = utils.HH, utils.UserException


ELEXON_PORTAL_SCRIPTING_KEY_KEY = 'elexonportal_scripting_key'


def identity_func(x):
    return x

def hh(supply_source):
    rate_sets = ds.supplier_rate_sets
    
    try:
        cache = ds.caches['system_price_elexon']
    except KeyError:
        cache = {}
        ds.caches['system_price_elexon'] = cache
        
    for hh in ds.hh_data:
        try:
            prices = cache[hh['start-date']]
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
                    prices[pref + '-gbp-per-kwh'] = float(rate[date_str]) / 1000 
                else:
                    raise UserException("Type returned by " + pref + "s at " + hh_format(dt) + " must be function or dictionary.")
            cache[hh['start-date']] = prices

        hh.update(prices)
        hh['ssp-gbp'] = hh['nbp-kwh'] * hh['ssp-gbp-per-kwh'] 
        hh['sbp-gbp'] = hh['nbp-kwh'] * hh['sbp-gbp-per-kwh']
        rate_sets['ssp'].add(hh['ssp-gbp-per-kwh'])
        rate_sets['sbp'].add(hh['sbp-gbp-per-kwh'])


system_price_importer = None

def key_format(dt):
    return dt.strftime("%d %H:%M Z")

class SystemPriceImporter(threading.Thread):
    def __init__(self):
        super(SystemPriceImporter, self).__init__()
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
        self.messages.appendleft(
            datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S") +
            " - " + message)
        if len(self.messages) > 100:
            self.messages.pop()

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = None
                try:
                    sess = db.session()
                    self.log("Starting to check System Prices.")
                    ct_tz = pytz.timezone('Europe/London')
                    contract = Contract.get_non_core_by_name(
                        sess, 'system_price_elexon')
                    latest_rs = sess.query(RateScript).filter(
                        RateScript.contract_id == contract.id).order_by(
                        RateScript.start_date.desc()).first()
                    latest_rs_id = latest_rs.id

                    latest_rs_start = latest_rs.start_date
                    month_start = latest_rs_start + relativedelta(months=1)
                    month_finish = latest_rs_start + \
                        relativedelta(months=2) - HH
                    now = datetime.datetime.now(pytz.utc)
                    if now > month_finish:
                        self.log(
                            "Checking to see if data is available from " +
                            str(month_start) + " to " + str(month_finish) +
                            " on Elexon Portal.")
                        config = Contract.get_non_core_by_name(
                            sess, 'configuration')
                        props = config.make_properties()

                        scripting_key = props.get(
                            ELEXON_PORTAL_SCRIPTING_KEY_KEY)
                        if scripting_key is None:
                            raise UserException(
                                "The property " +
                                ELEXON_PORTAL_SCRIPTING_KEY_KEY +
                                " cannot be found in the configuration "
                                "properties.")

                        data = urllib2.urlopen(
                            'https://downloads.elexonportal.co.uk/file/download/SSPSBPNIV_FILE?key=' + scripting_key)
                        parser = csv.reader(data, delimiter=',', quotechar='"')
                        piterator = iter(parser)
                        values = piterator.next()
                        values = piterator.next()

                        month_sps = {}
                        for values in piterator:
                            day, month, year = map(int, values[0].split('/'))
                            ct_start = ct_tz.localize(datetime.datetime(year, month, day))
                            hh_date = pytz.utc.normalize(ct_start.astimezone(pytz.utc))
                            hh_offset = int(values[1]) - 1
                            hh_date += relativedelta(minutes=30*hh_offset)
                            if month_start <= hh_date <= month_finish:
                                month_sps[key_format(hh_date)] = {'ssp': values[2], 'sbp': values[3]}

                        if key_format(month_finish) in month_sps:
                            self.log("The whole month's data is there.")
                            script = "def ssps():\n    return {\n" + ',\n'.join("'" + k + "': " + month_sps[k]['ssp'] for k in sorted(month_sps.keys())) + "}\n\ndef sbps():\n    return {\n" + ',\n'.join("'" + k + "': " + month_sps[k]['sbp'] for k in sorted(month_sps.keys())) + "}\n\n"
                            db.set_read_write(sess)
                            contract = Contract.get_non_core_by_name(sess, 'system_price_elexon')
                            rs = RateScript.get_by_id(sess, latest_rs_id)
                            contract.update_rate_script(
                                sess, rs, rs.start_date, month_finish,
                                rs.script)
                            contract.insert_rate_script(
                                sess, month_start, script)
                            sess.commit()
                            self.log("Added new rate script.")
                        else:
                            if len(month_sps) > 0:
                                self.log(
                                    "There isn't a whole month there. The "
                                    "last date is " +
                                    sorted(month_sps.keys())[-1])
                            else:
                                self.log("None of the month is there.")

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
                        self.log("Finished checking System Price rates.")

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
