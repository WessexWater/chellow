from decimal import Decimal

from chellow.fake_batch_updater import run_import
from chellow.models import Contract, GContract, MarketRole, Participant
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_run_import_existing_batch_in_current_month(mocker, sess):
    vf = to_utc(ct_datetime(1996, 4, 1))
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    Contract.insert_non_core(sess, "configuration", "", {}, vf, None, {})
    g_cv_rate_script = {
        "cvs": {
            "EA": {
                1: {"applicable_at": utc_datetime(2020, 10, 3), "cv": 39.2000},
            }
        }
    }
    GContract.insert_industry(sess, "cv", "", {}, vf, None, g_cv_rate_script)
    ug_rate_script = {
        "ug_gbp_per_kwh": {"EA1": Decimal("40.1")},
    }
    GContract.insert_industry(sess, "ug", "", {}, vf, None, ug_rate_script)
    ccl_rate_script = {"ccl_gbp_per_kwh": Decimal("0.00339")}
    GContract.insert_industry(sess, "ccl", "", {}, vf, None, ccl_rate_script)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        vf,
        None,
        bank_holiday_rate_script,
    )
    charge_script = """
import chellow.gas.ccl
from chellow.gas.engine import g_rates
from chellow.utils import reduce_bill_hhs


def make_fake_bills(
        sess, log, last_month_start, last_month_finish, current_month_start,
        current_months_finish
):
    pass
"""
    g_contract_rate_script = {
        "gas_rate": 0.1,
        "standing_rate": 0.1,
    }
    g_contract = GContract.insert(
        sess,
        False,
        "Fusion 2020",
        charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        g_contract_rate_script,
    )
    g_contract.insert_g_batch(sess, f"fake_g_batch_{g_contract.id}", "Fake Batch")
    sess.commit()
    messages = []

    def log(message):
        messages.append(message)

    def set_progress(progress):
        pass

    run_import(sess, log, set_progress)
