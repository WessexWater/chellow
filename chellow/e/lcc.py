import atexit
import collections
import threading
import traceback
from datetime import timedelta
from importlib import import_module

import requests

from werkzeug.exceptions import BadRequest

from chellow.models import (
    Contract,
    Session,
)
from chellow.utils import ct_datetime_now, hh_format, utc_datetime_now


importer = None


def api_records(log, s, resource_id, skip=0):
    url = f"https://dp.lowcarboncontracts.uk/datastore/dump/{resource_id}"
    params = {"format": "json"}
    res = s.get(url, params=params)
    log(f"Requested URL {res.url}")
    try:
        res_j = res.json()
    except requests.exceptions.JSONDecodeError as e:
        raise BadRequest(
            f"Couldn't parse as JSON the content from {url} with error {e}: "
            f"{res.text}"
        )

    if "success" in res_j and not res_j["success"]:
        raise BadRequest(res_j)

    field_titles = [f["id"] for f in res_j["fields"]]

    for record in res_j["records"][skip:]:
        yield {k: v for k, v in zip(field_titles, record)}


def run_import(sess, log, set_progress):
    log("Starting to import data from the Low Carbon Contracts Company")
    s = requests.Session()
    s.verify = False

    for mod_name in ("chellow.e.cfd", "chellow.e.rab"):
        mod = import_module(mod_name)
        mod.lcc_import(sess, log, set_progress, s)


LAST_RUN_KEY = "last_run"
GLOBAL_ALERT = (
    "There's a problem with a <a href='/e/lcc'>Low Carbon Contracts import</a>."
)
LCC_STATE_KEY = "lcc"
DELAY_DAYS = 7


class LowCarbonContracts(threading.Thread):
    def __init__(self):
        super().__init__(name="Low Carbon Contracts")
        self.messages = collections.deque(maxlen=500)
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

    def log(self, message):
        self.messages.appendleft(
            f"{ct_datetime_now().strftime('%Y-%m-%d %H:%M:%S')} - {message}"
        )

    def set_progress(self, progress):
        self.progress = progress

    def run(self):
        while not self.stopped.is_set():
            with Session() as sess:
                try:
                    config = Contract.get_non_core_by_name(sess, "configuration")
                    state = config.make_state()
                    lcc_state = state.get(LCC_STATE_KEY, {})
                except BaseException as e:
                    msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                    self.log(f"{msg}{traceback.format_exc()}")
                    self.global_alert = GLOBAL_ALERT
                    sess.rollback()

            last_run = lcc_state.get(LAST_RUN_KEY)
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
                            lcc_state = state[LCC_STATE_KEY]
                        except KeyError:
                            lcc_state = state[LCC_STATE_KEY] = {}

                        lcc_state[LAST_RUN_KEY] = utc_datetime_now()
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
                        self.log("Finished importing Low Carbon Contracts data.")

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
    importer = LowCarbonContracts()
    importer.start()


@atexit.register
def shutdown():
    if importer is not None:
        importer.stop()
