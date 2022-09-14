from io import StringIO

from chellow.models import (
    Contract,
    MarketRole,
    Participant,
)
from chellow.reports.report_81 import content
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
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    dc_charge_script = """
from chellow.utils import reduce_bill_hhs

def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]

        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))

    ds.dc_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, dc_charge_script, {}, vf, None, {}
    )

    sess.commit()
    f = StringIO()
    f.close = mocker.Mock()
    mocker.patch("chellow.reports.report_81.open", return_value=f)
    mocker.patch("chellow.reports.report_81.os.rename")
    running_name = "running"
    finished_name = "finished"
    end_year = 2020
    end_month = 1
    months = 1
    content(running_name, finished_name, dc_contract.id, end_year, end_month, months)
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
