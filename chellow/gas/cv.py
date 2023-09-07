import atexit
import csv
import threading
import traceback
from collections import deque
from datetime import datetime as Datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta


import requests

from sqlalchemy import select


from chellow.models import GContract, GRateScript, Session
from chellow.utils import (
    HH,
    c_months_u,
    hh_after,
    hh_format,
    to_ct,
    to_utc,
    utc_datetime_now,
)


def param_format(dt):
    return to_ct(dt).strftime("%Y-%m-%dT%H:%M:%S")


cv_importer = None


class CvImporter(threading.Thread):
    def __init__(self):
        super().__init__(name="CV Importer")
        self.lock = threading.RLock()
        self.messages = deque(maxlen=5000)
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
                sess = self.global_alert = g_contract = None
                with Session() as sess:
                    try:
                        g_contract = GContract.get_industry_by_name(sess, "cv")
                        fetch_cvs(sess, self.log, g_contract)
                    except BaseException:
                        self.log(f"Outer problem {traceback.format_exc()}")
                        if g_contract is None:
                            self.global_alert = (
                                "There's a problem with the gas CV automatic importer."
                            )
                        else:
                            self.global_alert = (
                                f"There's a problem with the <a "
                                f"href='/g/industry_contracts/{g_contract.id}'>gas CV "
                                f"automatic importer</a>."
                            )
                        sess.rollback()
                    finally:
                        self.lock.release()
                        self.log("Finished checking CV rates.")

            self.going.wait(60 * 60 * 24)
            self.going.clear()


def fetch_cvs(sess, log_f, g_contract):
    log_f("Starting to check CV rates.")
    props = g_contract.make_properties()
    if not props.get("enabled", False):
        log_f(
            "The automatic importer is disabled. To enable it, edit the contract "
            "properties to set 'enabled' to true."
        )
        return

    now = utc_datetime_now()
    state = g_contract.make_state()
    try:
        last_applicable_at = state["last_applicable_at"]
    except KeyError:
        last_applicable_at = now

    search_start = last_applicable_at - relativedelta(days=1)
    search_finish = now + relativedelta(days=1)

    url = (
        f"https://data.nationalgas.com/api/find-gas-data-download?applicableFor=N&"
        f"dateFrom={param_format(search_start)}&dateTo={param_format(search_finish)}&"
        f"dateType=NORMALDAY&latestFlag=Y&ids=PUBOBJ1660,PUBOB4507,PUBOB4508,PUBOB4510,"
        f"PUBOB4509,PUBOB4511,PUBOB4512,PUBOB4513,PUBOB4514,PUBOB4515,PUBOB4516,"
        f"PUBOB4517,PUBOB4518,PUBOB4519,PUBOB4521,PUBOB4520,PUBOB4522,PUBOBJ1661,"
        f"PUBOBJ1662&type=CSV"
    )
    log_f(
        f"Checking to see if data is was made available from {hh_format(search_start)} "
        f"to {hh_format(search_finish)} at {url}"
    )

    s = requests.Session()
    s.verify = False
    res = s.get(url)
    log_f(f"Received {res.status_code} {res.reason}")

    cf = csv.reader(res.text.splitlines())
    row = next(cf)  # Skip title row
    for row in cf:
        applicable_at_str = row[0]
        applicable_for_str = row[1]
        applicable_for_ct = to_ct(Datetime.strptime(applicable_for_str, "%d/%m/%Y"))
        data_item = row[2]
        value_str = row[3]

        if "LDZ" in data_item:
            ldz = data_item[-3:-1]
            applicable_at = to_utc(
                to_ct(Datetime.strptime(applicable_at_str, "%d/%m/%Y %H:%M:%S"))
            )
            last_applicable_at = max(last_applicable_at, applicable_at)
            cv = Decimal(value_str)
            month_pairs = list(
                c_months_u(
                    start_year=applicable_for_ct.year,
                    start_month=applicable_for_ct.month,
                    months=1,
                )
            )
            month_start, month_finish = month_pairs[0]
            rs = sess.execute(
                select(GRateScript).where(
                    GRateScript.g_contract == g_contract,
                    GRateScript.start_date == month_start,
                )
            ).scalar_one_or_none()
            if rs is None:
                if month_start < g_contract.start_g_rate_script.start_date:
                    rs = g_contract.start_g_rate_script
                    orig_script = g_contract.start_g_rate_script.make_script()
                    g_contract.update_g_rate_script(
                        sess, rs, month_start, rs.finish_date, {"cvs": {}}
                    )
                    g_contract.insert_g_rate_script(
                        sess, month_finish + HH, orig_script
                    )
                elif hh_after(month_start, g_contract.finish_g_rate_script.finish_date):
                    g_contract.update_g_rate_script(
                        sess,
                        g_contract.finish_g_rate_script,
                        g_contract.finish_g_rate_script.start_date,
                        month_finish,
                        g_contract.finish_g_rate_script.make_script(),
                    )
                    rs = g_contract.insert_g_rate_script(sess, month_start, {"cvs": {}})
                else:
                    rs = g_contract.insert_g_rate_script(sess, month_start, {"cvs": {}})

            script = rs.make_script()
            rs_cvs = script["cvs"]
            try:
                ldz_days = rs_cvs[ldz]
            except KeyError:
                ldz_days = rs_cvs[ldz] = {}

            ldz_days[applicable_for_ct.day] = {"applicable_at": applicable_at, "cv": cv}

            g_contract.update_g_rate_script(
                sess, rs, rs.start_date, rs.finish_date, script
            )
            sess.commit()
            log_f(
                f"Added applicable_for: {applicable_for_str}, "
                f"applicable_at: {applicable_at_str}, value: {cv}"
            )

    state["last_applicable_at"] = last_applicable_at
    g_contract.update_state(state)
    sess.commit()


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
