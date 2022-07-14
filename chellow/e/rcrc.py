import atexit
import collections
import csv
import threading
import traceback
from decimal import Decimal

from dateutil.relativedelta import relativedelta

import requests

from werkzeug.exceptions import BadRequest

from zish import loads

from chellow.models import Contract, RateScript, Session, get_non_core_contract_id
from chellow.utils import (
    ct_datetime_parse,
    hh_format,
    to_utc,
    u_months_u,
    utc_datetime_now,
)


ELEXON_PORTAL_SCRIPTING_KEY_KEY = "elexonportal_scripting_key"


def hh(data_source):
    try:
        cache = data_source.caches["rcrc"]
    except KeyError:
        cache = data_source.caches["rcrc"] = {}

    for hh in data_source.hh_data:
        try:
            hh["rcrc-rate"] = rcrc = cache[hh["start-date"]]
        except KeyError:
            h_start = hh["start-date"]
            db_id = get_non_core_contract_id("rcrc")
            rates = data_source.hh_rate(db_id, h_start)["rates"]
            try:
                hh["rcrc-rate"] = rcrc = cache[h_start] = (
                    float(rates[key_format(h_start)]) / 1000
                )
            except KeyError:
                try:
                    dt = h_start - relativedelta(days=3)
                    hh["rcrc-rate"] = rcrc = cache[h_start] = (
                        float(rates[key_format(dt)]) / 1000
                    )
                except KeyError:
                    raise BadRequest(
                        f"For the RCRC rate script at {hh_format(dt)} the rate cannot "
                        f"be found."
                    )

        hh["rcrc-kwh"] = hh["nbp-kwh"]
        hh["rcrc-gbp"] = hh["nbp-kwh"] * rcrc


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
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message
        )

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = None
                try:
                    sess = Session()
                    _process(self.log, sess)
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


def _find_month(lines, month_start, month_finish):
    parser = csv.reader(lines, delimiter=",", quotechar='"')
    next(parser)
    next(parser)
    month_rcrcs = {}
    for values in parser:
        hh_date = to_utc(ct_datetime_parse(values[0], "%d/%m/%Y"))
        hh_date += relativedelta(minutes=30 * int(values[2]))
        if month_start <= hh_date <= month_finish:
            month_rcrcs[key_format(hh_date)] = Decimal(values[3])
    return month_rcrcs


def _process(log_f, sess):
    log_f("Starting to check RCRCs.")
    contract = Contract.get_non_core_by_name(sess, "rcrc")
    latest_rs = (
        sess.query(RateScript)
        .filter(RateScript.contract_id == contract.id)
        .order_by(RateScript.start_date.desc())
        .first()
    )
    latest_rs_id = latest_rs.id
    latest_rs_start = latest_rs.start_date

    months = list(
        u_months_u(
            start_year=latest_rs_start.year, start_month=latest_rs_start.month, months=2
        )
    )
    month_start, month_finish = months[1]
    now = utc_datetime_now()
    if now > month_finish:
        config = Contract.get_non_core_by_name(sess, "configuration")
        props = config.make_properties()

        scripting_key = props.get(ELEXON_PORTAL_SCRIPTING_KEY_KEY)
        if scripting_key is None:
            raise BadRequest(
                f"The property {ELEXON_PORTAL_SCRIPTING_KEY_KEY} cannot be found in "
                f"the configuration properties."
            )

        contract_props = contract.make_properties()
        url_str = f"{contract_props['url']}file/download/RCRC_FILE?key={scripting_key}"
        log_f(
            f"Downloading {url_str} to see if data is available from "
            f"{hh_format(month_start)} to {hh_format(month_finish)}."
        )

        sess.rollback()  # Avoid long-running transaction
        r = requests.get(url_str, timeout=60)
        month_rcrcs = _find_month(
            (x.decode() for x in r.iter_lines()), month_start, month_finish
        )
        if key_format(month_finish) in month_rcrcs:
            log_f("The whole month's data is there.")
            script = {"rates": month_rcrcs}
            contract = Contract.get_non_core_by_name(sess, "rcrc")
            rs = RateScript.get_by_id(sess, latest_rs_id)
            contract.update_rate_script(
                sess, rs, rs.start_date, month_finish, loads(rs.script)
            )
            contract.insert_rate_script(sess, month_start, script)
            sess.commit()
            log_f(f"Added a new rate script starting at {hh_format(month_start)}.")
        else:
            msg = "There isn't a whole month there yet."
            if len(month_rcrcs) > 0:
                msg += f" The last date is {sorted(month_rcrcs.keys())[-1]}"
            log_f(msg)


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
