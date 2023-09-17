from datetime import datetime as Datetime
from decimal import Decimal
from io import BytesIO

import odio

import pytest

from sqlalchemy import select

from utils import match

from zish import loads

from chellow.models import (
    BillType,
    Comm,
    Contract,
    Cop,
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
    insert_energisation_statuses,
    insert_generator_types,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_247 import content
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_with_scenario(mocker, sess, client):
    mock_Thread = mocker.patch("chellow.reports.report_247.threading.Thread")

    properties = """{
      "scenario_start_year": 2009,
      "scenario_start_month": 8,
      "scenario_duration": 1,

      "era_maps": {
        2000-08-01T00:00:00Z: {
          "llfcs": {
            "22": {
              "new_export": "521"
            }
          },
          "supplier_contracts": {
            "new_export": 10
          }
        }
      },

      "hh_data": {
        "CI017": {
          "generated": "
                2009-08-01 00:00, 40
                2009-08-15 00:00, 40"
        }
      }
    }"""
    scenario_props = loads(properties)
    scenario = Scenario.insert(sess, "New Gen", scenario_props)

    site_code = "CI017"
    site = Site.insert(sess, site_code, "Water Works")
    sess.commit()

    now = utc_datetime(2020, 1, 1)
    mocker.patch("chellow.reports.report_247.utc_datetime_now", return_value=now)

    data = {
        "site_id": site.id,
        "scenario_id": scenario.id,
        "compression": False,
    }

    response = client.post("/reports/247", data=data)

    match(response, 303)

    base_name = ["New Gen"]
    user = User.get_by_email_address(sess, "admin@example.com")
    is_bill_check = False
    scenario_props["site_codes"] = [site_code]
    args = (
        scenario_props,
        base_name,
        user.id,
        False,
        now,
        is_bill_check,
    )

    mock_Thread.assert_called_with(target=content, args=args)


def test_do_post_without_scenario(mocker, sess, client):
    mock_Thread = mocker.patch("chellow.reports.report_247.threading.Thread")

    site_code = "CI017"
    Site.insert(sess, site_code, "Water Works")
    sess.commit()

    now = utc_datetime(2020, 1, 1)
    mocker.patch("chellow.reports.report_247.utc_datetime_now", return_value=now)

    data = {
        "compression": False,
        "finish_year": 2009,
        "finish_month": 8,
        "months": 1,
        "site_codes": "",
    }

    response = client.post("/reports/247", data=data)

    match(response, 303)

    base_name = ["monthly_duration"]
    user = User.get_by_email_address(sess, "admin@example.com")
    is_bill_check = False
    scenario_props = {
        "scenario_start_year": 2009,
        "scenario_start_month": 8,
        "scenario_duration": 1,
        "by_hh": False,
    }
    args = (
        scenario_props,
        base_name,
        user.id,
        False,
        now,
        is_bill_check,
    )

    mock_Thread.assert_called_with(target=content, args=args)


def test_do_post_error(mocker, sess, client):
    now = utc_datetime(2020, 1, 1)
    mocker.patch("chellow.reports.report_247.utc_datetime_now", return_value=now)

    data = {
        "compression": False,
        "finish_year": 2009,
        "finish_month": 8,
        "months": 1,
        "site_codes": "x",
    }

    response = client.post("/reports/247", data=data)

    match(response, 400)


def test_without_scenario(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    months = 1

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
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
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
        utc_datetime(2000, 1, 1),
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
    site.insert_e_supply(
        sess,
        source,
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
        {},
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
    site_code = site.code

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
        "site_codes": [site_code],
        "mpan_cores": None,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    table = list(sheet.tables[0].rows)

    expected = [
        [
            "creation-date",
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "metering-type",
            "sources",
            "generator-types",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            "",
            Datetime(2009, 7, 31, 23, 30),
            "hh",
            "net",
            "",
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

    assert expected == table


def test_missing_mop_script(mocker, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    months = 1

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)

    mop_charge_script = ""
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
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.ccl
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
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(sess, "845", False, True, valid_from, None)
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
        utc_datetime(1996, 1, 1),
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
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    site.insert_e_supply(
        sess,
        source,
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
        {},
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
    site_code = site.code
    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
        "site_codes": [site_code],
        "mpan_cores": None,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    table = list(sheet.tables[0].rows)

    expected = (
        "For the contract Fusion Mop Contract there doesn't seem to be a "
        "'virtual_bill_titles' function."
    )

    assert expected in table[0][0]


def test_bill_after_end_supply(mocker, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    months = 1

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)

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
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.ccl
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
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "a b", "")
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
    mtc = Mtc.insert(sess, "845", False, True, valid_from, None)
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
        utc_datetime(1996, 1, 1),
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
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2000, 1, 31, 23, 30),
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
        {},
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
    insert_bill_types(sess)
    bill_type = sess.execute(select(BillType).where(BillType.code == "N")).scalar_one()
    batch.insert_bill(
        sess,
        "dd",
        "hjk",
        start_date,
        utc_datetime(2009, 7, 10),
        utc_datetime(2009, 7, 10),
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
    site_code = site.code

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
        "site_codes": [site_code],
        "mpan_cores": None,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")

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
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "metering-type",
            "sources",
            "generator-types",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            "",
            Datetime(2009, 7, 31, 23, 30),
            None,
            "",
            "",
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
            10.0,
            0.0,
            0.0,
        ],
    ]

    assert site_expected == site_table

    era_table = list(sheet.tables[1].rows)
    era_expected = [
        [
            "creation-date",
            "imp-mpan-core",
            "imp-supplier-contract",
            "exp-mpan-core",
            "exp-supplier-contract",
            "era-start-date",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
            None,
            None,
            None,
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "22 7867 6232 781",
            "Fusion Supplier 2000",
            None,
            None,
            Datetime(2009, 7, 1, 0, 0),
            "hh",
            "net",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            "CI017",
            "Water Works",
            None,
            Datetime(2009, 7, 31, 23, 30),
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
            10.0,
            0.0,
            0.0,
        ],
    ]
    assert era_expected == era_table


def test_bill_after_end_supply_with_supply_id(mocker, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    months = 1

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)

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
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.ccl
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
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "a b", "")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(sess, "845", False, True, valid_from, None)
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
        utc_datetime(1996, 1, 1),
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
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    imp_mpan_core = "22 7867 6232 781"
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2000, 1, 31, 23, 30),
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
        {},
        imp_mpan_core,
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
    insert_bill_types(sess)
    bill_type = sess.execute(select(BillType).where(BillType.code == "N")).scalar_one()
    batch.insert_bill(
        sess,
        "dd",
        "hjk",
        start_date,
        utc_datetime(2009, 7, 10),
        utc_datetime(2009, 7, 10),
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
    site_code = site.code

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
        "site_codes": [site_code],
        "mpan_cores": [imp_mpan_core],
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )
    sheet = odio.parse_spreadsheet(mock_file)
    table = list(sheet.tables[0].rows)

    expected = [
        [
            "creation-date",
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "metering-type",
            "sources",
            "generator-types",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            "",
            Datetime(2009, 7, 31, 23, 30),
            None,
            "",
            "",
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
            10.0,
            0.0,
            0.0,
        ],
    ]

    assert expected == table


def test_supply_attached_to_different_sites(mocker, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site_1 = Site.insert(sess, "CI017", "Water Works 1")
    site_2 = Site.insert(sess, "CI018", "Water Works 2")
    start_date = utc_datetime(2000, 1, 1, 0, 0)
    months = 1

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)

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
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
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
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "a b", "")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    Contract.insert_dno(sess, dno.dno_code, participant, "", {}, valid_from, None, {})
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(sess, "845", False, True, valid_from, None)
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
        utc_datetime(1996, 1, 1),
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
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    supply = site_1.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2000, 1, 31, 23, 30),
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
        {},
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
    era = supply.insert_era_at(sess, utc_datetime(2000, 1, 15))
    era.attach_site(sess, site_2, True)
    insert_bill_types(sess)
    bill_type = sess.execute(select(BillType).where(BillType.code == "N")).scalar_one()
    batch.insert_bill(
        sess,
        "dd",
        "hjk",
        start_date,
        utc_datetime(2000, 1, 1),
        utc_datetime(2000, 1, 31),
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
    site_1_code = site_1.code
    user_id = user.id

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
        "site_codes": [site_1_code],
        "mpan_cores": None,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    table = list(sheet.tables[0].rows)

    expected = [
        [
            "creation-date",
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "metering-type",
            "sources",
            "generator-types",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works 1",
            "CI018",
            Datetime(2000, 1, 31, 23, 30),
            "hh",
            "net",
            "",
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
            4.663428174878557,
            4.663428174878557,
            4.663428174878557,
            0.0,
            0.0,
        ],
    ]

    assert expected == table


def test_supply_end_two_eras_in_month(mocker, sess):
    site = Site.insert(sess, "CI017", "Water Works 1")
    start_date = utc_datetime(2000, 1, 1, 0, 0)
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    months = 1

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )

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
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
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
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "a b", "")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    Contract.insert_dno(sess, dno.dno_code, participant, "", {}, valid_from, None, {})
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(sess, "845", False, True, valid_from, None)
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
        utc_datetime(1996, 1, 1),
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
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2000, 1, 25, 23, 30),
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
        {},
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
    supply.insert_era_at(sess, utc_datetime(2000, 1, 15))
    insert_bill_types(sess)
    bill_type = sess.execute(select(BillType).where(BillType.code == "N")).scalar_one()
    batch.insert_bill(
        sess,
        "dd",
        "hjk",
        start_date,
        utc_datetime(2000, 1, 1),
        utc_datetime(2000, 1, 31),
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
    site_code = site.code

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
        "site_codes": [site_code],
        "mpan_cores": None,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")

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
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "metering-type",
            "sources",
            "generator-types",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works 1",
            "",
            Datetime(2000, 1, 31, 23, 30),
            "hh",
            "net",
            "",
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
            10.0,
            0.0,
            0.0,
        ],
    ]
    assert site_expected == site_table

    era_table = list(sheet.tables[1].rows)
    era_expected = [
        [
            "creation-date",
            "imp-mpan-core",
            "imp-supplier-contract",
            "exp-mpan-core",
            "exp-supplier-contract",
            "era-start-date",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
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
            "22 7867 6232 781",
            "Fusion Supplier 2000",
            None,
            None,
            Datetime(2000, 1, 1, 0, 0),
            "hh",
            "net",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            "CI017",
            "Water Works 1",
            "",
            Datetime(2000, 1, 31, 23, 30),
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
            4.663428174878557,
            4.663428174878557,
            4.663428174878557,
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
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "22 7867 6232 781",
            "Fusion Supplier 2000",
            None,
            None,
            Datetime(2000, 1, 15, 0, 0),
            "hh",
            "net",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            "CI017",
            "Water Works 1",
            "",
            Datetime(2000, 1, 31, 23, 30),
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
            3.66412213740458,
            3.66412213740458,
            3.66412213740458,
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
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "22 7867 6232 781",
            "Fusion Supplier 2000",
            None,
            None,
            Datetime(2000, 1, 26, 0, 0),
            "hh",
            "net",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            "CI017",
            "Water Works 1",
            None,
            Datetime(2000, 1, 31, 23, 30),
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
            1.6724496877168633,
            1.6724496877168633,
            1.6724496877168633,
            0.0,
            0.0,
        ],
    ]
    assert era_expected == era_table


def test_bill_before_begining_supply(mocker, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(1999, 12, 1)
    months = 1

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )

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
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.ccl
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
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "a b", "")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(sess, "845", False, True, valid_from, None)
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
        utc_datetime(1996, 1, 1),
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
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    dno.insert_llfc(
        sess,
        "521",
        "Export (HV)",
        voltage_level,
        False,
        False,
        utc_datetime(1996, 1, 1),
        None,
    )
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2000, 1, 31, 23, 30),
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
        {},
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
    insert_bill_types(sess)
    bill_type = sess.execute(select(BillType).where(BillType.code == "N")).scalar_one()
    batch.insert_bill(
        sess,
        "dd",
        "hjk",
        start_date,
        utc_datetime(1999, 12, 10),
        utc_datetime(1999, 12, 15),
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
    site_code = site.code

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
        "site_codes": [site_code],
        "mpan_cores": None,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")

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
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "metering-type",
            "sources",
            "generator-types",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            "",
            Datetime(1999, 12, 31, 23, 30),
            None,
            "",
            "",
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
            10.0,
            0.0,
            0.0,
        ],
    ]

    assert site_expected == site_table

    era_table = list(sheet.tables[1].rows)
    era_expected = [
        [
            "creation-date",
            "imp-mpan-core",
            "imp-supplier-contract",
            "exp-mpan-core",
            "exp-supplier-contract",
            "era-start-date",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
            None,
            None,
            None,
            None,
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "22 7867 6232 781",
            "Fusion Supplier 2000",
            None,
            None,
            None,
            "hh",
            "net",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            "CI017",
            "Water Works",
            None,
            Datetime(1999, 12, 31, 23, 30),
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
            10.0,
            0.0,
            0.0,
        ],
    ]
    assert era_expected == era_table


def test_bill_before_begining_supply_mid_month(mocker, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2000, 1, 1)
    months = 1

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AB Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion", valid_from, None, None)
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )

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
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
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
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "a b", "")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    Contract.insert_dno(sess, dno.dno_code, participant, "", {}, valid_from, None, {})
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(sess, "845", False, True, valid_from, None)
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
        utc_datetime(1996, 1, 1),
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
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 15),
        utc_datetime(2000, 1, 31, 23, 30),
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
        {},
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
    insert_bill_types(sess)
    bill_type = sess.execute(select(BillType).where(BillType.code == "N")).scalar_one()
    batch.insert_bill(
        sess,
        "dd",
        "hjk",
        start_date,
        utc_datetime(2000, 1, 1),
        utc_datetime(2000, 1, 30),
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
    site_code = site.code

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
        "site_codes": [site_code],
        "mpan_cores": None,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    table = list(sheet.tables[0].rows)

    expected = [
        [
            "creation-date",
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "metering-type",
            "sources",
            "generator-types",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "CI017",
            "Water Works",
            "",
            Datetime(2000, 1, 31, 23, 30),
            "hh",
            "net",
            "",
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
            10,
            10,
            10,
            0.0,
            0.0,
        ],
    ]
    assert expected == table


def test_displaced(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    months = 1

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
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        vf,
        None,
        {},
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
    source_net = Source.get_by_code(sess, "net")
    source_lm = Source.get_by_code(sess, "gen")
    insert_generator_types(sess)
    generator_lm = GeneratorType.get_by_code(sess, "lm")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    site.insert_e_supply(
        sess,
        source_net,
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
        {},
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
        source_lm,
        generator_lm,
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
        {},
        "22 7864 6232 780",
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
    site_code = site.code

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
        "site_codes": [site_code],
        "mpan_cores": None,
    }
    base_name = ["monthly_duration"]
    compression = False
    now = utc_datetime(2020, 1, 1)
    is_bill_check = False

    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")

    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    era_table = list(sheet.tables[1].rows)

    era_expected = [
        [
            "creation-date",
            "imp-mpan-core",
            "imp-supplier-contract",
            "exp-mpan-core",
            "exp-supplier-contract",
            "era-start-date",
            "metering-type",
            "source",
            "generator-type",
            "supply-name",
            "msn",
            "pc",
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
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
            "22 7867 6232 781",
            "Fusion Supplier 2000",
            None,
            None,
            Datetime(2000, 1, 1, 0, 0),
            "hh",
            "net",
            None,
            "Bob",
            "hgjeyhuw",
            "00",
            "CI017",
            "Water Works",
            "",
            Datetime(2009, 7, 31, 23, 30),
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
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            "22 7864 6232 780",
            "Fusion Supplier 2000",
            None,
            None,
            Datetime(2000, 1, 1, 0, 0),
            "hh",
            "gen",
            "lm",
            "Bob",
            "hgjeyhuw",
            "00",
            "CI017",
            "Water Works",
            "",
            Datetime(2009, 7, 31, 23, 30),
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
        ],
        [
            Datetime(2020, 1, 1, 0, 0),
            None,
            "Fusion Supplier 2000",
            None,
            None,
            None,
            "hh",
            "displaced",
            None,
            None,
            None,
            None,
            "CI017",
            "Water Works",
            "",
            Datetime(2009, 7, 31, 23, 30),
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
            0.0,
            0.0,
            0.0,
            0.0,
            0.0,
            None,
        ],
    ]
    assert era_expected == era_table


def test_content_error():
    scenario_props = {}
    base_name = []
    user_id = 0
    compression = False
    now = to_utc(ct_datetime(2020, 1, 1))
    is_bill_check = False
    with pytest.raises(
        TypeError,
        match="expected str, bytes or os.PathLike object, not NoneType",
    ):
        content(
            scenario_props,
            base_name,
            user_id,
            compression,
            now,
            is_bill_check,
        )


def test_content_no_mpan_cores(mocker, sess, client):
    mock_file = BytesIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_247.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_247.chellow.dloads.make_names", return_value=("a", "b")
    )
    mocker.patch("chellow.reports.report_247.os.rename")
    scenario_props = {
        "scenario_start_year": 2022,
        "scenario_start_month": 9,
        "scenario_duration": 1,
    }
    base_name = ["no_mpan_cores"]
    user = User.get_by_email_address(sess, "admin@example.com")
    user_id = user.id
    sess.commit()
    compression = False
    now = to_utc(ct_datetime(2020, 1, 1))
    is_bill_check = False
    content(
        scenario_props,
        base_name,
        user_id,
        compression,
        now,
        is_bill_check,
    )
    sheet = odio.parse_spreadsheet(mock_file)
    table = list(sheet.tables[0].rows)

    expected = [
        [
            "creation-date",
            "site-id",
            "site-name",
            "associated-site-ids",
            "month",
            "metering-type",
            "sources",
            "generator-types",
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
        ],
    ]

    assert expected == table
