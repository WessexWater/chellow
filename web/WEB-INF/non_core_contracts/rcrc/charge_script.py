from net.sf.chellow.physical import HhStartDate, Configuration
from net.sf.chellow.billing import Contract, RateScript
from java.util import Date, Timer, TimerTask, Calendar, Properties, GregorianCalendar, TimeZone, Locale
from java.util.concurrent.locks import ReentrantLock
from java.text import SimpleDateFormat
from net.sf.chellow.monad.types import MonadDate
from net.sf.chellow.monad import Hiber, UserException, Monad
from java.io import StringReader
from org.apache.http.protocol import HTTP
from org.apache.http.client.entity import UrlEncodedFormEntity
from org.apache.http.util import EntityUtils
from org.apache.http import HttpHost
from org.apache.http.conn.params import ConnRoutePNames
from org.apache.http.impl.client import DefaultHttpClient
from org.apache.http.message import BasicNameValuePair
from org.apache.http.client.methods import HttpGet, HttpPost
from com.Ostermiller.util import CSVParser
import sys
import types
import threading
import csv
import collections
import datetime
import pytz
import traceback
from dateutil.relativedelta import relativedelta


Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException', 'HH']})

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
                    sess = session()
                    self.log("Starting to check RCRCs.")
                    contract = Contract.get_non_core_by_name(sess, 'rcrc')
                    latest_rate_script = sess.query(RateScript).filter(RateScript.contract_id==contract.id).order_by(RateScript.start_date.desc()).first()
                    latest_rate_script_id = latest_rate_script.id
                    latest_rate_script_text = latest_rate_script.script

                    latest_rate_start = latest_rate_script.start_date
                    this_month_start = datetime.datetime(latest_rate_start.year, latest_rate_start.month, 1, tzinfo=pytz.utc)
                    next_month_start = this_month_start + relativedelta(months=1)
                    now = datetime.datetime.now(pytz.utc)
                    if now > next_month_start:
                        self.log("Checking to see if data is available from " + str(this_month_start) + " to " + str(next_month_start - HH) + " on Elexon Portal.")
                        config = Contract.get_non_core_by_name(sess, 'configuration')
                        props = config.make_properties()

                        scripting_key = props.get(ELEXON_PORTAL_SCRIPTING_KEY_KEY)
                        if scripting_key is None:
                            raise UserException("The property " + ELEXON_PORTAL_SCRIPTING_KEY_KEY + " cannot be found in the configuration properties.")

                        proxy_host = props.get(self.PROXY_HOST_KEY)

                        client = DefaultHttpClient()
                        if proxy_host is not None:
                            proxy_port = properties.get(self.PROXY_PORT_KEY)
                            if proxy_port is None:
                                raise UserException("The property " + self.PROXY_HOST_KEY + " is set, but the property " + self.PROXY_PORT_KEY + " is not.")
                            proxy = HttpHost(proxy_host, int(proxy_port), "http")
                            client.getParams().setParameter(ConnRoutePNames.DEFAULT_PROXY, proxy)

                        http_get = HttpGet('https://downloads.elexonportal.co.uk/file/download/RCRC_FILE?key=' + scripting_key)
                        entity = client.execute(http_get).getEntity()
                        csv_is = entity.getContent()
                        parser = CSVParser(csv_is)
                        values = parser.getLine()
                        values = parser.getLine()
                        month_rcrcs = {}
                        while values is not None:
                            hh_date = datetime.datetime.strptime(values[0], "%d/%m/%Y").replace(tzinfo=pytz.utc)
                            hh_date += relativedelta(minutes=30*int(values[2]))
                            if not hh_date < this_month_start and hh_date < next_month_start:
                                month_rcrcs[key_format(hh_date)] = values[3]
                            values = parser.getLine()

                        if key_format(next_month_start - HH) in month_rcrcs:
                            self.log("The whole month's data is there.")
                            script = "def rates():\n    return {\n" + ',\n'.join("'" + k + "': " + month_rcrcs[k] for k in sorted(month_rcrcs.keys())) + "}"
                            set_read_write(sess)
                            contract = Contract.get_non_core_by_name(sess, 'rcrc')
                            contract.insert_rate_script(sess, next_month_start, latest_rate_script_text)
                            rs = RateScript.get_by_id(sess, latest_rate_script_id)
                            contract.update_rate_script(sess, rs, rs.start_date, rs.finish_date, script)
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
