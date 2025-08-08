import atexit
import collections
import threading
import traceback

from dateutil.relativedelta import relativedelta

from sqlalchemy import false, select

from chellow.models import ReportRun, Session
from chellow.utils import utc_datetime_now

rrun_deleter = None


def startup():
    global rrun_deleter

    rrun_deleter = ReportRunDeleter()
    rrun_deleter.start()


class ReportRunDeleter(threading.Thread):
    def __init__(self):
        super(ReportRunDeleter, self).__init__(name="ReportRun Deleter")
        self.messages = collections.deque(maxlen=1000)
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
            utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + " - " + message
        )

    def run(self):
        while not self.stopped.isSet():
            try:
                with Session() as sess:
                    now = utc_datetime_now()
                    cutoff_date = now - relativedelta(years=1)
                    for report_run in sess.scalars(
                        select(ReportRun).where(
                            ReportRun.date_created < cutoff_date,
                            ReportRun.data["keep"].as_boolean() == false(),
                        )
                    ):
                        report_run.delete(sess)
                        sess.commit()
                        self.log("Deleted report run")
            except BaseException:
                self.log("Outer problem " + traceback.format_exc())
                self.global_alert = (
                    "There's a problem with a "
                    "<a href='/report_runs'>Report Runs</a>."
                )
            finally:
                self.going.clear()
                self.log("Finished deleting Report Runs.")

            self.going.wait(24 * 60 * 60)
            self.going.clear()


def get_importer():
    return rrun_deleter


@atexit.register
def shutdown():
    if rrun_deleter is not None:
        rrun_deleter.stop()
