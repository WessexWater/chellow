from datetime import datetime as Datetime
from decimal import Decimal
from io import BytesIO

import odio

from sqlalchemy import select

from utils import match, match_tables

from chellow.models import (
    BillType,
    Comm,
    Contract,
    Cop,
    DtcMeterType,
    EnergisationStatus,
    GeneratorType,
    GspGroup,
    MarketRole,
    MeterPaymentType,
    MeterType,
    Mtc,
    MtcLlfc,
    MtcParticipant,
    Participant,
    Pc,
    Scenario,
    Site,
    Source,
    User,
    UserRole,
    VoltageLevel,
    insert_bill_types,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_generator_types,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_59 import content
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_do_post_scenario(mocker, sess, client):
    scenario_props = {
        "scenario_start_year": 2022,
        "scenario_start_month": 8,
        "scenario_start_day": 6,
        "scenario_start_hour": 0,
        "scenario_start_minute": 0,
        "scenario_finish_year": 2022,
        "scenario_finish_month": 8,
        "scenario_finish_day": 6,
        "scenario_finish_hour": 23,
        "scenario_finish_minute": 30,
        "mpan_cores": None,
        "site_codes": ["CI017"],
    }
    scenario = Scenario.insert(sess, "test", scenario_props)

    mock_Thread = mocker.patch("chellow.reports.report_59.threading.Thread")

    now = utc_datetime(2020, 1, 1)
    mocker.patch("chellow.reports.report_59.utc_datetime_now", return_value=now)

    compression = False
    data = {
        "scenario_id": scenario.id,
        "site_codes": "",
        "compression": compression,
    }

    sess.commit()
    response = client.post("/reports/59", data=data)

    match(response, 303)

    base_name = ["duration", "test"]

    user = User.get_by_email_address(sess, "admin@example.com")
    is_bill_check = False
    args = (
        scenario_props,
        base_name,
        user.id,
        compression,
        now,
        is_bill_check,
    )

    mock_Thread.assert_called_with(target=content, args=args)


def test_do_post(mocker, sess, client):
    site_code = "CI017"
    Site.insert(sess, site_code, "Water Works")
    sess.commit()

    mock_Thread = mocker.patch("chellow.reports.report_59.threading.Thread")

    now = utc_datetime(2020, 1, 1)
    mocker.patch("chellow.reports.report_59.utc_datetime_now", return_value=now)

    compression = False
    start_year = 2022
    start_month = 8
    start_day = 6
    start_hour = 0
    start_minute = 0
    finish_year = 2022
    finish_month = 8
    finish_day = 6
    finish_hour = 23
    finish_minute = 30
    data = {
        "site_codes": site_code,
        "compression": compression,
        "start_year": start_year,
        "start_month": start_month,
        "start_day": start_day,
        "start_hour": start_hour,
        "start_minute": start_minute,
        "finish_year": finish_year,
        "finish_month": finish_month,
        "finish_day": finish_day,
        "finish_hour": finish_hour,
        "finish_minute": finish_minute,
    }

    response = client.post("/reports/59", data=data)

    match(response, 303)

    base_name = ["duration", "2022-08-06_00_00"]

    scenario_props = {
        "scenario_start_year": start_year,
        "scenario_start_month": start_month,
        "scenario_start_day": start_day,
        "scenario_start_hour": start_hour,
        "scenario_start_minute": start_minute,
        "scenario_finish_year": finish_year,
        "scenario_finish_month": finish_month,
        "scenario_finish_day": finish_day,
        "scenario_finish_hour": finish_hour,
        "scenario_finish_minute": finish_minute,
        "site_codes": [site_code],
    }
    user = User.get_by_email_address(sess, "admin@example.com")
    is_bill_check = False
    args = (
        scenario_props,
        base_name,
        user.id,
        compression,
        now,
        is_bill_check,
    )

    mock_Thread.assert_called_with(target=content, args=args)


def test_displaced_over_two_months(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
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
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)

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
        sess,
        "Fusion Mop Contract",
        participant,
        mop_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )

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
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill_titles():
    return [
        'ccl-kwh', 'ccl-rate', 'ccl-gbp', 'net-gbp', 'vat-gbp', 'gross-gbp',
        'sum-msp-kwh', 'sum-msp-gbp', 'problem']

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

def displaced_virtual_bill(ds):
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]
        bill_hh['sum-msp-kwh'] = hh['msp-kwh']
        bill_hh['sum-msp-gbp'] = hh['msp-kwh'] * 0.1
        bill_hh['standing-gbp'] = 0.01
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
    Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
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
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        vf,
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source_grid = Source.get_by_code(sess, "grid")
    source_gen = Source.get_by_code(sess, "gen")
    insert_generator_types(sess)
    generator_type_pv = GeneratorType.get_by_code(sess, "pv")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source_grid,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
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
    site.insert_e_supply(
        sess,
        source_gen,
        generator_type_pv,
        "Bob",
        utc_datetime(2000, 1, 1),
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
        "22 7867 5232 780",
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

    scenario_props = {
        "scenario_start_year": 2009,
        "scenario_start_month": 1,
        "scenario_start_day": 1,
        "scenario_start_hour": 0,
        "scenario_start_minute": 0,
        "scenario_finish_year": 2009,
        "scenario_finish_month": 2,
        "scenario_finish_day": 10,
        "scenario_finish_hour": 23,
        "scenario_finish_minute": 30,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_59.open_file", return_value=mock_file)

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    site_table = list(sheet.tables[0].rows)

    site_expected = [
        [
            "creation-date",
            "site-code",
            "site-name",
            "associated-site-codes",
            "start-date",
            "finish-date",
            "metering-type",
            "sources",
            "generator-types",
            "md-used-kw",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            None,
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            "hh",
            "gen | grid",
            "pv",
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            19.67999999999967,
            19.67999999999967,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
    ]
    assert site_expected == site_table

    supply_table = list(sheet.tables[1].rows)
    supply_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "source",
            "generator-type",
            "supply-name",
            "imp-md-kw",
            "imp-md-kva",
            "exp-md-kw",
            "exp-md-kva",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2009, 2, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            "displaced",
            None,
            "CI017",
            "Water Works",
            None,
            "displaced",
            None,
            "displaced",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            "grid",
            None,
            "Bob",
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            "22 7867 5232 780",
            None,
            "CI017",
            "Water Works",
            None,
            "gen",
            "pv",
            "Bob",
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    ]
    match_tables(supply_expected, supply_table)

    era_table = list(sheet.tables[2].rows)
    era_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "era-start-date",
            "era-finish-date",
            "imp-supplier-contract",
            "imp-non-actual-hhs",
            "imp-non-actual-kwh",
            "exp-supplier-contract",
            "exp-non-actual-hhs",
            "exp-non-actual-kwh",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
            None,
            "mop-net-gbp",
            "mop-problem",
            None,
            "dc-net-gbp",
            "dc-problem",
            None,
            "imp-supplier-ccl-kwh",
            "imp-supplier-ccl-rate",
            "imp-supplier-ccl-gbp",
            "imp-supplier-net-gbp",
            "imp-supplier-vat-gbp",
            "imp-supplier-gross-gbp",
            "imp-supplier-sum-msp-kwh",
            "imp-supplier-sum-msp-gbp",
            "imp-supplier-problem",
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            Datetime(2000, 1, 1, 0, 0),
            None,
            "Fusion Supplier 2000",
            1968.0,
            0.0,
            None,
            None,
            None,
            "hh",
            "grid",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            None,
            None,
            0.0,
            None,
            None,
            None,
            None,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            "22 7867 5232 780",
            None,
            "CI017",
            "Water Works",
            None,
            Datetime(2000, 1, 1, 0, 0),
            None,
            "Fusion Supplier 2000",
            1968.0,
            0.0,
            None,
            None,
            None,
            "hh",
            "gen",
            "pv",
            "Bob",
            "hgjeyhuw",
            "00",
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            None,
            None,
            0.0,
            None,
            None,
            None,
            None,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 1, 31, 23, 30),
            None,
            None,
            "CI017",
            "Water Works",
            None,
            None,
            None,
            "Fusion Supplier 2000",
            None,
            None,
            None,
            None,
            None,
            "hh",
            "displaced",
            None,
            None,
            None,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            14.879999999999727,
            14.879999999999727,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2009, 2, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            None,
            None,
            "CI017",
            "Water Works",
            None,
            None,
            None,
            "Fusion Supplier 2000",
            None,
            None,
            None,
            None,
            None,
            "hh",
            "displaced",
            None,
            None,
            None,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            4.799999999999942,
            4.799999999999942,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    ]
    match_tables(era_expected, era_table)


def test_associated_site_codes(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    associated_site = Site.insert(sess, "J77y", "Sewage Works")

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
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)

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
        sess,
        "Fusion Mop Contract",
        participant,
        mop_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )

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
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill_titles():
    return [
        'ccl-kwh', 'ccl-rate', 'ccl-gbp', 'net-gbp', 'vat-gbp', 'gross-gbp',
        'sum-msp-kwh', 'sum-msp-gbp', 'problem']

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
    Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
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
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        vf,
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source_grid = Source.get_by_code(sess, "grid")
    insert_generator_types(sess)
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source_grid,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
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
    era = supply.eras[0]
    era.attach_site(sess, associated_site)

    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id

    sess.commit()

    scenario_props = {
        "scenario_start_year": 2009,
        "scenario_start_month": 1,
        "scenario_start_day": 1,
        "scenario_start_hour": 0,
        "scenario_start_minute": 0,
        "scenario_finish_year": 2009,
        "scenario_finish_month": 2,
        "scenario_finish_day": 10,
        "scenario_finish_hour": 23,
        "scenario_finish_minute": 30,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_59.open_file", return_value=mock_file)

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    site_table = list(sheet.tables[0].rows)

    site_expected = [
        [
            "creation-date",
            "site-code",
            "site-name",
            "associated-site-codes",
            "start-date",
            "finish-date",
            "metering-type",
            "sources",
            "generator-types",
            "md-used-kw",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            "J77y",
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            "hh",
            "grid",
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "J77y",
            "Sewage Works",
            "CI017",
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            None,
            None,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
    ]
    match_tables(site_expected, site_table)

    supply_table = list(sheet.tables[1].rows)
    supply_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "source",
            "generator-type",
            "supply-name",
            "imp-md-kw",
            "imp-md-kva",
            "exp-md-kw",
            "exp-md-kva",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            "J77y",
            "grid",
            None,
            "Bob",
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    ]
    match_tables(supply_expected, supply_table)

    era_table = list(sheet.tables[2].rows)

    era_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "era-start-date",
            "era-finish-date",
            "imp-supplier-contract",
            "imp-non-actual-hhs",
            "imp-non-actual-kwh",
            "exp-supplier-contract",
            "exp-non-actual-hhs",
            "exp-non-actual-kwh",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
            None,
            "mop-net-gbp",
            "mop-problem",
            None,
            "dc-net-gbp",
            "dc-problem",
            None,
            "imp-supplier-ccl-kwh",
            "imp-supplier-ccl-rate",
            "imp-supplier-ccl-gbp",
            "imp-supplier-net-gbp",
            "imp-supplier-vat-gbp",
            "imp-supplier-gross-gbp",
            "imp-supplier-sum-msp-kwh",
            "imp-supplier-sum-msp-gbp",
            "imp-supplier-problem",
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2009, 1, 1, 0, 0),
            Datetime(2009, 2, 10, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            "J77y",
            Datetime(2000, 1, 1, 0, 0),
            None,
            "Fusion Supplier 2000",
            1968.0,
            0.0,
            None,
            None,
            None,
            "hh",
            "grid",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            None,
            None,
            0.0,
            None,
            None,
            None,
            None,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
        ],
    ]

    match_tables(era_expected, era_table)


def test_bills_before_supply(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
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
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)

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
        sess,
        "Fusion Mop Contract",
        participant,
        mop_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )

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
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill_titles():
    return [
        'ccl-kwh', 'ccl-rate', 'ccl-gbp', 'net-gbp', 'vat-gbp', 'gross-gbp',
        'sum-msp-kwh', 'sum-msp-gbp', 'problem']

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
    Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
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
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        vf,
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source_grid = Source.get_by_code(sess, "grid")
    insert_generator_types(sess)
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source_grid,
        None,
        "Bob",
        to_utc(ct_datetime(2000, 1, 15)),
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
    batch = imp_supplier_contract.insert_batch(sess, "a b", "")
    insert_bill_types(sess)
    bill_type = sess.execute(select(BillType).where(BillType.code == "N")).scalar_one()
    batch.insert_bill(
        sess,
        "dd",
        "hjk",
        to_utc(ct_datetime(2000, 1, 1)),
        to_utc(ct_datetime(2000, 1, 1)),
        to_utc(ct_datetime(2000, 1, 5)),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        bill_type,
        {},
        supply,
    )

    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id

    sess.commit()

    scenario_props = {
        "scenario_start_year": 2000,
        "scenario_start_month": 1,
        "scenario_start_day": 1,
        "scenario_start_hour": 0,
        "scenario_start_minute": 0,
        "scenario_finish_year": 2000,
        "scenario_finish_month": 1,
        "scenario_finish_day": 31,
        "scenario_finish_hour": 23,
        "scenario_finish_minute": 30,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_59.open_file", return_value=mock_file)

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    site_table = list(sheet.tables[0].rows)

    site_expected = [
        [
            "creation-date",
            "site-code",
            "site-name",
            "associated-site-codes",
            "start-date",
            "finish-date",
            "metering-type",
            "sources",
            "generator-types",
            "md-used-kw",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            None,
            Datetime(2000, 1, 1, 0, 0),
            Datetime(2000, 1, 31, 23, 30),
            "hh",
            "grid",
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            10.0,
            10.0,
            0.0,
            0.0,
            10.0,
            10.0,
            10.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
    ]
    match_tables(site_expected, site_table)

    supply_table = list(sheet.tables[1].rows)
    supply_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "source",
            "generator-type",
            "supply-name",
            "imp-md-kw",
            "imp-md-kva",
            "exp-md-kw",
            "exp-md-kva",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2000, 1, 15, 0, 0),
            Datetime(2000, 1, 31, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            "grid",
            None,
            "Bob",
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    ]
    match_tables(supply_expected, supply_table)

    era_table = list(sheet.tables[2].rows)

    era_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "era-start-date",
            "era-finish-date",
            "imp-supplier-contract",
            "imp-non-actual-hhs",
            "imp-non-actual-kwh",
            "exp-supplier-contract",
            "exp-non-actual-hhs",
            "exp-non-actual-kwh",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
            None,
            "mop-net-gbp",
            "mop-problem",
            None,
            "dc-net-gbp",
            "dc-problem",
            None,
            "imp-supplier-ccl-kwh",
            "imp-supplier-ccl-rate",
            "imp-supplier-ccl-gbp",
            "imp-supplier-net-gbp",
            "imp-supplier-vat-gbp",
            "imp-supplier-gross-gbp",
            "imp-supplier-sum-msp-kwh",
            "imp-supplier-sum-msp-gbp",
            "imp-supplier-problem",
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2000, 1, 15, 0, 0),
            Datetime(2000, 1, 31, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            Datetime(2000, 1, 15, 0, 0),
            None,
            "Fusion Supplier 2000",
            816.0,
            0.0,
            None,
            None,
            None,
            "hh",
            "grid",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            None,
            None,
            0.0,
            None,
            None,
            None,
            None,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2000, 1, 1, 0, 0),
            Datetime(2000, 1, 31, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            None,
            None,
            "Fusion Supplier 2000",
            None,
            None,
            None,
            None,
            None,
            "hh",
            "grid",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            10.0,
            10.0,
            0.0,
            0.0,
            10.0,
            10.0,
            10.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    ]
    match_tables(era_expected, era_table)


def test_bills_after_supply(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
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
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)

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
        sess,
        "Fusion Mop Contract",
        participant,
        mop_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )

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
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill_titles():
    return [
        'ccl-kwh', 'ccl-rate', 'ccl-gbp', 'net-gbp', 'vat-gbp', 'gross-gbp',
        'sum-msp-kwh', 'sum-msp-gbp', 'problem']

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
    Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
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
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        vf,
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source_grid = Source.get_by_code(sess, "grid")
    insert_generator_types(sess)
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source_grid,
        None,
        "Bob",
        to_utc(ct_datetime(2000, 1, 1)),
        to_utc(ct_datetime(2000, 1, 15)),
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
    batch = imp_supplier_contract.insert_batch(sess, "a b", "")
    insert_bill_types(sess)
    bill_type = sess.execute(select(BillType).where(BillType.code == "N")).scalar_one()
    batch.insert_bill(
        sess,
        "dd",
        "hjk",
        to_utc(ct_datetime(2000, 1, 1)),
        to_utc(ct_datetime(2000, 1, 19)),
        to_utc(ct_datetime(2009, 1, 21)),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        bill_type,
        {},
        supply,
    )

    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id

    sess.commit()

    scenario_props = {
        "scenario_start_year": 2000,
        "scenario_start_month": 1,
        "scenario_start_day": 1,
        "scenario_start_hour": 0,
        "scenario_start_minute": 0,
        "scenario_finish_year": 2000,
        "scenario_finish_month": 1,
        "scenario_finish_day": 31,
        "scenario_finish_hour": 23,
        "scenario_finish_minute": 30,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_59.open_file", return_value=mock_file)

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    site_table = list(sheet.tables[0].rows)

    site_expected = [
        [
            "creation-date",
            "site-code",
            "site-name",
            "associated-site-codes",
            "start-date",
            "finish-date",
            "metering-type",
            "sources",
            "generator-types",
            "md-used-kw",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            None,
            Datetime(2000, 1, 1, 0, 0),
            Datetime(2000, 1, 31, 23, 30),
            "hh",
            "grid",
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.03951342759987589,
            0.03951342759987589,
            0.0,
            0.0,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
    ]
    match_tables(site_expected, site_table)

    supply_table = list(sheet.tables[1].rows)
    supply_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "source",
            "generator-type",
            "supply-name",
            "imp-md-kw",
            "imp-md-kva",
            "exp-md-kw",
            "exp-md-kva",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2000, 1, 1, 0, 0),
            Datetime(2000, 1, 15, 0, 0),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            "grid",
            None,
            "Bob",
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    ]
    match_tables(supply_expected, supply_table)

    era_table = list(sheet.tables[2].rows)

    era_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "era-start-date",
            "era-finish-date",
            "imp-supplier-contract",
            "imp-non-actual-hhs",
            "imp-non-actual-kwh",
            "exp-supplier-contract",
            "exp-non-actual-hhs",
            "exp-non-actual-kwh",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
            None,
            "mop-net-gbp",
            "mop-problem",
            None,
            "dc-net-gbp",
            "dc-problem",
            None,
            "imp-supplier-ccl-kwh",
            "imp-supplier-ccl-rate",
            "imp-supplier-ccl-gbp",
            "imp-supplier-net-gbp",
            "imp-supplier-vat-gbp",
            "imp-supplier-gross-gbp",
            "imp-supplier-sum-msp-kwh",
            "imp-supplier-sum-msp-gbp",
            "imp-supplier-problem",
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2000, 1, 1, 0, 0),
            Datetime(2000, 1, 15, 0, 0),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            Datetime(2000, 1, 1, 0, 0),
            Datetime(2000, 1, 15, 0, 0),
            "Fusion Supplier 2000",
            673.0,
            0.0,
            None,
            None,
            None,
            "hh",
            "grid",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            None,
            None,
            0.0,
            None,
            None,
            None,
            None,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2000, 1, 15, 0, 30),
            Datetime(2000, 1, 31, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            None,
            None,
            "Fusion Supplier 2000",
            None,
            None,
            None,
            None,
            None,
            "hh",
            "grid",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.03951342759987589,
            0.03951342759987589,
            0.0,
            0.0,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    ]
    match_tables(era_expected, era_table)


def test_bills(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
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
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)

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
        sess,
        "Fusion Mop Contract",
        participant,
        mop_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )

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
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill_titles():
    return [
        'ccl-kwh', 'ccl-rate', 'ccl-gbp', 'net-gbp', 'vat-gbp', 'gross-gbp',
        'sum-msp-kwh', 'sum-msp-gbp', 'problem']

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
    Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
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
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        vf,
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source_grid = Source.get_by_code(sess, "grid")
    insert_generator_types(sess)
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source_grid,
        None,
        "Bob",
        to_utc(ct_datetime(2000, 1, 1)),
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
    batch = imp_supplier_contract.insert_batch(sess, "a b", "")
    insert_bill_types(sess)
    bill_type = sess.execute(select(BillType).where(BillType.code == "N")).scalar_one()
    batch.insert_bill(
        sess,
        "dd",
        "hjk",
        to_utc(ct_datetime(2000, 1, 1)),
        to_utc(ct_datetime(2000, 1, 19)),
        to_utc(ct_datetime(2009, 1, 21)),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        bill_type,
        {},
        supply,
    )

    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id

    sess.commit()

    scenario_props = {
        "scenario_start_year": 2000,
        "scenario_start_month": 1,
        "scenario_start_day": 1,
        "scenario_start_hour": 0,
        "scenario_start_minute": 0,
        "scenario_finish_year": 2000,
        "scenario_finish_month": 1,
        "scenario_finish_day": 31,
        "scenario_finish_hour": 23,
        "scenario_finish_minute": 30,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_59.open_file", return_value=mock_file)

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    site_table = list(sheet.tables[0].rows)

    site_expected = [
        [
            "creation-date",
            "site-code",
            "site-name",
            "associated-site-codes",
            "start-date",
            "finish-date",
            "metering-type",
            "sources",
            "generator-types",
            "md-used-kw",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            None,
            Datetime(2000, 1, 1, 0, 0),
            Datetime(2000, 1, 31, 23, 30),
            "hh",
            "grid",
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
        ],
    ]
    match_tables(site_expected, site_table)

    supply_table = list(sheet.tables[1].rows)
    supply_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "source",
            "generator-type",
            "supply-name",
            "imp-md-kw",
            "imp-md-kva",
            "exp-md-kw",
            "exp-md-kva",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2000, 1, 1, 0, 0),
            Datetime(2000, 1, 31, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            "grid",
            None,
            "Bob",
            0.0,
            0.0,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ],
    ]
    match_tables(supply_expected, supply_table)

    era_table = list(sheet.tables[2].rows)

    era_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "era-start-date",
            "era-finish-date",
            "imp-supplier-contract",
            "imp-non-actual-hhs",
            "imp-non-actual-kwh",
            "exp-supplier-contract",
            "exp-non-actual-hhs",
            "exp-non-actual-kwh",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
            None,
            "mop-net-gbp",
            "mop-problem",
            None,
            "dc-net-gbp",
            "dc-problem",
            None,
            "imp-supplier-ccl-kwh",
            "imp-supplier-ccl-rate",
            "imp-supplier-ccl-gbp",
            "imp-supplier-net-gbp",
            "imp-supplier-vat-gbp",
            "imp-supplier-gross-gbp",
            "imp-supplier-sum-msp-kwh",
            "imp-supplier-sum-msp-gbp",
            "imp-supplier-problem",
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            Datetime(2000, 1, 1, 0, 0),
            Datetime(2000, 1, 31, 23, 30),
            "22 7867 6232 781",
            None,
            "CI017",
            "Water Works",
            None,
            Datetime(2000, 1, 1, 0, 0),
            None,
            "Fusion Supplier 2000",
            1488.0,
            0.0,
            None,
            None,
            None,
            "hh",
            "grid",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            0.0,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.03951342759987589,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            0.0,
            None,
            None,
            0.0,
            None,
            None,
            None,
            None,
            None,
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
            None,
        ],
    ]
    match_tables(era_expected, era_table)


def test_base_exception(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
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
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)

    mop_charge_script = """
from chellow.utils import reduce_bill_hhs

def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    raise Exception("MOP Exception")
"""
    mop_contract = Contract.insert_mop(
        sess,
        "Fusion Mop Contract",
        participant,
        mop_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )

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
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill_titles():
    return [
        'ccl-kwh', 'ccl-rate', 'ccl-gbp', 'net-gbp', 'vat-gbp', 'gross-gbp',
        'sum-msp-kwh', 'sum-msp-gbp', 'problem']

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
    Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
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
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        vf,
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source_grid = Source.get_by_code(sess, "grid")
    insert_generator_types(sess)
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source_grid,
        None,
        "Bob",
        to_utc(ct_datetime(2000, 1, 1)),
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

    scenario_props = {
        "scenario_start_year": 2000,
        "scenario_start_month": 1,
        "scenario_start_day": 1,
        "scenario_start_hour": 0,
        "scenario_start_minute": 0,
        "scenario_finish_year": 2000,
        "scenario_finish_month": 1,
        "scenario_finish_day": 31,
        "scenario_finish_hour": 23,
        "scenario_finish_minute": 30,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_59.open_file", return_value=mock_file)

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    site_table = list(sheet.tables[0].rows)

    assert site_table[1][0].startswith("Problem Traceback")

    supply_table = list(sheet.tables[1].rows)
    supply_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "source",
            "generator-type",
            "supply-name",
            "imp-md-kw",
            "imp-md-kva",
            "exp-md-kw",
            "exp-md-kva",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
        ],
    ]
    match_tables(supply_expected, supply_table)

    era_table = list(sheet.tables[2].rows)

    era_expected = [
        [
            "creation-date",
            "start-date",
            "finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "associated-site-codes",
            "era-start-date",
            "era-finish-date",
            "imp-supplier-contract",
            "imp-non-actual-hhs",
            "imp-non-actual-kwh",
            "exp-supplier-contract",
            "exp-non-actual-hhs",
            "exp-non-actual-kwh",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "import-grid-kwh",
            "export-grid-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-grid-net-gbp",
            "export-grid-net-gbp",
            "import-gen-net-gbp",
            "export-gen-net-gbp",
            "import-3rd-party-net-gbp",
            "export-3rd-party-net-gbp",
            "displaced-net-gbp",
            "used-net-gbp",
            "used-3rd-party-net-gbp",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "billed-import-vat-gbp",
            "billed-import-gross-gbp",
            "billed-import-supplier-net-gbp",
            "billed-import-supplier-vat-gbp",
            "billed-import-supplier-gross-gbp",
            "billed-import-dc-net-gbp",
            "billed-import-dc-vat-gbp",
            "billed-import-dc-gross-gbp",
            "billed-import-mop-net-gbp",
            "billed-import-mop-vat-gbp",
            "billed-import-mop-gross-gbp",
            None,
            "mop-net-gbp",
            "mop-problem",
            None,
            "dc-net-gbp",
            "dc-problem",
            None,
            "imp-supplier-ccl-kwh",
            "imp-supplier-ccl-rate",
            "imp-supplier-ccl-gbp",
            "imp-supplier-net-gbp",
            "imp-supplier-vat-gbp",
            "imp-supplier-gross-gbp",
            "imp-supplier-sum-msp-kwh",
            "imp-supplier-sum-msp-gbp",
            "imp-supplier-problem",
            None,
        ],
    ]
    match_tables(era_expected, era_table)
