import atexit
import collections
import threading
import traceback

import requests

import chellow.e.mdd_importer
from chellow.models import (
    Contract,
    Session,
)
from chellow.utils import utc_datetime_now


importer = None


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
                    repo_branch = props.get("rate_server_branch")
                    s = requests.Session()
                    s.verify = False
                    repo_entry = s.get(self.repo_url).json()
                    self.log(
                        f"Looking at {repo_entry['html_url']} and branch "
                        f"{'default' if repo_branch is None else repo_branch}"
                    )
                    chellow.e.mdd_importer.import_mdd(
                        sess, self.repo_url, repo_branch, self.log
                    )
                    chellow.gas.dn_rate_parser.rate_server_import(
                        sess, self.repo_url, repo_branch, self.log
                    )
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
