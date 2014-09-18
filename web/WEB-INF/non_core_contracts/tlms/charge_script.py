from net.sf.chellow.physical import Configuration
from net.sf.chellow.monad import Monad
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
import collections
import traceback
import datetime
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_

Monad.getUtils()['impt'](globals(), 'db', 'utils')

set_read_write, session = db.set_read_write, db.session
Contract, RateScript = db.Contract, db.RateScript
UserException, hh_after, HH = utils.UserException, utils.hh_after, utils.HH

ELEXON_PORTAL_SCRIPTING_KEY_KEY = 'elexonportal_scripting_key'

def key_format(dt):
    return dt.strftime("%d %H:%M Z")

def hh(data_source):
    rate_set = data_source.supplier_rate_sets['tlm']

    try:
        cache = data_source.caches['tlms']
    except KeyError:
        cache = {}
        data_source.caches['tlms'] = cache

    for h in data_source.hh_data:
        try:
            h['tlm'] = tlm = cache[h['start-date']]
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
                tlms = ns['tlms']()
                dt = chunk_start
                if isinstance(tlms, types.FunctionType):
                    transform_func = tlms
                    base_year = (rscript.start_date - HH).year
                    while dt <= chunk_finish:
                        cd = dt.replace(year=base_year)
                        if cd >= rscript.start_date:
                            cd = dt.replace(year=base_year - 1)
                        tlms = data_source.hh_rate(db_id, cd, 'tlms')
                        cache[dt] = transform_func(tlms[dt.strftime("%d %H:%M Z")])
                        dt += HH
                else:
                    while dt <= chunk_finish:
                        cache[dt] = tlms[dt.strftime("%d %H:%M Z")]
                        dt += HH

            h['tlm'] = tlm = cache[h['start-date']]

        rate_set.add(tlm)
        h['nbp-kwh'] = h['gsp-kwh'] * tlm

tlm_importer = None

class TlmImporter(threading.Thread):
    def __init__(self):
        super(TlmImporter, self).__init__()
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
                    self.log("Starting to check TLMs.")
                    contract = Contract.get_non_core_by_name(sess, 'tlms')
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
                        ct_tz = pytz.timezone('Europe/London')

                        http_get = HttpGet('https://downloads.elexonportal.co.uk/file/download/TLM_FILE?key=' + scripting_key)
                        entity = client.execute(http_get).getEntity()
                        csv_is = entity.getContent()
                        parser = CSVParser(csv_is)
                        values = parser.getLine()
                        values = parser.getLine()
                        month_tlms = {}
                        while values is not None:
                            hh_date_ct = ct_tz.localize(datetime.datetime.strptime(values[0], "%d/%m/%Y"))
                            hh_date = pytz.utc.normalize(hh_date_ct.astimezone(pytz.utc))
                            hh_date += relativedelta(minutes=30*int(values[2]))
                            if not hh_date < this_month_start and hh_date < next_month_start:
                                month_tlms[key_format(hh_date)] = {'off-taking': values[3], 'delivering': values[4]}
                            values = parser.getLine()

                        if key_format(next_month_start - HH) in month_tlms:
                            self.log("The whole month's data is there.")
                            script = "def tlms():\n    return {\n" + ',\n'.join("'" + k + "': " + month_tlms[k]['off-taking'] for k in sorted(month_tlms.keys())) + "}"
                            set_read_write(sess)
                            contract = Contract.get_non_core_by_name(sess, 'tlms')
                            contract.insert_rate_script(sess, next_month_start, latest_rate_script_text)
                            rs = RateScript.get_by_id(sess, latest_rate_script_id)
                            contract.update_rate_script(sess, rs, rs.start_date, rs.finish_date, script)
                            sess.commit()
                            self.log("Added new rate script.")
                        else:
                            self.log("There isn't a whole month there yet. The last date is " + sorted(month_tlms.keys())[-1])
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
                        self.log("Finished checking TLM rates.")

            self.going.wait(30 * 60)
            self.going.clear()


def get_tlm_importer():
    return tlm_importer

def startup():
    global tlm_importer
    tlm_importer = TlmImporter()
    tlm_importer.start()

def shutdown():
    if tlm_importer is not None:
        tlm_importer.stop()
        if tlm_importer.isAlive():
            raise UserException("Can't shut down TLM importer, it's still running.")