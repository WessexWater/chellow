import atexit
import collections
import csv
import threading
import traceback
from datetime import timedelta
from importlib import import_module
from io import StringIO

import requests

from werkzeug.exceptions import BadRequest

from chellow.models import (
    Contract,
    Session,
)
from chellow.utils import (
    ct_datetime_now,
    ct_datetime_parse,
    hh_format,
    to_utc,
    utc_datetime_now,
)

importer = None


def api_get(path, params=None):
    url = f"https://api.neso.energy/api/3/action/{path}"
    res = requests.get(url, params=params, timeout=120)
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


def csv_download(url):
    res = requests.get(url, timeout=120)
    csv_file = StringIO(res.text)
    return csv.DictReader(csv_file)


def csv_get(resource_id):
    res_j = api_get("resource_show", params={"id": resource_id})
    download_url = res_j["result"]["url"]
    return csv_download(download_url)


def csv_latest(package_id, last_import_date, name=None):
    params = {"id": package_id}
    res_j = api_get("datapackage_show", params=params)
    latest_lm = None
    latest_resource = None
    for resource in res_j["result"]["resources"]:
        if name is None or resource["name"].startswith(name):
            last_modified = resource["last_modified"]
            if last_import_date is None or last_modified > last_import_date:
                if latest_lm is None or last_modified > latest_lm:
                    latest_lm = last_modified
                    latest_resource = resource

    if latest_resource is None:
        return None
    else:
        return csv_download(latest_resource["path"])


def parse_date(date_str):
    if "/" in date_str:
        fmt = "%d/%m/%Y"
    elif "-" in date_str:
        fmt = "%Y-%m-%d"
    else:
        raise BadRequest(f"Couldn't parse the date {date_str}")

    return to_utc(ct_datetime_parse(date_str, fmt))


def run_import(sess, log, set_progress):
    log("Starting to import data from the NESO")

    for mod_name in (
        "chellow.e.aahedc",
        "chellow.e.tnuos",
        "chellow.e.bsuos",
        "chellow.e.triad",
    ):
        mod = import_module(mod_name)
        mod.neso_import(sess, log, set_progress)


LAST_RUN_KEY = "last_run"
GLOBAL_ALERT = "There's a problem with a <a href='/e/neso'>NESO import</a>."
NG_STATE_KEY = "neso"


class Neso(threading.Thread):
    def __init__(self):
        super().__init__(name="NESO")
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
                        self.log("Finished importing NESO data.")

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
    importer = Neso()
    importer.start()


@atexit.register
def shutdown():
    if importer is not None:
        importer.stop()
