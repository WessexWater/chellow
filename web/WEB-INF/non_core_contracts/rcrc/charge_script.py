from net.sf.chellow.monad import Monad
import sys
import types
import threading
import csv
import collections
import datetime
import pytz
import traceback
import urllib2
from dateutil.relativedelta import relativedelta

Monad.getUtils()['impt'](globals(), 'db', 'utils')
Contract, RateScript = db.Contract, db.RateScript
UserException, HH = utils.UserException, utils.HH

ELEXON_PORTAL_SCRIPTING_KEY_KEY = 'elexonportal_scripting_key'


def hh(data_source):
    bill = data_source.supplier_bill

    try:
        cache = data_source.caches['rcrc']
    except KeyError:
        cache = {}
        data_source.caches['rcrc'] = cache

    rate_set = data_source.supplier_rate_sets['rcrc-rate']

    for hh in data_source.hh_data:
        try:
            hh['rcrc-gbp-per-kwh'] = rcrc = cache[hh['start-date']]
        except KeyError:
            h_start = hh['start-date']
            rates = data_source.hh_rate(db_id, h_start, 'rates')
            try:
                hh['rcrc-gbp-per-kwh'] = rcrc = cache[h_start] = float(rates[h_start.strftime("%d %H:%M Z")]) / 1000
            except KeyError:
                raise UserException("For the RCRC rate script at " + hh_format(h_start) + " the rate cannot be found.")

        rate_set.add(rcrc)
        bill['rcrc-kwh'] += hh['nbp-kwh']
        bill['rcrc-gbp'] += hh['nbp-kwh'] * rcrc


rcrc_importer = None

def key_format(dt):
    return dt.strftime("%d %H:%M Z")

class RcrcImporter(threading.Thread):
    def __init__(self):
        super(RcrcImporter, self).__init__()
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
        self.messages.appendleft(datetime.datetime.utcnow().replace(tzinfo=pytz.utc).strftime("%Y-%m-%d %H:%M:%S") + " - " + message)
        if len(self.messages) > 100:
            self.messages.pop()

    
    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = None
                try:
                    sess = db.session()
                    self.log("Starting to check RCRCs.")
                    contract = Contract.get_non_core_by_name(sess, 'rcrc')
                    latest_rs = sess.query(RateScript).filter(RateScript.contract_id == contract.id).order_by(RateScript.start_date.desc()).first()
                    latest_rs_id = latest_rs.id
                    latest_rs_start = latest_rs.start_date

                    month_start = latest_rs_start + relativedelta(months=1)
                    month_finish = month_start + relativedelta(months=1) - HH
                    now = datetime.datetime.now(pytz.utc)
                    if now > month_finish:
                        self.log("Checking to see if data is available from " + str(month_start) + " to " + str(month_finish) + " on Elexon Portal.")
                        config = Contract.get_non_core_by_name(sess, 'configuration')
                        props = config.make_properties()

                        scripting_key = props.get(ELEXON_PORTAL_SCRIPTING_KEY_KEY)
                        if scripting_key is None:
                            raise UserException("The property " + ELEXON_PORTAL_SCRIPTING_KEY_KEY + " cannot be found in the configuration properties.")

                        data = urllib2.urlopen('https://downloads.elexonportal.co.uk/file/download/RCRC_FILE?key=' + scripting_key)
                        parser = csv.reader(data, delimiter=',', quotechar='"')
                        piterator = iter(parser)
                        values = piterator.next()
                        values = piterator.next()
                        month_rcrcs = {}
                        for values in piterator:
                            hh_date = datetime.datetime.strptime(values[0], "%d/%m/%Y").replace(tzinfo=pytz.utc)
                            hh_date += relativedelta(minutes=30*int(values[2]))
                            if month_start <= hh_date <= month_finish:
                                month_rcrcs[key_format(hh_date)] = values[3]

                        if key_format(month_finish) in month_rcrcs:
                            self.log("The whole month's data is there.")
                            script = "def rates():\n    return {\n" + ',\n'.join("'" + k + "': " + month_rcrcs[k] for k in sorted(month_rcrcs.keys())) + "}"
                            db.set_read_write(sess)
                            contract = Contract.get_non_core_by_name(sess, 'rcrc')
                            rs = RateScript.get_by_id(sess, latest_rs_id)
                            contract.update_rate_script(sess, rs, rs.start_date, month_finish, rs.script)
                            contract.insert_rate_script(sess, month_start, script)
                            sess.commit()
                            self.log("Added new rate script.")
                        else:
                            self.log("There isn't a whole month there yet. The last date is " + sorted(month_rcrcs.keys())[-1])
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
                        self.log("Finished checking RCRC rates.")


            self.going.wait(30 * 60)
            self.going.clear()


def get_rcrc_importer():
    return rcrc_importer

def startup():
    global rcrc_importer
    rcrc_importer = RcrcImporter()
    rcrc_importer.start()

def shutdown():
    if rcrc_importer is not None:
        rcrc_importer.stop()
        if rcrc_importer.isAlive():
            raise UserException("Can't shut down RCRC importer, it's still running.")
