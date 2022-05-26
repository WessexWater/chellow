import atexit
import csv
import threading
import traceback
from collections import defaultdict, deque
from datetime import datetime as Datetime, timedelta as Timedelta
from decimal import Decimal

from dateutil.relativedelta import relativedelta


import requests

from sqlalchemy import select

from zish import loads

from chellow.models import GContract, GRateScript, Session
from chellow.utils import (
    c_months_u,
    hh_format,
    to_ct,
    to_utc,
    utc_datetime,
    utc_datetime_now,
)


def param_format(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


cv_importer = None


class CvImporter(threading.Thread):
    def __init__(self):
        super().__init__(name="CV Importer")
        self.lock = threading.RLock()
        self.messages = deque(maxlen=500)
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.PROXY_HOST_KEY = "proxy.host"
        self.PROXY_PORT_KEY = "proxy.port"
        self.global_alert = None

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
        self.messages.appendleft(f"{hh_format(utc_datetime_now())} - {message}")

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = self.global_alert = None
                try:
                    sess = Session()
                    fetch_cvs(sess, self.log)
                except BaseException:
                    self.log("Outer problem " + traceback.format_exc())
                    self.global_alert = (
                        "There's a problem with the gas CV automatic importer."
                    )
                    sess.rollback()
                finally:
                    if sess is not None:
                        sess.close()
                    self.lock.release()
                    self.log("Finished checking CV rates.")

            self.going.wait(30 * 60)
            self.going.clear()


def fetch_cvs(sess, log_f):
    log_f("Starting to check CV rates.")
    g_contract = GContract.get_industry_by_name(sess, "cv")
    latest_rs = (
        sess.execute(
            select(GRateScript)
            .where(GRateScript.g_contract == g_contract)
            .order_by(GRateScript.start_date.desc())
        )
        .scalars()
        .first()
    )
    latest_rs_id = latest_rs.id
    latest_rs_start_date_ct = to_ct(latest_rs.start_date)

    month_pairs = list(
        c_months_u(
            start_year=latest_rs_start_date_ct.year,
            start_month=latest_rs_start_date_ct.month,
            months=2,
        )
    )
    month_start, month_finish = month_pairs[1]

    now = utc_datetime_now()
    props = g_contract.make_properties()
    if not props.get("enabled", False):
        log_f(
            "The automatic importer is disabled. To enable it, edit the contract "
            "properties to set 'enabled' to true."
        )
        return

    search_start = month_start - relativedelta(days=1)
    search_finish = month_finish + relativedelta(days=1)
    if now <= search_finish:
        return

    url = props["url"]
    log_f(
        f"Checking to see if data is available from {hh_format(search_start)} to "
        f"{hh_format(search_finish)} at {url}"
    )

    res = requests.post(
        url,
        data={
            "LatestValue": "true",
            "PublicationObjectIds": "408:28,+408:5328,+408:5320,+408:5291,"
            "+408:5366,+408:5312,+408:5346,+408:5324,+408:5316,+408:5308,"
            "+408:5336,+408:5333,+408:5342,+408:5354,+408:82,+408:70,"
            "+408:59,+408:38,+408:49",
            "PublicationObjectStagingIds": "PUBOBJ1660,PUBOB4507,PUBOB4508,"
            "PUBOB4510,PUBOB4509,PUBOB4511,PUBOB4512,PUBOB4513,PUBOB4514,"
            "PUBOB4515,PUBOB4516,PUBOB4517,PUBOB4518,PUBOB4519,PUBOB4521,"
            "PUBOB4520,PUBOB4522,PUBOBJ1661,PUBOBJ1662",
            "Applicable": "applicableFor",
            "PublicationObjectCount": "19",
            "FromUtcDatetime": param_format(search_start),
            "ToUtcDateTime": param_format(search_finish),
            "FileType": "Csv",
        },
    )
    log_f(f"Received {res.status_code} {res.reason}")

    month_cv = defaultdict(dict)
    cf = csv.reader(res.text.splitlines())
    row = next(cf)  # Skip title row
    last_date = utc_datetime(1900, 1, 1)
    for row in cf:
        applicable_at_str = row[0]
        applicable_for_str = row[1]
        applicable_for = to_utc(
            to_ct(Datetime.strptime(applicable_for_str, "%d/%m/%Y"))
        )
        data_item = row[2]
        value_str = row[3]

        if "LDZ" in data_item and month_start <= applicable_for < month_finish:
            ldz = data_item[-3:-1]
            cvs = month_cv[ldz]
            applicable_at = to_utc(
                to_ct(Datetime.strptime(applicable_at_str, "%d/%m/%Y %H:%M:%S"))
            )
            last_date = max(last_date, applicable_at)
            cv = Decimal(value_str)
            try:
                existing = cvs[applicable_for.day]
                if applicable_at > existing["applicable_at"]:
                    existing["cv"] = cv
                    existing["applicable_at"] = applicable_at
            except KeyError:
                cvs[applicable_for.day] = {"cv": cv, "applicable_at": applicable_at}

    all_equal = len(set(map(len, month_cv.values()))) <= 1
    if last_date + Timedelta(days=1) > month_finish and all_equal:
        log_f("The whole month's data is there.")
        script = {"cvs": month_cv}
        contract = GContract.get_industry_by_name(sess, "cv")
        rs = GRateScript.get_by_id(sess, latest_rs_id)
        contract.update_g_rate_script(
            sess, rs, rs.start_date, month_finish, loads(rs.script)
        )
        sess.flush()
        contract.insert_g_rate_script(sess, month_start, script)
        sess.commit()
        log_f("Added new rate script.")
    else:
        log_f(
            f"There isn't a whole month there yet. The last date is "
            f"{hh_format(last_date)}."
        )


def get_importer():
    return cv_importer


def startup():
    global cv_importer
    cv_importer = CvImporter()
    cv_importer.start()


@atexit.register
def shutdown():
    if cv_importer is not None:
        cv_importer.stop()
