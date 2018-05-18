import csv
import threading
import collections
import traceback
from dateutil.relativedelta import relativedelta
import requests
from chellow.models import (
    Session, Contract, RateScript, get_non_core_contract_id)
from chellow.utils import HH, hh_format, utc_datetime_now, to_utc, to_ct
from werkzeug.exceptions import BadRequest
import atexit
from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation
from zish import loads


ELEXON_PORTAL_SCRIPTING_KEY_KEY = 'elexonportal_scripting_key'


def key_format(dt):
    return dt.strftime("%d %H:%M Z")


def hh(data_source):
    rate_set = data_source.supplier_rate_sets['tlm']

    try:
        cache = data_source.caches['tlms']
    except KeyError:
        cache = data_source.caches['tlms'] = {}

    for h in data_source.hh_data:
        try:
            h['tlm'] = tlm = cache[h['start-date']]
        except KeyError:
            h_start = h['start-date']
            db_id = get_non_core_contract_id('tlms')
            rates = data_source.hh_rate(db_id, h_start)['tlms']

            key = h_start.strftime("%d %H:%M Z")
            if key in rates:
                try:
                    h['tlm'] = tlm = cache[h_start] = float(rates[key])
                except TypeError as e:
                    raise BadRequest(
                        "For the TLMs rate script at " + hh_format(h_start) +
                        " the rate 'tlms' has the problem: " + str(e))
            else:
                h['tlm'] = tlm = cache[h_start] = float(
                    sorted(rates.items())[-1][1])

        rate_set.add(tlm)
        h['nbp-kwh'] = h['gsp-kwh'] * tlm


tlm_importer = None


class TlmImporter(threading.Thread):
    def __init__(self):
        super(TlmImporter, self).__init__(name="TLM Importer")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=100)
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
                sess = None
                try:
                    sess = Session()
                    self.log("Starting to check TLMs.")
                    contract = Contract.get_non_core_by_name(sess, 'tlms')
                    latest_rs = sess.query(RateScript).filter(
                        RateScript.contract_id == contract.id).order_by(
                        RateScript.start_date.desc()).first()
                    latest_rs_id = latest_rs.id
                    next_month_start = latest_rs.start_date + relativedelta(
                        months=1)
                    next_month_finish = latest_rs.start_date + relativedelta(
                        months=2) - HH

                    now = utc_datetime_now()
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
                            raise BadRequest(
                                "The property " +
                                ELEXON_PORTAL_SCRIPTING_KEY_KEY +
                                " cannot be found in the configuration " +
                                "properties.")

                        contract_props = contract.make_properties()
                        url_str = ''.join(
                            (
                                contract_props['url'],
                                'file/download/TLM_FILE?key=',
                                scripting_key))

                        r = requests.get(url_str)
                        parser = csv.reader(
                            (l.decode() for l in r.iter_lines()),
                            delimiter=',', quotechar='"')
                        self.log("Opened " + url_str + ".")

                        next(parser, None)
                        month_tlms = {}
                        for values in parser:
                            hh_date_ct = to_ct(
                                Datetime.strptime(values[0], "%d/%m/%Y"))
                            hh_date = to_utc(hh_date_ct)
                            hh_date += relativedelta(minutes=30*int(values[2]))
                            off_taking_str = values[4]
                            try:
                                off_taking = Decimal(off_taking_str)
                            except InvalidOperation as e:
                                raise BadRequest(
                                    "Problem parsing 'off-taking' field '" +
                                    off_taking_str + "' in the row " + str(
                                        values) + ".")
                            delivering = Decimal(values[5])

                            if next_month_start <= hh_date <= \
                                    next_month_finish:
                                month_tlms[key_format(hh_date)] = {
                                    'off-taking': off_taking,
                                    'delivering': delivering}

                        if key_format(next_month_finish) in month_tlms:
                            self.log("The whole month's data is there.")
                            script = {
                                'tlms': dict(
                                    (k, month_tlms[k]['off-taking'])
                                    for k in month_tlms.keys())}
                            contract = Contract.get_non_core_by_name(
                                sess, 'tlms')
                            rs = RateScript.get_by_id(sess, latest_rs_id)
                            contract.update_rate_script(
                                sess, rs, rs.start_date,
                                rs.start_date + relativedelta(months=2) - HH,
                                loads(rs.script))
                            sess.flush()
                            new_start = rs.start_date + relativedelta(months=1)
                            contract.insert_rate_script(
                                sess, new_start, script)
                            sess.commit()
                            self.log(
                                "Added new rate script starting at " +
                                hh_format(new_start) + ".")
                        else:
                            msg = "There isn't a whole month there yet."
                            if len(month_tlms) > 0:
                                msg += "The last date is " + sorted(
                                    month_tlms.keys())[-1]
                            self.log(msg)
                except BadRequest as e:
                    self.log("Problem: " + e.description)
                    sess.rollback()
                except BaseException:
                    self.log("Outer problem " + traceback.format_exc())
                    sess.rollback()
                finally:
                    if sess is not None:
                        sess.close()
                    self.lock.release()
                    self.log("Finished checking TLM rates.")

            self.going.wait(30 * 60)
            self.going.clear()


def get_importer():
    return tlm_importer


def startup():
    global tlm_importer
    if tlm_importer is not None:
        raise BadRequest("The TLM importer has already been started.")
    tlm_importer = TlmImporter()
    tlm_importer.start()


@atexit.register
def shutdown():
    if tlm_importer is not None:
        tlm_importer.stop()
