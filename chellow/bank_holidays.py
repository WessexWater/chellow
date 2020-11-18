import atexit
import collections
import threading
import traceback

from chellow.models import Contract, RateScript, Session
from chellow.utils import (
    HH, hh_format, utc_datetime, utc_datetime_now, utc_datetime_parse,
)

from dateutil.relativedelta import relativedelta

import requests

from zish import loads


ELEXON_PORTAL_SCRIPTING_KEY_KEY = 'elexonportal_scripting_key'


bh_importer = None


class BankHolidayImporter(threading.Thread):
    def __init__(self):
        super(BankHolidayImporter, self).__init__(name="Bank Holiday Importer")
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
                    self.log("Starting to check bank holidays")
                    contract = Contract.get_non_core_by_name(
                        sess, 'bank_holidays')
                    contract_props = contract.make_properties()

                    if contract_props.get('enabled', False):
                        url_str = contract_props['url']

                        self.log("Downloading from " + url_str + ".")
                        res = requests.get(url_str)
                        self.log(
                            ' '.join(
                                (
                                    "Received", str(res.status_code),
                                    res.reason)))
                        PREFIX = 'DTSTART;VALUE=DATE:'
                        hols = collections.defaultdict(list)
                        for line in res.text.splitlines():
                            if line.startswith(PREFIX):
                                dt = utc_datetime_parse(line[-8:], "%Y%m%d")
                                hols[dt.year].append(dt)

                        for year in sorted(hols.keys()):
                            year_start = utc_datetime(year, 1, 1)
                            year_finish = year_start + \
                                relativedelta(years=1) - HH
                            rs = sess.query(RateScript).filter(
                                RateScript.contract == contract,
                                RateScript.start_date == year_start).first()
                            if rs is None:
                                self.log(
                                    "Adding a new rate script starting at " +
                                    hh_format(year_start) + ".")

                                latest_rs = sess.query(RateScript).filter(
                                    RateScript.contract == contract).\
                                    order_by(RateScript.start_date.desc()). \
                                    first()

                                contract.update_rate_script(
                                    sess, latest_rs, latest_rs.start_date,
                                    year_finish, loads(latest_rs.script))
                                rs = contract.insert_rate_script(
                                    sess, year_start, {})

                            script = {
                                'bank_holidays': [
                                    v.strftime("%Y-%m-%d")
                                    for v in hols[year]]}

                            contract.update_rate_script(
                                sess, rs, rs.start_date, rs.finish_date,
                                script)
                            sess.commit()
                            self.log(
                                "Updated rate script starting at " +
                                hh_format(year_start) + ".")
                    else:
                        self.log(
                            "The automatic importer is disabled. To "
                            "enable it, edit the contract properties to "
                            "set 'enabled' to True.")

                except BaseException:
                    self.log("Outer problem " + traceback.format_exc())
                    sess.rollback()
                finally:
                    if sess is not None:
                        sess.close()
                    self.lock.release()
                    self.log("Finished checking bank holidays.")

            self.going.wait(24 * 60 * 60)
            self.going.clear()


def get_importer():
    return bh_importer


def startup():
    global bh_importer
    bh_importer = BankHolidayImporter()
    bh_importer.start()


@atexit.register
def shutdown():
    if bh_importer is not None:
        bh_importer.stop()
