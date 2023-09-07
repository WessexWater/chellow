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


def api_get(s, path, params=None):
    url = f"https://api.nationalgrideso.com/api/3/action/{path}"
    res = s.get(url, params=params)
    try:
        res_j = res.json()
    except requests.exceptions.JSONDecodeError as e:
        raise BadRequest(
            f"Couldn't parse as JSON the content from {url} with error {e}: "
            f"{res.text}"
        )

    if "success" in res_j and not res_j["success"]:
        raise BadRequest(res_j)

    return res_j


def run_import(sess, log, set_progress):
    log("Starting to import data from the National Grid")
    s = requests.Session()
    s.verify = False

    for mod_name in ("chellow.e.tnuos", "chellow.e.bsuos"):
        mod = import_module(mod_name)
        mod.national_grid_import(sess, log, set_progress, s)


LAST_RUN_KEY = "last_run"
GLOBAL_ALERT = (
    "There's a problem with a <a href='/national_grid'>National Grid import</a>."
)
NG_STATE_KEY = "national_grid"


class NationalGrid(threading.Thread):
    def __init__(self):
        super().__init__(name="National Grid")
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
                    ng_state = state.get(NG_STATE_KEY, {})
                except BaseException as e:
                    msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                    self.log(f"{msg}{traceback.format_exc()}")
                    self.global_alert = GLOBAL_ALERT
                    sess.rollback()

            last_run = ng_state.get(LAST_RUN_KEY)
            if last_run is None or utc_datetime_now() - last_run > timedelta(days=1):
                self.going.set()

            if self.going.is_set():
                self.global_alert = None
                with Session() as sess:
                    try:
                        config = Contract.get_non_core_by_name(sess, "configuration")
                        state = config.make_state()
                        try:
                            ng_state = state[NG_STATE_KEY]
                        except KeyError:
                            ng_state = state[NG_STATE_KEY] = {}

                        ng_state[LAST_RUN_KEY] = utc_datetime_now()
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
                        self.log("Finished importing National Grid data.")

            else:
                self.log(
                    f"The importer was last run at {hh_format(last_run)}. There will "
                    f"be another import when 24 hours have elapsed since the last run."
                )
                self.going.wait(60 * 60)


def get_importer():
    return importer


def startup():
    global importer
    importer = NationalGrid()
    importer.start()


@atexit.register
def shutdown():
    if importer is not None:
        importer.stop()
