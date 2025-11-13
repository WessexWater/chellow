import csv
from io import StringIO

from utils import match_tables

from chellow.models import (
    Comm,
    Contract,
    Cop,
    DtcMeterType,
    EnergisationStatus,
    GspGroup,
    MarketRole,
    MeterPaymentType,
    MeterType,
    Mtc,
    MtcLlfc,
    MtcParticipant,
    Participant,
    Pc,
    Site,
    Source,
    User,
    UserRole,
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_231 import content
from chellow.utils import ct_datetime, to_utc


def test_content_no_supplies(mocker, sess):
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
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    sess.commit()

    f = StringIO()
    f.close = mocker.Mock()
    mocker.patch("chellow.reports.report_231.open_file", return_value=f)
    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 5))
    content(user_id, start_date, finish_date, mop_contract.id)

    f.seek(0)
    sheet = csv.reader(f)
    actual_table = list(sheet)
    expected_table = [
        [
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
        ],
    ]
    match_tables(expected_table, actual_table)


def test_content_one_supply(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
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
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_M, "Fusion MOP", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
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
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
    )

    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    Contract.insert_dno(sess, dno.dno_code, participant, "", {}, vf, None, {})
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", vf, None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", vf, None)
    mtc = Mtc.insert(sess, "845", False, True, vf, None)
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "HH COP5 And Above With Comms",
        False,
        True,
        meter_type,
        meter_payment_type,
        0,
        vf,
        None,
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        vf,
        None,
        gsp_group,
        mop_contract,
        dc_contract,
        "hgjeyhuw",
        dno,
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        dtc_meter_type,
        "22 7867 6232 781",
        "510",
        imp_supplier_contract,
        "7748",
        361,
        None,
        None,
        None,
        None,
        None,
    )

    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    sess.commit()

    f = StringIO()
    f.close = mocker.Mock()
    mocker.patch("chellow.reports.report_231.open_file", return_value=f)
    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 5))
    content(user_id, start_date, finish_date, mop_contract.id)

    f.seek(0)
    sheet = csv.reader(f)
    actual_table = list(sheet)
    expected_table = [
        [
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
        ],
        [
            "22 7867 6232 781",
            "",
            "2020-01-01 00:00",
            "2020-01-05 00:00",
            "E",
            "_L",
            "22",
            "2000-01-01 00:00",
            "00",
            "C5",
            "CI017",
            "False",
            "510",
            "PC 5-8 & HH HV",
            "",
            "",
            "",
            "0",
            "",
        ],
    ]
    match_tables(expected_table, actual_table)
