from io import StringIO

from chellow.models import (
    Contract,
    MarketRole,
    Participant,
)
from chellow.reports.report_231 import content
from chellow.utils import ct_datetime, to_utc


def test_content(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
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
    market_role_M = MarketRole.insert(sess, "M", "HH Mop")
    participant.insert_party(sess, market_role_M, "Fusion MOP", vf, None, None)
    mop_charge_script = """
from chellow.utils import reduce_bill_hhs

def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]

        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))

    ds.mop_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    mop_contract = Contract.insert_mop(
        sess, "Fusion MOP 2000", participant, mop_charge_script, {}, vf, None, {}
    )

    sess.commit()
    f = StringIO()
    f.close = mocker.Mock()
    mocker.patch("chellow.reports.report_231.open", return_value=f)
    mocker.patch("chellow.reports.report_231.os.rename")
    running_name = "running"
    finished_name = "finished"
    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 5))
    content(running_name, finished_name, start_date, finish_date, mop_contract.id)
    actual = f.getvalue()
    expected = [
        "Import MPAN Core",
        "Export MPAN Core",
        "Start Date",
        "Finish Date",
        "net-gbp",
        "problem",
    ]
    assert actual == ",".join(expected) + "\n"
