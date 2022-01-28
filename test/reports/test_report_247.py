from datetime import datetime as Datetime
from decimal import Decimal
from io import BytesIO

import odio

from sqlalchemy import select

from utils import match

from zish import loads

from chellow.models import (
    BillType,
    Comm,
    Contract,
    Cop,
    EnergisationStatus,
    GspGroup,
    MarketRole,
    MeterPaymentType,
    MeterType,
    OldMtc,
    Participant,
    Pc,
    Scenario,
    Site,
    Source,
    VoltageLevel,
    insert_bill_types,
    insert_comms,
    insert_cops,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_247 import _make_calcs, _make_site_deltas, content
from chellow.utils import utc_datetime


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
    sess.commit()

    now = utc_datetime(2020, 1, 1)
    mocker.patch("chellow.reports.report_247.utc_datetime_now", return_value=now)

    site_code = "CI017"
    site = Site.insert(sess, site_code, "Water Works")

    data = {
        "site_id": site.id,
        "scenario_id": scenario.id,
        "compression": False,
    }

    response = client.post("/reports/247", data=data)

    match(response, 303)

    base_name = ["New Gen"]
    args = scenario_props, base_name, site.id, None, None, False, [], now

    mock_Thread.assert_called_with(target=content, args=args)


def test_make_site_deltas(mocker):
    era_1 = mocker.Mock()
    era_1.start_date = utc_datetime(2018, 1, 1)
    era_1.finish_date = None
    filter_returns = iter([[era_1], []])

    class Sess:
        def query(self, *args):
            return self

        def join(self, *args):
            return self

        def filter(self, *args):
            return next(filter_returns)

    sess = Sess()
    report_context = {}
    site = mocker.Mock()
    site.code = "1"
    scenario_hh = {site.code: {"used": "2019-03-01 00:00, 0"}}
    forecast_from = utc_datetime(2019, 4, 1)
    supply_id = None

    ss = mocker.patch("chellow.computer.SiteSource", autospec=True)
    ss_instance = ss.return_value
    ss_instance.hh_data = [
        {
            "start-date": utc_datetime(2019, 3, 1),
            "used-kwh": 0,
            "export-net-kwh": 0,
            "import-net-kwh": 0,
            "msp-kwh": 0,
        }
    ]

    se = mocker.patch("chellow.reports.report_247.SiteEra", autospec=True)
    se.site = mocker.Mock()

    sup_s = mocker.patch("chellow.reports.report_247.SupplySource", autospec=True)
    sup_s_instance = sup_s.return_value
    sup_s_instance.hh_data = {}

    res = _make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id
    )

    assert len(res["supply_deltas"][False]["net"]["site"]) == 0


def test_make_site_deltas_nhh(mocker):
    era_1 = mocker.Mock()
    era_1.start_date = utc_datetime(2018, 1, 1)
    era_1.finish_date = None
    """
    filter_args = iter(
        [
            [
                'False',
                'era.finish_date IS NULL OR era.finish_date >= :finish_date_1',
                'era.imp_mpan_core IS NOT NULL',
                'era.start_date <= :start_date_1', 'pc.code != :code_1',
                'true = :param_1'
            ],
            [
                'False',
                'era.finish_date IS NULL OR era.finish_date >= :finish_date_1',
                'era.imp_mpan_core IS NOT NULL',
                'era.start_date <= :start_date_1', 'source.code = :code_1',
                'true = :param_1'
            ]
        ]
    )
    """

    filter_returns = iter([[era_1], []])

    class Sess:
        def query(self, *args):
            return self

        def join(self, *args):
            return self

        def filter(self, *args):
            """
            actual_args = sorted(map(str, args))
            expected_args = next(filter_args)
            assert actual_args == expected_args
            """
            return next(filter_returns)

    sess = Sess()
    report_context = {}
    site = mocker.Mock()
    site.code = "1"
    scenario_hh = {site.code: {"used": "2019-03-01 00:00, 0"}}
    forecast_from = utc_datetime(2019, 4, 1)
    supply_id = None

    ss = mocker.patch("chellow.computer.SiteSource", autospec=True)
    ss_instance = ss.return_value
    ss_instance.hh_data = [
        {
            "start-date": utc_datetime(2019, 3, 1),
            "used-kwh": 0,
            "export-net-kwh": 0,
            "import-net-kwh": 0,
            "msp-kwh": 0,
        }
    ]

    se = mocker.patch("chellow.reports.report_247.SiteEra", autospec=True)
    se.site = mocker.Mock()

    sup_s = mocker.patch("chellow.reports.report_247.SupplySource", autospec=True)
    sup_s_instance = sup_s.return_value
    hh_start_date = utc_datetime(2019, 3, 1)
    sup_s_instance.hh_data = [{"start-date": hh_start_date, "msp-kwh": 10}]

    res = _make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id
    )

    assert res["supply_deltas"][True]["net"]["site"] == {hh_start_date: -10.0}


def test_scenario_new_generation(mocker, sess):
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    finish_date = utc_datetime(2009, 8, 31, 22, 30)
    supply_id = None
    report_context = {}
    forecast_from = utc_datetime(2020, 1, 1)

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
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
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
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

    sess.commit()

    scenario_hh = {
        "CI017": {
            "generated": """
                2009-08-01 00:00, 40
                2009-08-15 00:00, 40"""
        }
    }

    era_maps = {
        utc_datetime(2000, 8, 1): {
            "llfcs": {"22": {"new_export": "521"}},
            "supplier_contracts": {"new_export": 4},
        }
    }

    site_deltas = _make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id
    )
    calcs, _, _ = _make_calcs(
        sess,
        site,
        start_date,
        finish_date,
        supply_id,
        site_deltas,
        forecast_from,
        report_context,
        era_maps,
    )

    assert calcs[1][1] == "CI017_extra_gen_TRUE"
    assert calcs[2][2] == "CI017_extra_net_export"


def test_without_scenario(mocker, sess):
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    months = 1
    supply_id = None

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    site_id = site.id
    user = mocker.Mock()
    compression = False
    site_codes = []
    now = utc_datetime(2020, 1, 1)

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
        site_id,
        supply_id,
        user,
        compression,
        site_codes,
        now,
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
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    months = 1
    supply_id = None

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    site_id = site.id
    user = mocker.Mock()
    compression = False
    site_codes = []
    now = utc_datetime(2020, 1, 1)

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
        site_id,
        supply_id,
        user,
        compression,
        site_codes,
        now,
    )

    sheet = odio.parse_spreadsheet(mock_file)
    table = list(sheet.tables[0].rows)

    expected = (
        "For the contract Fusion Mop Contract there doesn't seem to be a "
        "'virtual_bill_titles' function."
    )

    assert expected in table[0][0]


def test_bill_after_end_supply(mocker, sess):
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    months = 1
    supply_id = None

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    site_id = site.id
    user = mocker.Mock()
    compression = False
    site_codes = []
    now = utc_datetime(2020, 1, 1)

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
        site_id,
        supply_id,
        user,
        compression,
        site_codes,
        now,
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


def test_bill_after_end_supply_with_supply_id(mocker, sess):
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    months = 1

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    site_id = site.id
    user = mocker.Mock()
    compression = False
    site_codes = []
    now = utc_datetime(2020, 1, 1)

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
        site_id,
        supply.id,
        user,
        compression,
        site_codes,
        now,
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
    site_1 = Site.insert(sess, "CI017", "Water Works 1")
    site_2 = Site.insert(sess, "CI018", "Water Works 2")
    start_date = utc_datetime(2000, 1, 1, 0, 0)
    months = 1
    supply_id = None

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    site_1_id = site_1.id
    user = mocker.Mock()
    compression = False
    site_codes = []
    now = utc_datetime(2020, 1, 1)

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
        site_1_id,
        supply_id,
        user,
        compression,
        site_codes,
        now,
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
    months = 1
    supply_id = None

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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
        utc_datetime(2000, 1, 25, 23, 30),
        gsp_group,
        mop_contract,
        "773",
        dc_contract,
        "ghyy3",
        "hgjeyhuw",
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

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    site_id = site.id
    user = mocker.Mock()
    compression = False
    site_codes = []
    now = utc_datetime(2020, 1, 1)

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
        site_id,
        supply_id,
        user,
        compression,
        site_codes,
        now,
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
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(1999, 12, 1)
    months = 1
    supply_id = None

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    site_id = site.id
    user = mocker.Mock()
    compression = False
    site_codes = []
    now = utc_datetime(2020, 1, 1)

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
        site_id,
        supply_id,
        user,
        compression,
        site_codes,
        now,
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

    assert expected == table


def test_bill_before_begining_supply_mid_month(mocker, sess):
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2000, 1, 1)
    months = 1
    supply_id = None

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AB Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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
        utc_datetime(2000, 1, 15),
        utc_datetime(2000, 1, 31, 23, 30),
        gsp_group,
        mop_contract,
        "773",
        dc_contract,
        "ghyy3",
        "hgjeyhuw",
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

    sess.commit()

    scenario_props = {
        "scenario_start_year": start_date.year,
        "scenario_start_month": start_date.month,
        "scenario_duration": months,
        "by_hh": False,
    }
    base_name = ["monthly_duration"]
    site_id = site.id
    user = mocker.Mock()
    compression = False
    site_codes = []
    now = utc_datetime(2020, 1, 1)

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
        site_id,
        supply_id,
        user,
        compression,
        site_codes,
        now,
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
    print(table)
    assert expected == table
