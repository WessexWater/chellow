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


def api_sql(s, sql):
    url = "https://dp.lowcarboncontracts.uk/api/3/action/datastore_search_sql"
    params = {"sql": sql}
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


def api_search(s, resource_id, sort=None):
    url = "https://dp.lowcarboncontracts.uk/api/3/action/datastore_search"
    params = {"resource_id": resource_id}
    if sort is not None:
        params["sort"] = sort
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


def run_import(sess, log, set_progress, scripting_key):
    log("Starting to import data from Elexon")
    s = requests.Session()
    s.verify = False

    for mod_name in (
        "chellow.e.system_price",
        "chellow.e.tlms",
        "chellow.e.rcrc",
        "chellow.e.lafs",
    ):
        mod = import_module(mod_name)
        mod.elexon_import(sess, log, set_progress, s, scripting_key)


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
                                f"cannot be found in the configuration properties."
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
