import atexit
import collections
import threading
import traceback

from sqlalchemy.sql.expression import select

from chellow.models import (
    Contract,
    GContract,
    RSession,
    Report,
)
from chellow.utils import ct_datetime_now


tester = None


def _run(log_f, sess):
    log_f("Starting to run tests.")
    for report in sess.execute(select(Report).order_by(Report.id)).scalars():
        _test_report(log_f, sess, report)
        sess.rollback()  # Avoid long-running transaction
    for contract in sess.execute(select(Contract).order_by(Contract.id)).scalars():
        _test_contract(log_f, sess, contract)
        sess.rollback()  # Avoid long-running transaction
    for g_contract in sess.execute(select(GContract).order_by(GContract.id)).scalars():
        _test_g_contract(log_f, sess, g_contract)
        sess.rollback()  # Avoid long-running transaction


class Tester(threading.Thread):
    def __init__(self):
        super().__init__(name="Tester")
        self.lock = threading.RLock()
        self.messages = collections.deque(maxlen=500)
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
            f"{ct_datetime_now().strftime('%Y-%m-%d %H:%M:%S')} - {message}"
        )

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                self.global_alert = None
                with RSession() as sess:
                    try:
                        _run(self.log, sess)
                    except BaseException:
                        self.log(traceback.format_exc())
                        self.global_alert = (
                            "There's a problem with the "
                            "<a href='/tester'>Automatic Tester</a>."
                        )
                        sess.rollback()
                    finally:
                        self.lock.release()
                        self.log("Finished running tests.")

            self.going.wait(60 * 60 * 24)
            self.going.clear()


def _test_report(logger, sess, report):
    logger(f"Starting to test local report {report.id} {report.name}.")
    code = compile(report.script, "<string>", "exec")
    ns = {"report_id": report.id, "template": report.template}
    exec(code, ns)
    if "test" in ns:
        ns["test"]()


def _test_contract(logger, sess, contract):
    logger(
        f"Starting to test {contract.market_role.description} contract {contract.id} "
        f"{contract.name}."
    )
    code = compile(contract.charge_script, "<string>", "exec")
    ns = {"db_id": contract.id}
    exec(code, ns)
    if "test" in ns:
        ns["test"]()


def _test_g_contract(logger, sess, g_contract):
    logger(
        f"Starting to test gas {'industry' if g_contract.is_industry else 'supplier'} "
        f"contract {g_contract.id} {g_contract.name}."
    )
    code = compile(g_contract.charge_script, "<string>", "exec")
    ns = {"db_id": g_contract.id, "properties": g_contract.make_properties()}
    exec(code, ns)
    if "test" in ns:
        ns["test"]()


def get_importer():
    return tester


def startup():
    global tester
    tester = Tester()
    tester.start()


@atexit.register
def shutdown():
    if tester is not None:
        tester.stop()
