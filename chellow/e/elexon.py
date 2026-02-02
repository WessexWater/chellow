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


def download_file(log, scripting_key, file_name):
    params = {"key": scripting_key}
    url = f"https://downloads.elexonportal.co.uk/file/download/{file_name}"

    log(f"Downloading from {url}?key={scripting_key}")

    return requests.get(url, params=params, timeout=120)


def run_import(sess, log, set_progress, scripting_key):
    log("Starting to import data from Elexon")

    for mod_name in (
        "chellow.e.system_price",
        "chellow.e.tlms",
        "chellow.e.rcrc",
        "chellow.e.lafs",
    ):
        mod = import_module(mod_name)
        try:
            mod.elexon_import(sess, log, set_progress, scripting_key)
        except TypeError as e:
            raise BadRequest(f"Problem with module {mod_name}: {e}") from e


ELEXON_PORTAL_SCRIPTING_KEY_KEY = "elexonportal_scripting_key"
LAST_RUN_KEY = "last_run"
GLOBAL_ALERT = "There's a problem with an <a href='/e/elexon'>Elexon import</a>."
ELEXON_STATE_KEY = "elexon"


class Elexon(threading.Thread):
    def __init__(self):
        super().__init__(name="Elexon")
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
                    elexon_state = state.get(ELEXON_STATE_KEY, {})
                except BaseException as e:
                    msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                    self.log(f"{msg}{traceback.format_exc()}")
                    self.global_alert = GLOBAL_ALERT
                    sess.rollback()

            last_run = elexon_state.get(LAST_RUN_KEY)
            if last_run is None or utc_datetime_now() - last_run > timedelta(days=1):
                self.going.set()

            if self.going.is_set():
                self.global_alert = None
                with Session() as sess:
                    try:
                        config = Contract.get_non_core_by_name(sess, "configuration")
                        state = config.make_state()
                        try:
                            elexon_state = state[ELEXON_STATE_KEY]
                        except KeyError:
                            elexon_state = state[ELEXON_STATE_KEY] = {}

                        elexon_state[LAST_RUN_KEY] = utc_datetime_now()
                        config.update_state(state)
                        props = config.make_properties()
                        scripting_key = props.get(ELEXON_PORTAL_SCRIPTING_KEY_KEY)
                        sess.commit()
                        if scripting_key is None:
                            raise BadRequest(
                                f"The property {ELEXON_PORTAL_SCRIPTING_KEY_KEY} "
                                f"cannot be found in the configuration properties. "
                                f"A scripting key can be obtained from "
                                f"https://www.elexonportal.co.uk/"
                            )
                        run_import(sess, self.log, self.set_progress, scripting_key)
                    except BaseException as e:
                        msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                        self.log(f"{msg}{traceback.format_exc()}")
                        self.global_alert = GLOBAL_ALERT
                        sess.rollback()
                    finally:
                        self.going.clear()
                        self.log("Finished importing Elexon data.")

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
    importer = Elexon()
    importer.start()


@atexit.register
def shutdown():
    if importer is not None:
        importer.stop()
