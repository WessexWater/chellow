import atexit
import collections
import threading
import traceback

from sqlalchemy.sql.expression import select

from werkzeug.exceptions import BadRequest

from chellow.models import (
    Contract,
    GContract,
    RSession,
    Report,
)
from chellow.utils import ct_datetime_now

tester = None

single_tests = {
    "report": {},
    "contract": {},
    "g_contract": {},
}


def _get_single_tester(test_type, test_id):
    type_tests = single_tests[test_type]
    tester = type_tests.get(test_id)
    if tester is None:
        tester = type_tests[test_id] = SingleTester(test_type, test_id)
        tester.start()
    return tester


def get_single_tester_report(report_id):
    return _get_single_tester("report", report_id)


def get_single_tester_contract(contract_id):
    return _get_single_tester("contract", contract_id)


def get_single_tester_g_contract(g_contract_id):
    return _get_single_tester("g_contract", g_contract_id)


def _run_single_tester(test_type, test_id):
    tester = _get_single_tester(test_type, test_id)
    if not tester.is_alive():
        single_tests[test_type][test_id] = None
        _get_single_tester(test_type, test_id)


def run_single_tester_report(report_id):
    _run_single_tester("report", report_id)


def run_single_tester_contract(contract_id):
    _run_single_tester("contract", contract_id)


def run_single_tester_g_contract(g_contract_id):
    _run_single_tester("g_contract", g_contract_id)


def log(messages, message):
    messages.appendleft(
        f"{ct_datetime_now().strftime('%Y-%m-%d %H:%M:%S')} - {message}"
    )


def _run_all(messages, sess):
    log(messages, "Starting to run tests.")
    for report in sess.execute(select(Report).order_by(Report.id)).scalars():
        test_report(messages, sess, report)
        sess.rollback()  # Avoid long-running transaction
    for contract in sess.execute(select(Contract).order_by(Contract.id)).scalars():
        test_contract(messages, sess, contract)
        sess.rollback()  # Avoid long-running transaction
    for g_contract in sess.execute(select(GContract).order_by(GContract.id)).scalars():
        test_g_contract(messages, sess, g_contract)
        sess.rollback()  # Avoid long-running transaction


class SingleTester(threading.Thread):
    def __init__(self, test_type, test_id):
        super().__init__(name="Tester")
        self.messages = collections.deque(maxlen=500)
        self.test_type = test_type
        self.test_id = test_id

    def run(self):
        log(self.messages, "Starting to Test")
        with RSession() as sess:
            try:
                if self.test_type == "report":
                    report = Report.get_by_id(sess, self.test_id)
                    test_report(self.messages, sess, report)
                elif self.test_type == "contract":
                    contract = Contract.get_by_id(sess, self.test_id)
                    test_contract(self.messages, sess, contract)
                elif self.test_type == "g_contract":
                    g_contract = GContract.get_by_id(sess, self.test_id)
                    test_g_contract(self.messages, sess, g_contract)
                else:
                    raise BadRequest(f"Test type {self.test_type} not recognized.")
            except BaseException:
                log(self.messages, traceback.format_exc())
            finally:
                log(self.messages, "Finished running test.")


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

    def run(self):
        while not self.stopped.isSet():
            if self.lock.acquire(False):
                self.global_alert = None
                with RSession() as sess:
                    try:
                        _run_all(self.messages, sess)
                    except BaseException:
                        log(self.messages, traceback.format_exc())
                        self.global_alert = (
                            "There's a problem with the "
                            "<a href='/tester'>Automatic Tester</a>."
                        )
                        sess.rollback()
                    finally:
                        self.lock.release()
                        log(self.messages, "Finished running tests.")

            self.going.wait(60 * 60 * 24)
            self.going.clear()


def test_report(messages, sess, report):
    log(messages, f"Starting to test local report {report.id} {report.name}.")
    code = compile(report.script, "<string>", "exec")
    ns = {"report_id": report.id, "template": report.template}
    exec(code, ns)
    if "test" in ns:
        ns["test"]()


def test_contract(messages, sess, contract):
    log(
        messages,
        f"Starting to test {contract.party.market_role.description} contract "
        f"{contract.id} {contract.name}.",
    )
    code = compile(contract.charge_script, "<string>", "exec")
    ns = {"db_id": contract.id}
    exec(code, ns)
    if "test" in ns:
        ns["test"]()


def test_g_contract(messages, sess, g_contract):
    log(
        messages,
        f"Starting to test gas {'industry' if g_contract.is_industry else 'supplier'} "
        f"contract {g_contract.id} {g_contract.name}.",
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
