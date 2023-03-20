import atexit
import collections
import threading
import traceback
from base64 import b64decode
from importlib import import_module

import requests

from werkzeug.exceptions import BadRequest

from chellow.models import (
    Contract,
    Session,
)
from chellow.utils import utc_datetime_now


importer = None


def download(s, url):
    fl_json = s.get(url).json()
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
    repo_res = s.get(repo_url)
    try:
        repo_entry = repo_res.json()
    except requests.exceptions.JSONDecodeError as e:
        raise BadRequest(
            f"Couldn't parse as JSON the content from {repo_url} with error {e}: "
            f"{repo_res.text}"
        )
    if "message" in repo_entry:
        raise Exception(f"Message from the GitHub API: {repo_entry['message']}")

    log(
        f"Looking at {repo_entry['html_url']} and branch "
        f"{'default' if repo_branch is None else repo_branch}"
    )
    branch_entry = s.get(f"{repo_url}/branches/{repo_branch}").json()

    tree_entry = s.get(
        branch_entry["commit"]["commit"]["tree"]["url"],
        params={"recursive": "true"},
    ).json()

    if tree_entry["truncated"]:
        raise Exception("Tree from rate server is truncated.")

    paths_list = []
    for sub_entry in tree_entry["tree"]:
        path = sub_entry["path"].split("/")
        if path[-1] != "README.md":
            paths_list.append((path, sub_entry["url"]))

    paths = tuple(paths_list)

    for mod_name in (
        "chellow.e.bsuos",
        "chellow.e.dno_rate_parser",
        "chellow.e.laf_import",
        "chellow.e.mdd_importer",
        "chellow.e.tnuos",
        "chellow.gas.dn_rate_parser",
    ):
        mod = import_module(mod_name)
        mod.rate_server_import(sess, log, set_progress, s, paths)


class RateServer(threading.Thread):
    def __init__(self):
        super().__init__(name="Rate Server")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=500)
        self.progress = ""
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
            f"{utc_datetime_now().strftime('%Y-%m-%d %H:%M:%S')} - {message}"
        )

    def set_progress(self, progress):
        self.progress = progress

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = self.global_alert = None
                try:
                    sess = Session()
                    run_import(sess, self.log, self.set_progress)
                except BaseException as e:
                    msg = f"{e.description} " if isinstance(e, BadRequest) else ""
                    self.log(f"{msg}{traceback.format_exc()}")
                    self.global_alert = (
                        "There's a problem with a <a href='/rate_server'>Rate Server "
                        "import</a>."
                    )
                    sess.rollback()
                finally:
                    if sess is not None:
                        sess.close()
                    self.lock.release()
                    self.log("Finished importing rates.")

            self.going.wait(60 * 60 * 24)
            self.going.clear()


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
