from net.sf.chellow.monad import Monad
import urllib.request
import csv
import threading
import collections
import traceback
import datetime
import pytz
from dateutil.relativedelta import relativedelta
import db
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils')

set_read_write, session = db.set_read_write, db.session
Contract, RateScript = db.Contract, db.RateScript
UserException, hh_after, HH = utils.UserException, utils.hh_after, utils.HH
hh_format = utils.hh_format
db_id = globals()['db_id']

ELEXON_PORTAL_SCRIPTING_KEY_KEY = 'elexonportal_scripting_key'


def key_format(dt):
    return dt.strftime("%d %H:%M Z")


def tlms_future(ns):
    old_result = ns['tlms']()
    last_value = old_result[sorted(old_result.keys())[-1]]

    new_result = collections.defaultdict(lambda: last_value, old_result)

    def tlms():
        return new_result
    return {'tlms': tlms}


def hh(data_source):
    rate_set = data_source.supplier_rate_sets['tlm']

    try:
        cache = data_source.caches['tlms']
    except KeyError:
        cache = {}
        data_source.caches['tlms'] = cache

        try:
            future_funcs = data_source.caches['future_funcs']
        except KeyError:
            future_funcs = {}
            data_source.caches['future_funcs'] = future_funcs

        try:
            future_funcs[db_id]
        except KeyError:
            future_funcs[db_id] = {'start_date': None, 'func': tlms_future}

    for h in data_source.hh_data:
        try:
            h['tlm'] = tlm = cache[h['start-date']]
        except KeyError:
            h_start = h['start-date']
            rates = data_source.hh_rate(db_id, h_start, 'tlms')
            try:
                h['tlm'] = tlm = cache[h_start] = \
                    rates[h_start.strftime("%d %H:%M Z")]
            except KeyError:
                raise UserException(
                    "For the TLMs rate script at " +
                    hh_format(h_start) + " the rate cannot be found.")
            except TypeError as e:
                raise UserException(
                    "For the TLMs rate script at " + hh_format(h_start) +
                    " the rate 'tlms' has the problem: " + str(e))

        rate_set.add(tlm)
        h['nbp-kwh'] = h['gsp-kwh'] * tlm


tlm_importer = None


class TlmImporter(threading.Thread):
    def __init__(self):
        super(TlmImporter, self).__init__(name="TLM Importer")
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
            datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
            .strftime("%Y-%m-%d %H:%M:%S") + " - " + message)
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
                    latest_rs = sess.query(RateScript).filter(
                        RateScript.contract_id == contract.id).order_by(
                        RateScript.start_date.desc()).first()
                    latest_rs_id = latest_rs.id
                    next_month_start = latest_rs.start_date + \
                        relativedelta(months=1)
                    next_month_finish = latest_rs.start_date + \
                        relativedelta(months=2) - HH

                    now = datetime.datetime.now(pytz.utc)
                    if now > next_month_start:
                        self.log(
                            "Checking to see if data is available from " +
                            str(next_month_start) + " to " +
                            str(next_month_finish) + " on Elexon Portal.")
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

                        data = urllib.request.urlopen(
                            'https://downloads.elexonportal.co.uk/file/'
                            'download/TLM_FILE?key=' + scripting_key)
                        self.log("Opened URL.")

                        ct_tz = pytz.timezone('Europe/London')

                        parser = csv.reader(data, delimiter=',', quotechar='"')
                        piterator = iter(parser)
                        values = piterator.next()
                        values = piterator.next()
                        month_tlms = {}
                        for values in piterator:
                            hh_date_ct = ct_tz.localize(
                                datetime.datetime.strptime(
                                    values[0], "%d/%m/%Y"))
                            hh_date = pytz.utc.normalize(
                                hh_date_ct.astimezone(pytz.utc))
                            hh_date += relativedelta(minutes=30*int(values[2]))
                            if next_month_start <= hh_date <= \
                                    next_month_finish:
                                month_tlms[key_format(hh_date)] = {
                                    'off-taking': values[3],
                                    'delivering': values[4]}

                        if key_format(next_month_finish) in month_tlms:
                            self.log("The whole month's data is there.")
                            script = "def tlms():\n    return {\n" + \
                                ',\n'.join(
                                    "'" + k + "': " +
                                    month_tlms[k]['off-taking'] for k in
                                    sorted(month_tlms.keys())) + "}"
                            set_read_write(sess)
                            contract = Contract.get_non_core_by_name(
                                sess, 'tlms')
                            rs = RateScript.get_by_id(sess, latest_rs_id)
                            contract.update_rate_script(
                                sess, rs, rs.start_date,
                                rs.start_date + relativedelta(months=2) - HH,
                                rs.script)
                            sess.flush()
                            contract.insert_rate_script(
                                sess, rs.start_date + relativedelta(months=1),
                                script)
                            sess.commit()
                            self.log("Added new rate script.")
                        else:
                            self.log(
                                "There isn't a whole month there yet. The "
                                "last date is " +
                                sorted(month_tlms.keys())[-1])
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
    if tlm_importer is not None:
        raise UserException("The TLM importer has already been started.")
    tlm_importer = TlmImporter()
    tlm_importer.start()


def shutdown():
    if tlm_importer is not None:
        tlm_importer.stop()
        if tlm_importer.isAlive():
            raise UserException(
                "Can't shut down TLM importer, it's still running.")
