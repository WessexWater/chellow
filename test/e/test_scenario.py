from chellow.e.scenario import make_calcs, make_site_deltas
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
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


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

    ss = mocker.patch("chellow.e.scenario.SiteSource", autospec=True)
    ss_instance = ss.return_value
    ss_instance.hh_data = [
        {
            "start-date": utc_datetime(2019, 3, 1),
            "used-kwh": 0,
            "export-grid-kwh": 0,
            "import-grid-kwh": 0,
            "msp-kwh": 0,
        }
    ]

    se = mocker.patch("chellow.e.scenario.SiteEra", autospec=True)
    se.site = mocker.Mock()

    sup_s = mocker.patch("chellow.e.scenario.SupplySource", autospec=True)
    sup_s_instance = sup_s.return_value
    sup_s_instance.hh_data = {}

    res = make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id
    )

    assert len(res["supply_deltas"][False]["grid"]["site"]) == 0


def test_make_site_deltas_hh_multi_month(mocker):
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

    ss = mocker.patch("chellow.e.scenario.SiteSource", autospec=True)
    ss_instance = ss.return_value
    ss_instance.hh_data = [
        {
            "start-date": utc_datetime(2019, 3, 1),
            "used-kwh": 0,
            "export-grid-kwh": 0,
            "import-grid-kwh": 0,
            "msp-kwh": 0,
        }
    ]

    se = mocker.patch("chellow.e.scenario.SiteEra", autospec=True)
    se.site = mocker.Mock()

    sup_s = mocker.patch("chellow.e.scenario.SupplySource", autospec=True)
    sup_s_instance = sup_s.return_value
    sup_s_instance.hh_data = {}

    res = make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id
    )
    filter_returns = iter([[era_1], []])

    class Sess:
        def query(self, *args):
            return self

        def join(self, *args):
            return self

        def filter(self, *args):
            return next(filter_returns)

    sess = Sess()
    res = make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id
    )

    assert len(res["supply_deltas"][False]["grid"]["site"]) == 0


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

    ss = mocker.patch("chellow.e.scenario.SiteSource", autospec=True)
    ss_instance = ss.return_value
    ss_instance.hh_data = [
        {
            "start-date": utc_datetime(2019, 3, 1),
            "used-kwh": 0,
            "export-grid-kwh": 0,
            "import-grid-kwh": 0,
            "msp-kwh": 0,
        }
    ]

    se = mocker.patch("chellow.e.scenario.SiteEra", autospec=True)
    se.site = mocker.Mock()

    sup_s = mocker.patch("chellow.e.scenario.SupplySource", autospec=True)
    sup_s_instance = sup_s.return_value
    hh_start_date = utc_datetime(2019, 3, 1)
    sup_s_instance.hh_data = [{"start-date": hh_start_date, "msp-kwh": 10}]

    res = make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_id
    )

    assert res["supply_deltas"][True]["grid"]["site"] == {hh_start_date: -10.0}


def test_make_calcs_new_generation(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    finish_date = utc_datetime(2009, 8, 31, 22, 30)
    supply_ids = None
    report_context = {}
    forecast_from = utc_datetime(2020, 1, 1)

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
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, vf, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    imp_supplier_charge_script = """
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
        imp_supplier_charge_script,
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
    mtc = Mtc.insert(sess, "845", True, False, vf, None)
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
    llfc_imp = dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        vf,
        None,
    )
    dno.insert_llfc(
        sess,
        "521",
        "Export (HV)",
        voltage_level,
        False,
        False,
        vf,
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc_imp, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
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

    site_deltas = make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_ids
    )
    calcs, _ = make_calcs(
        sess,
        site,
        start_date,
        finish_date,
        supply_ids,
        site_deltas,
        forecast_from,
        report_context,
        era_maps,
        None,
    )
    assert calcs[1][1] == "displaced"
    assert calcs[2][1] == "CI017_extra_gen_TRUE"
    assert calcs[3][2] == "CI017_extra_grid_export"
