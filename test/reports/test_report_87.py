import csv
from io import StringIO

from utils import match_tables

import chellow.e.computer
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
from chellow.reports.report_87 import content
from chellow.utils import ct_datetime, to_utc


class Sess:
    def __init__(self, *results):
        self.it = iter(results)

    def query(self, *arg):
        return self

    def join(self, *arg):
        return self

    def order_by(self, *arg):
        return self

    def filter(self, *arg):
        return self

    def scalar(self, *arg):
        return next(self.it)

    def first(self, *arg):
        return next(self.it)

    def distinct(self, *arg):
        return next(self.it)


def test_summertime(mocker):
    start_date_ct = ct_datetime(2010, 5)
    finish_date_ct = ct_datetime(2010, 5, 31, 23, 30)
    start_date = to_utc(start_date_ct)
    finish_date = to_utc(finish_date_ct)
    contract_id = 1
    user = mocker.Mock()
    user.email_address = "sfreud"

    mock_c_months_u = mocker.patch(
        "chellow.reports.report_87.c_months_u", autospec=True
    )

    MockEra = mocker.patch("chellow.reports.report_87.Era", autospec=True)
    MockEra.finish_date = finish_date
    MockEra.start_date = start_date

    mocker.patch(
        "chellow.reports.report_87.contract_func",
        autospec=True,
        return_value=lambda: ["standing_gbp"],
    )

    f = StringIO()
    sess = Sess([], [])

    chellow.reports.report_87.create_csv(f, sess, start_date, finish_date, contract_id)

    mock_c_months_u.assert_called_with(
        start_year=start_date_ct.year,
        start_month=start_date_ct.month,
        finish_year=finish_date_ct.year,
        finish_month=finish_date_ct.month,
    )


def test_content_no_supplies(mocker, sess):
    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_87.open_file", return_value=mock_file)
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    vf = to_utc(ct_datetime(1996, 1, 1))
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)

    contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
    )
    sess.commit()

    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 31, 23, 30))

    content(start_date, finish_date, contract.id, user_id)


def test_content_one_supply(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)

    mop_contract = Contract.insert_mop(
        sess, "Fusion Mop Contract", participant, "", {}, vf, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
from chellow.utils import reduce_bill_hhs

def virtual_bill_titles():
    return [
        'net-gbp', 'vat-gbp', 'gross-gbp', 'sum-msp-kwh', 'sum-msp-gbp', 'problem'
    ]

def virtual_bill(ds):
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]
        bill_hh['sum-msp-kwh'] = hh['msp-kwh']
        bill_hh['sum-msp-gbp'] = hh['msp-kwh'] * 0.1
        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat-gbp'] = 0
        bill_hh['gross-gbp'] = bill_hh['net-gbp'] + bill_hh['vat-gbp']

    ds.supplier_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        supplier_charge_script,
        {},
        vf,
        None,
        {},
    )
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
    source = Source.get_by_code(sess, "net")
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
        "773",
        dc_contract,
        "ghyy3",
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

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_87.open_file", return_value=mock_file)

    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 31, 23, 30))

    content(start_date, finish_date, imp_supplier_contract.id, user_id)

    mock_file.seek(0)
    sheet = csv.reader(mock_file)
    actual_table = list(sheet)
    print(actual_table)

    expected_table = [
        [
            "mpan_core",
            "site_code",
            "site_name",
            "account",
            "from",
            "to",
            "energisation_status",
            "gsp_group",
            "dno",
            "era_start",
            "pc",
            "meter_type",
            "imp_is_substation",
            "imp_llfc_code",
            "imp_llfc_description",
            "exp_is_substation",
            "exp_llfc_code",
            "exp_llfc_description",
            "net-gbp",
            "vat-gbp",
            "gross-gbp",
            "sum-msp-kwh",
            "sum-msp-gbp",
            "problem",
        ],
        [
            "22 7867 6232 781",
            "CI017",
            "Water Works",
            "7748",
            "2020-01-01 00:00",
            "2020-01-31 23:30",
            "E",
            "_L",
            "22",
            "1996-01-01 00:00",
            "00",
            "C5",
            "False",
            "510",
            "PC 5-8 & HH HV",
            "",
            "",
            "",
            "0.0",
            "0",
            "0.0",
            "0",
            "0.0",
            "",
        ],
    ]
    match_tables(expected_table, actual_table)
