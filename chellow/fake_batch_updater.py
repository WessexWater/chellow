import atexit
import collections
import threading
import traceback
from datetime import timedelta

from sqlalchemy import false, null, select

from werkzeug.exceptions import BadRequest

from chellow.e.computer import contract_func
from chellow.gas.engine import g_contract_func
from chellow.models import (
    Batch,
    BillType,
    Contract,
    GBatch,
    GBill,
    GContract,
    GRateScript,
    GReadType,
    GSupply,
    GUnit,
    RateScript,
    ReadType,
    Session,
    Supply,
    Tpr,
)
from chellow.utils import (
    c_months_u,
    ct_datetime_now,
    hh_format,
    keydefaultdict,
    utc_datetime_now,
)


importer = None


def run_import(sess, log, set_progress):
    log("Starting to update the fake batches")
    caches = {}

    now_ct = ct_datetime_now()
    (last_month_start, last_month_finish), (
        current_month_start,
        current_month_finish,
    ) = list(c_months_u(finish_year=now_ct.year, finish_month=now_ct.month, months=2))

    for last_rate_script in sess.scalars(
        select(RateScript)
        .join(Contract, RateScript.contract_id == Contract.id)
        .where(RateScript.finish_date == null())
    ):
        contract = last_rate_script.contract
        fb_func = contract_func(caches, contract, "make_fake_bills")
        if fb_func is None:
            continue

        fake_batch_name = f"fake_e_batch_{contract.id}"

        fake_batch = sess.scalar_one_or_none(
            select(Batch).where(
                Batch.contract == contract,
                Batch.reference == fake_batch_name,
            )
        )

        if fake_batch is not None and fake_batch.start_date < current_month_start:
            fake_batch.delete(sess)
            sess.flush()
            fake_batch = None

        if fake_batch is None:
            fake_batch = contract.insert_batch(sess, fake_batch_name, "Fake Batch")
            bill_types = keydefaultdict(lambda k: BillType.get_by_code(sess, k))

            tprs = keydefaultdict(
                lambda k: None if k is None else Tpr.get_by_code(sess, k)
            )

            read_types = keydefaultdict(lambda k: ReadType.get_by_code(sess, k))
            for raw_bill in fb_func(
                sess,
                log,
                last_month_start,
                last_month_finish,
                current_month_start,
                current_month_finish,
            ):
                mpan_core = raw_bill["mpan_core"]
                supply = Supply.get_by_mpan_core(sess, mpan_core)
                bill = fake_batch.insert_bill(
                    sess,
                    raw_bill["account"],
                    raw_bill["reference"],
                    raw_bill["issue_date"],
                    raw_bill["start_date"],
                    raw_bill["finish_date"],
                    raw_bill["kwh"],
                    raw_bill["net"],
                    raw_bill["vat"],
                    raw_bill["gross"],
                    bill_types[raw_bill["bill_type_code"]],
                    raw_bill["breakdown"],
                    supply,
                )
                for raw_read in raw_bill["reads"]:
                    bill.insert_read(
                        sess,
                        tprs[raw_read["tpr_code"]],
                        raw_read["coefficient"],
                        raw_read["units"],
                        raw_read["msn"],
                        raw_read["mpan"],
                        raw_read["prev_date"],
                        raw_read["prev_value"],
                        read_types[raw_read["prev_type_code"]],
                        raw_read["pres_date"],
                        raw_read["pres_value"],
                        read_types[raw_read["pres_type_code"]],
                    )
    for last_rate_script in sess.scalars(
        select(GRateScript)
        .join(GContract, GRateScript.g_contract_id == GContract.id)
        .where(GContract.is_industry == false(), GRateScript.finish_date == null())
    ):
        g_contract = last_rate_script.g_contract
        log(f"Looking at gas contract {g_contract.name}")
        fb_func = g_contract_func(caches, g_contract, "make_fake_bills")
        if fb_func is None:
            log("Doesn't have a make_fake_bills function so skipping")
            continue

        fake_batch_name = f"fake_g_batch_{g_contract.id}"

        fake_batch = sess.scalars(
            select(GBatch).where(
                GBatch.g_contract == g_contract,
                GBatch.reference == fake_batch_name,
            )
        ).one_or_none()

        if fake_batch is not None:
            log("Found existing fake batch")
            first_fake_bill = sess.scalars(
                select(GBill)
                .where(GBill.g_batch == fake_batch)
                .order_by(GBill.start_date)
            ).first()
            if (
                first_fake_bill is None
                or first_fake_bill.start_date < current_month_start
            ):
                fake_batch.delete(sess)
                sess.flush()
                fake_batch = None

        if fake_batch is None:
            log("Adding a new fake batch")
            fake_batch = g_contract.insert_g_batch(sess, fake_batch_name, "Fake Batch")
            raw_bills = fb_func(
                sess,
                log,
                last_month_start,
                last_month_finish,
                current_month_start,
                current_month_finish,
            )
            if raw_bills is not None and len(raw_bills) > 0:
                log("About to insert raw bills")
                for raw_bill in raw_bills:
                    bill_type = BillType.get_by_code(sess, raw_bill["bill_type_code"])
                    g_supply = GSupply.get_by_mprn(sess, raw_bill["mprn"])
                    g_bill = fake_batch.insert_g_bill(
                        sess,
                        g_supply,
                        bill_type,
                        raw_bill["reference"],
                        raw_bill["account"],
                        raw_bill["issue_date"],
                        raw_bill["start_date"],
                        raw_bill["finish_date"],
                        raw_bill["kwh"],
                        raw_bill["net_gbp"],
                        raw_bill["vat_gbp"],
                        raw_bill["gross_gbp"],
                        raw_bill["raw_lines"],
                        raw_bill["breakdown"],
                    )
                    sess.flush()
                    for raw_read in raw_bill["reads"]:
                        prev_type = GReadType.get_by_code(
                            sess, raw_read["prev_type_code"]
                        )
                        pres_type = GReadType.get_by_code(
                            sess, raw_read["pres_type_code"]
                        )
                        g_unit = GUnit.get_by_code(sess, raw_read["unit"])
                        g_bill.insert_g_read(
                            sess,
                            raw_read["msn"],
                            g_unit,
                            raw_read["correction_factor"],
                            raw_read["calorific_value"],
                            raw_read["prev_value"],
                            raw_read["prev_date"],
                            prev_type,
                            raw_read["pres_value"],
                            raw_read["pres_date"],
                            pres_type,
                        )
                    sess.commit()
            sess.commit()


LAST_RUN_KEY = "fake_batch_updater_last_run"


class FakeBatchUpdater(threading.Thread):
    def __init__(self):
        super().__init__(name="Fake Batch Updater")
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
                        "There's a problem with a <a href='/fake_batch_updater'>"
                        "Fake Batch Updater</a>."
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
                            "<a href='/fake_batch_updater'>Fake Batch Updater</a>."
                        )
                        sess.rollback()
                    finally:
                        self.going.clear()
                        self.log("Finished updating fake batches.")

            else:
                self.log(
                    f"The updater was last run at {hh_format(last_run)}. There will "
                    f"be another update when a hour has elapsed since the last run."
                )
                self.going.wait(60 * 60)


def get_importer():
    return importer


def startup():
    global importer
    importer = FakeBatchUpdater()
    importer.start()


@atexit.register
def shutdown():
    if importer is not None:
        importer.stop()
