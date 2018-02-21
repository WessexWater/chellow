from dateutil.relativedelta import relativedelta
import traceback
import threading
from collections import defaultdict, deque
from chellow.models import RateScript, Contract, Session
from chellow.utils import HH, hh_format, utc_datetime_now, to_utc
import atexit
import requests
import csv
from decimal import Decimal
from datetime import datetime as Datetime, timedelta as Timedelta
from zish import loads


def param_format(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


g_cv_importer = None


class GCvImporter(threading.Thread):
    def __init__(self):
        super(GCvImporter, self).__init__(name="GCv Importer")
        self.lock = threading.RLock()
        self.messages = deque()
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
        if len(self.messages) > 100:
            self.messages.pop()

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = None
                try:
                    sess = Session()
                    self.run_inner(sess)
                except BaseException:
                    self.log("Outer problem " + traceback.format_exc())
                    sess.rollback()
                finally:
                    if sess is not None:
                        sess.close()
                    self.lock.release()
                    self.log("Finished checking GCv rates.")

            self.going.wait(30 * 60)
            self.going.clear()

    def run_inner(self, sess):
        self.log("Starting to check GCv rates.")
        contract = Contract.get_non_core_by_name(sess, 'g_cv')
        latest_rs = sess.query(RateScript).filter(
            RateScript.contract == contract).order_by(
            RateScript.start_date.desc()).first()
        latest_rs_id = latest_rs.id
        this_month_start = latest_rs.start_date + relativedelta(months=1)
        next_month_start = this_month_start + relativedelta(months=1)
        now = utc_datetime_now()
        props = contract.make_properties()
        if props.get('enabled', False):
            search_finish = next_month_start + relativedelta(days=1)
            if now > search_finish:
                url = props['url']
                self.log(
                    "Checking to see if data is available from " +
                    hh_format(this_month_start) + " to " +
                    hh_format(search_finish) + " at " + url)

                res = requests.post(
                    url, data={
                        'LatestValue': 'true',
                        'PublicationObjectIds':
                            '408:12265,+408:4636,+408:4637,+408:4639,'
                            '+408:4638,+408:4640,+408:4641,+408:4642,'
                            '+408:4643,+408:4644,+408:4645,+408:4646,'
                            '+408:4647,+408:4648,+408:12269,+408:12268,'
                            '+408:12270,+408:12266,+408:12267',
                        'Applicable': 'applicableFor',
                        'PublicationObjectCount': '19',
                        'FromUtcDatetime': param_format(this_month_start),
                        'ToUtcDateTime': param_format(search_finish),
                        'FileType': 'Csv'})
                self.log("Received " + str(res.status_code) + " " + res.reason)

                month_cv = defaultdict(dict)
                cf = csv.reader(res.text.splitlines())
                row = next(cf)  # Skip title row
                last_date = to_utc(Datetime.min)
                for row in cf:
                    applicable_at_str = row[0]
                    applicable_for_str = row[1]
                    applicable_for = to_utc(
                        Datetime.strptime(applicable_for_str, "%d/%m/%Y"))
                    data_item = row[2]
                    value_str = row[3]

                    if 'LDZ' in data_item and \
                            this_month_start <= applicable_for < \
                            next_month_start:
                        ldz = data_item[-3:-1]
                        cvs = month_cv[ldz]
                        applicable_at = to_utc(
                            Datetime.strptime(
                                applicable_at_str, "%d/%m/%Y %H:%M:%S"))
                        last_date = max(last_date, applicable_at)
                        cv = Decimal(value_str)
                        try:
                            existing = cvs[applicable_for.day]
                            if applicable_at > existing['applicable_at']:
                                existing['cv'] = cv
                                existing['applicable_at'] = applicable_at
                        except KeyError:
                            cvs[applicable_for.day] = {
                                'cv': cv,
                                'applicable_at': applicable_at}

                all_equal = len(set(map(len, month_cv.values()))) <= 1
                if last_date + Timedelta(days=1) >= next_month_start and \
                        all_equal:
                    self.log("The whole month's data is there.")
                    script = {'cvs': month_cv}
                    contract = Contract.get_non_core_by_name(sess, 'g_cv')
                    rs = RateScript.get_by_id(sess, latest_rs_id)
                    contract.update_rate_script(
                        sess, rs, rs.start_date,
                        rs.start_date + relativedelta(months=2) - HH,
                        loads(rs.script))
                    sess.flush()
                    contract.insert_rate_script(
                        sess, rs.start_date + relativedelta(months=1), script)
                    sess.commit()
                    self.log("Added new rate script.")
                else:
                    self.log(
                        "There isn't a whole month there yet. The "
                        "last date is " + hh_format(last_date) + ".")
        else:
            self.log(
                "The automatic importer is disabled. To "
                "enable it, edit the contract properties to "
                "set 'enabled' to True.")


def get_importer():
    return g_cv_importer


def startup():
    global g_cv_importer
    g_cv_importer = GCvImporter()
    g_cv_importer.start()


@atexit.register
def shutdown():
    if g_cv_importer is not None:
        g_cv_importer.stop()
