import atexit
import collections
import threading
import traceback
from datetime import timedelta

import requests

from sqlalchemy import select

from werkzeug.exceptions import BadRequest

from chellow.models import Contract, RateScript, Session
from chellow.utils import (
    ct_datetime,
    hh_format,
    to_utc,
    utc_datetime,
    utc_datetime_now,
    utc_datetime_parse,
)

GLOBAL_ALERT = """There's a problem with the <a
href="/bank_holidays">Bank Holiday importer</a>."""
LAST_RUN_KEY = "last_run"
BH_STATE_KEY = "bh"
DELAY_DAYS = 1

importer = None


def run_import(sess, log_f, set_progress):
    log_f("Starting to check bank holidays")
    contract_name = "bank_holidays"
    contract = Contract.find_non_core_by_name(sess, contract_name)
    if contract is None:
        contract = Contract.insert_non_core(
            sess,
            contract_name,
            "",
            {"enabled": True},
            to_utc(ct_datetime(1996, 4, 1)),
            None,
            {},
        )
        sess.commit()
    contract_props = contract.make_properties()

    if contract_props.get("enabled", True):
        url_str = "https://www.gov.uk/bank-holidays/england-and-wales.ics"

        log_f(f"Downloading from {url_str}.")
        res = requests.get(url_str)
        log_f(" ".join(("Received", str(res.status_code), res.reason)))
        PREFIX = "DTSTART;VALUE=DATE:"
        hols = collections.defaultdict(list)
        for line in res.text.splitlines():
            if line.startswith(PREFIX):
                dt = utc_datetime_parse(line[-8:], "%Y%m%d")
                hols[dt.year].append(dt)

        for year in sorted(hols.keys()):
            year_start = utc_datetime(year, 1, 1)
            rs = sess.scalars(
                select(RateScript).where(
                    RateScript.contract == contract,
                    RateScript.start_date == year_start,
                )
            ).one_or_none()
            if rs is None:
                log_f(f"Adding a new rate script starting at {hh_format(year_start)}.")

                rs = contract.insert_rate_script(sess, year_start, {})

            script = {"bank_holidays": [v.strftime("%Y-%m-%d") for v in hols[year]]}

            contract.update_rate_script(sess, rs, rs.start_date, rs.finish_date, script)
            sess.commit()
            log_f(f"Updated rate script starting at {hh_format(year_start)}.")
    else:
        log_f(
            "The automatic importer is disabled. To enable it, edit the contract "
            "properties to set 'enabled' to True."
        )


class BankHolidayImporter(threading.Thread):
    def __init__(self):
        super(BankHolidayImporter, self).__init__(name="Bank Holiday Importer")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=100)
        self.progress = ""
        self.stopped = threading.Event()
        self.going = threading.Event()
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
        self.messages.appendleft(
            f"{utc_datetime_now().strftime('%Y-%m-%d %H:%M:%S')} - {message}"
        )

    def set_progress(self, progress):
        self.progress = progress

    def run(self):
        while not self.stopped.is_set():
            with Session() as sess:
                try:
                    config = Contract.get_non_core_by_name(sess, "configuration")
                    state = config.make_state()
                    bh_state = state.get(BH_STATE_KEY, {})
                except BaseException as e:
                    msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                    self.log(f"{msg}{traceback.format_exc()}")
                    self.global_alert = GLOBAL_ALERT
                    sess.rollback()

            last_run = bh_state.get(LAST_RUN_KEY)
            if last_run is None or utc_datetime_now() - last_run > timedelta(
                days=DELAY_DAYS
            ):
                self.going.set()

            if self.going.is_set():
                self.global_alert = None
                with Session() as sess:
                    try:
                        config = Contract.get_non_core_by_name(sess, "configuration")
                        state = config.make_state()
                        try:
                            bh_state = state[BH_STATE_KEY]
                        except KeyError:
                            bh_state = state[BH_STATE_KEY] = {}

                        bh_state[LAST_RUN_KEY] = utc_datetime_now()
                        config.update_state(state)
                        sess.commit()
                        run_import(sess, self.log, self.set_progress)
                    except BaseException as e:
                        msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                        self.log(f"{msg}{traceback.format_exc()}")
                        self.global_alert = GLOBAL_ALERT
                        sess.rollback()
                    finally:
                        self.going.clear()
                        self.log("Finished checking bank holidays.")

            else:
                self.log(
                    f"The importer was last run at {hh_format(last_run)}. There will "
                    f"be another import when {DELAY_DAYS} days have elapsed since the "
                    f"last run."
                )
                self.going.wait(60 * 60)


def get_importer():
    return importer


def startup():
    global importer
    importer = BankHolidayImporter()
    importer.start()


@atexit.register
def shutdown():
    if importer is not None:
        importer.stop()
