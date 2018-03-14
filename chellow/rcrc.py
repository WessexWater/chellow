import threading
import csv
import collections
import traceback
import requests
from dateutil.relativedelta import relativedelta
from chellow.models import (
    Contract, RateScript, get_non_core_contract_id, Session)
from chellow.utils import HH, hh_format, utc_datetime_now, utc_datetime_parse
from werkzeug.exceptions import BadRequest
import atexit
from zish import loads
from decimal import Decimal


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
            db_id = get_non_core_contract_id('rcrc')
            rates = data_source.hh_rate(db_id, h_start)['rates']
            try:
                hh['rcrc-gbp-per-kwh'] = rcrc = cache[h_start] = float(
                    rates[key_format(h_start)]) / 1000
            except KeyError:
                try:
                    dt = h_start - relativedelta(days=3)
                    hh['rcrc-gbp-per-kwh'] = rcrc = cache[h_start] = float(
                        rates[key_format(dt)]) / 1000
                except KeyError:
                    raise BadRequest(
                        "For the RCRC rate script at " + hh_format(dt) +
                        " the rate cannot be found.")

        rate_set.add(rcrc)
        bill['rcrc-kwh'] += hh['nbp-kwh']
        bill['rcrc-gbp'] += hh['nbp-kwh'] * rcrc


rcrc_importer = None


def key_format(dt):
    return dt.strftime("%d %H:%M Z")


class RcrcImporter(threading.Thread):
    def __init__(self):
        super(RcrcImporter, self).__init__(name="RCRC Importer")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=100)
        self.stopped = threading.Event()
        self.going = threading.Event()

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
                    self.log("Starting to check RCRCs.")
                    contract = Contract.get_non_core_by_name(sess, 'rcrc')
                    latest_rs = sess.query(RateScript).filter(
                        RateScript.contract_id == contract.id).order_by(
                        RateScript.start_date.desc()).first()
                    latest_rs_id = latest_rs.id
                    latest_rs_start = latest_rs.start_date

                    month_start = latest_rs_start + relativedelta(months=1)
                    month_finish = month_start + relativedelta(months=1) - HH
                    now = utc_datetime_now()
                    if now > month_finish:
                        self.log(
                            "Checking to see if data is available from " +
                            hh_format(month_start) + " to " +
                            hh_format(month_finish) + " on Elexon Portal.")
                        config = Contract.get_non_core_by_name(
                            sess, 'configuration')
                        props = config.make_properties()

                        scripting_key = props.get(
                            ELEXON_PORTAL_SCRIPTING_KEY_KEY)
                        if scripting_key is None:
                            raise BadRequest(
                                "The property " +
                                ELEXON_PORTAL_SCRIPTING_KEY_KEY +
                                " cannot be found in the configuration "
                                "properties.")

                        contract_props = contract.make_properties()
                        url_str = ''.join(
                            (
                                contract_props['url'],
                                'file/download/RCRC_FILE?key=',
                                scripting_key))

                        r = requests.get(url_str)
                        parser = csv.reader(
                            (l.decode() for l in r.iter_lines()),
                            delimiter=',', quotechar='"')
                        next(parser)
                        next(parser)
                        month_rcrcs = {}
                        for values in parser:
                            hh_date = utc_datetime_parse(values[0], "%d/%m/%Y")
                            hh_date += relativedelta(minutes=30*int(values[2]))
                            if month_start <= hh_date <= month_finish:
                                month_rcrcs[key_format(hh_date)] = Decimal(
                                    values[3])
                        if key_format(month_finish) in month_rcrcs:
                            self.log("The whole month's data is there.")
                            script = {'rates': month_rcrcs}
                            contract = Contract.get_non_core_by_name(
                                sess, 'rcrc')
                            rs = RateScript.get_by_id(sess, latest_rs_id)
                            contract.update_rate_script(
                                sess, rs, rs.start_date, month_finish,
                                loads(rs.script))
                            contract.insert_rate_script(
                                sess, month_start, script)
                            sess.commit()
                            self.log(
                                "Added a new rate script starting at " +
                                hh_format(month_start) + ".")
                        else:
                            msg = "There isn't a whole month there yet."
                            if len(month_rcrcs) > 0:
                                msg += " The last date is " + \
                                    sorted(month_rcrcs.keys())[-1]
                            self.log(msg)
                except BaseException:
                    self.log("Outer problem " + traceback.format_exc())
                    sess.rollback()
                finally:
                    self.lock.release()
                    self.log("Finished checking RCRC rates.")
                    if sess is not None:
                        sess.close()

            self.going.wait(30 * 60)
            self.going.clear()


def get_importer():
    return rcrc_importer


def startup():
    global rcrc_importer
    rcrc_importer = RcrcImporter()
    rcrc_importer.start()


@atexit.register
def shutdown():
    if rcrc_importer is not None:
        rcrc_importer.stop()
