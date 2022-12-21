import atexit
import collections
import threading
import traceback
from base64 import b64decode
from importlib import import_module

import requests

from chellow.models import (
    Contract,
    Session,
)
from chellow.utils import utc_datetime_now


importer = None


def download(s, url):
    fl_json = s.get(url).json()
    return b64decode(fl_json["content"])


class RateServer(threading.Thread):
    def __init__(self):
        super().__init__(name="Rate Server")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=500)
        self.stopped = threading.Event()
        self.going = threading.Event()
        self.repo_url = "https://api.github.com/repos/WessexWater/chellow-rates"

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

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                sess = self.global_alert = None
                try:
                    self.log("Starting to import rates from the rate server")
                    sess = Session()
                    conf = Contract.get_non_core_by_name(sess, "configuration")
                    props = conf.make_properties()
                    repo_branch = props.get("rate_server_branch", "main")
                    s = requests.Session()
                    s.verify = False
                    repo_entry = s.get(self.repo_url).json()
                    if "message" in repo_entry:
                        raise Exception(
                            f"Message from the GitHub API: {repo_entry['message']}"
                        )

                    self.log(
                        f"Looking at {repo_entry['html_url']} and branch "
                        f"{'default' if repo_branch is None else repo_branch}"
                    )
                    branch_entry = s.get(
                        f"{self.repo_url}/branches/{repo_branch}"
                    ).json()

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
                        "chellow.e.dno_rate_parser",
                        "chellow.e.mdd_importer",
                        "chellow.e.tnuos",
                        "chellow.gas.dn_rate_parser",
                    ):
                        mod = import_module(mod_name)
                        mod.rate_server_import(sess, s, paths, self.log)
                except BaseException:
                    self.log(traceback.format_exc())
                    self.global_alert = "Rate Server: An import has failed"
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
