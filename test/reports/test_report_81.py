from io import StringIO

from chellow.models import Contract, MarketRole, Participant, User, UserRole
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
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    dc_contract_id = dc_contract.id

    sess.commit()
    f = StringIO()
    f.close = mocker.Mock()
    mocker.patch("chellow.reports.report_81.open_file", return_value=f)
    end_year = 2020
    end_month = 1
    months = 1
    content(user_id, dc_contract_id, end_year, end_month, months)
    actual = f.getvalue()
    expected = [
        "imp_mpan_core",
        "exp_mpan_core",
        "start_date",
        "finish_date",
        "energisation_status",
        "gsp_group",
        "dno",
        "era_start",
        "pc",
        "meter_type",
        "site_code",
        "imp_is_substation",
        "imp_llfc_code",
        "imp_llfc_description",
        "exp_is_substation",
        "exp_llfc_code",
        "exp_llfc_description",
        "net-gbp",
        "problem",
    ]
    assert actual == ",".join(expected) + "\n"
