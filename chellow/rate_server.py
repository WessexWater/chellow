import atexit
import collections
import threading
import traceback
from base64 import b64decode
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


def api_get(s, url, params=None):
    res = s.get(url, params=params)
    try:
        res_j = res.json()
    except requests.exceptions.JSONDecodeError as e:
        raise BadRequest(
            f"Couldn't parse as JSON the content from {url} with error {e}: "
            f"{res.text}"
        )
    if "message" in res_j:
        raise Exception(f"Message from the GitHub API: {res_j['message']}")

    return res_j


def download(s, url):
    fl_json = api_get(s, url)
    return b64decode(fl_json["content"])


def run_import(sess, log, set_progress):
    log("Starting to import rates from the rate server")
    conf = Contract.get_non_core_by_name(sess, "configuration")
    props = conf.make_properties()
    repo_props = props.get("rate_server", {})
    repo_url = repo_props.get(
        "url", "https://api.github.com/repos/WessexWater/chellow-rates"
    )
    repo_branch = repo_props.get("branch", "main")
    s = requests.Session()
    s.verify = False

    repo_entry = api_get(s, repo_url)

    log(
        f"Looking at {repo_entry['html_url']} and branch "
        f"{'default' if repo_branch is None else repo_branch}"
    )
    branch_entry = api_get(s, f"{repo_url}/branches/{repo_branch}")

    tree_entry = api_get(
        s,
        branch_entry["commit"]["commit"]["tree"]["url"],
        params={"recursive": "true"},
    )

    if tree_entry["truncated"]:
        raise Exception("Tree from rate server is truncated.")

    paths_list = []
    for sub_entry in tree_entry["tree"]:
        path = sub_entry["path"].split("/")
        if path[-1].upper() == "README.MD":
            continue
        if len(path) == 1 and path[0] == "LICENSE":
            continue

        path[0] = int(path[0])
        paths_list.append((tuple(path), sub_entry["url"]))

    paths = tuple(paths_list)

    for mod_name in (
        "chellow.e.mdd_importer",
        "chellow.e.bsuos",
        "chellow.e.ccl",
        "chellow.e.dno_rate_parser",
        "chellow.e.triad",
        "chellow.e.lafs",
        "chellow.gas.ccl",
        "chellow.gas.dn_rate_parser",
        "chellow.e.tlms",
        "chellow.e.ro",
    ):
        mod = import_module(mod_name)
        mod.rate_server_import(sess, log, set_progress, s, paths)


LAST_RUN_KEY = "rate_server_last_run"


class RateServer(threading.Thread):
    def __init__(self):
        super().__init__(name="Rate Server")
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
                except BaseException as e:
                    msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                    self.log(f"{msg}{traceback.format_exc()}")
                    self.global_alert = (
                        "There's a problem with a <a href='/rate_server'>Rate Server "
                        "import</a>."
                    )
                    sess.rollback()

            last_run = state.get(LAST_RUN_KEY)
            if last_run is None or utc_datetime_now() - last_run > timedelta(days=1):
                self.going.set()

            if self.going.is_set():
                self.global_alert = None
                with Session() as sess:
                    try:
                        config = Contract.get_non_core_by_name(sess, "configuration")
                        state = config.make_state()
                        state[LAST_RUN_KEY] = utc_datetime_now()
                        config.update_state(state)
                        sess.commit()
                        run_import(sess, self.log, self.set_progress)
                    except BaseException as e:
                        msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                        self.log(f"{msg}{traceback.format_exc()}")
                        self.global_alert = (
                            "There's a problem with a "
                            "<a href='/rate_server'>Rate Server import</a>."
                        )
                        sess.rollback()
                    finally:
                        self.going.clear()
                        self.log("Finished importing rates.")

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
    importer = RateServer()
    importer.start()


@atexit.register
def shutdown():
    if importer is not None:
        importer.stop()
