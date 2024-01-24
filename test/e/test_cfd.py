from chellow.e.cfd import _find_quarter_rs, _reconciled_days, hh
from chellow.e.computer import SupplySource
from chellow.models import (
    Comm,
    Contract,
    Cop,
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
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_reconciled_days(mocker):
    s = mocker.Mock()
    search_from = mocker.Mock()
    result = {
        "result": {
            "records": [
                {"Settlement_Date": "2023-03-30", "Settlement_Run_Type": "DF"},
                {"Settlement_Date": "2023-03-30", "Settlement_Run_Type": "RF"},
                {"Settlement_Date": "2023-03-31", "Settlement_Run_Type": "DF"},
                {"Settlement_Date": "2023-03-31", "Settlement_Run_Type": "RF"},
            ]
        }
    }
    mocker.patch("chellow.e.cfd.api_sql", return_value=result)
    actual = list(_reconciled_days(s, search_from))
    expected = [
        (
            utc_datetime(2023, 3, 29, 23, 0),
            {
                "DF": {"Settlement_Date": "2023-03-30", "Settlement_Run_Type": "DF"},
                "RF": {"Settlement_Date": "2023-03-30", "Settlement_Run_Type": "RF"},
            },
        ),
        (
            utc_datetime(2023, 3, 30, 23, 0),
            {
                "DF": {"Settlement_Date": "2023-03-31", "Settlement_Run_Type": "DF"},
                "RF": {"Settlement_Date": "2023-03-31", "Settlement_Run_Type": "RF"},
            },
        ),
    ]
    assert actual == expected


def test_find_quarter_rs(sess):
    contract_name = "cfd_rates"
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "CALB", "Calb")
    market_role = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role, "None core", vf, None, None)
    Contract.insert_non_core(
        sess,
        contract_name,
        "",
        {},
        to_utc(ct_datetime(2024, 1, 1)),
        None,
        {"rate_gbp_per_kwh": 0.10},
    )
    sess.commit()

    actual = _find_quarter_rs(sess, contract_name, to_utc(ct_datetime(2024, 4, 1)))
    assert actual is None


def test_hh(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    participant = Participant.insert(sess, "CALB", "Calb")
    market_role = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role, "None core", vf, None, None)
    Contract.insert_non_core(
        sess, "cfd_in_period_tracking", "", {}, vf, None, {"rate_gbp_per_kwh": 0.10}
    )
    Contract.insert_non_core(sess, "cfd_forecast_ilr_tra", "", {}, vf, None, {})
    Contract.insert_non_core(
        sess,
        "cfd_advanced_forecast_ilr_tra",
        "",
        {},
        vf,
        None,
        {"sensitivity": {"Base Case": {"Interim Levy Rate_GBP_Per_MWh": "100"}}},
    )
    Contract.insert_non_core(
        sess,
        "cfd_reconciled_daily_levy_rates",
        "",
        {},
        vf,
        None,
        {"rate_gbp_per_kwh": 0.30},
    )
    Contract.insert_non_core(
        sess,
        "cfd_operational_costs_levy",
        "",
        {},
        vf,
        None,
        {"record": {"Effective_OCL_Rate_GBP_Per_MWh": 0.20}},
    )
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion", vf, None, None)
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
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    supply = site.insert_e_supply(
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
    sess.commit()
    caches = {}
    ss = SupplySource(
        sess,
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2021, 1, 1)),
        supply.eras[0],
        True,
        caches,
    )
    hh(ss)
    expected = {
        "anti-msp-kw": 0,
        "anti-msp-kwh": 0,
        "cfd-rate": 0.10020000000000001,
        "ct-day": 1,
        "ct-day-of-week": 2,
        "ct-decimal-hour": 0.0,
        "ct-is-bank-holiday": False,
        "ct-is-month-end": False,
        "ct-month": 1,
        "ct-year": 2020,
        "exp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "hist-export-net-kvarh": 0,
        "hist-imp-msp-kvarh": 0,
        "hist-import-net-kvarh": 0,
        "hist-kwh": 0,
        "hist-start": utc_datetime(2020, 1, 1, 0, 0),
        "imp-msp-kvar": 0,
        "imp-msp-kvarh": 0,
        "msp-kva": 0.0,
        "start-date": utc_datetime(2020, 1, 1, 0, 0),
        "status": "X",
        "utc-day": 1,
        "utc-day-of-week": 2,
        "utc-decimal-hour": 0.0,
        "utc-hour": 0,
        "utc-is-bank-holiday": False,
        "utc-is-month-end": False,
        "utc-minute": 0,
        "utc-month": 1,
        "utc-year": 2020,
        "msp-kwh": 0,
        "msp-kw": 0,
    }
    assert ss.hh_data[0] == expected


def test_hh_use_period(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    participant = Participant.insert(sess, "CALB", "Calb")
    market_role = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role, "None core", vf, None, None)
    Contract.insert_non_core(
        sess,
        "cfd_in_period_tracking",
        "",
        {},
        vf,
        to_utc(ct_datetime(2020, 1, 1)),
        {"rate_gbp_per_kwh": 0.10},
    )
    Contract.insert_non_core(sess, "cfd_forecast_ilr_tra", "", {}, vf, None, {})
    Contract.insert_non_core(
        sess,
        "cfd_advanced_forecast_ilr_tra",
        "",
        {},
        vf,
        None,
        {"sensitivity": {"Base Case": {"Interim Levy Rate_GBP_Per_MWh": 100}}},
    )
    Contract.insert_non_core(
        sess,
        "cfd_reconciled_daily_levy_rates",
        "",
        {},
        vf,
        None,
        {"rate_gbp_per_kwh": 0.30},
    )
    Contract.insert_non_core(
        sess,
        "cfd_operational_costs_levy",
        "",
        {},
        vf,
        None,
        {"record": {"Effective_OCL_Rate_GBP_Per_MWh": 0.20}},
    )
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion", vf, None, None)
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
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    supply = site.insert_e_supply(
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
    sess.commit()
    caches = {}
    ss = SupplySource(
        sess,
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2021, 1, 1)),
        supply.eras[0],
        True,
        caches,
    )
    hh(ss)
    expected = {
        "anti-msp-kw": 0,
        "anti-msp-kwh": 0,
        "cfd-rate": 0.10020000000000001,
        "ct-day": 1,
        "ct-day-of-week": 2,
        "ct-decimal-hour": 0.0,
        "ct-is-bank-holiday": False,
        "ct-is-month-end": False,
        "ct-month": 1,
        "ct-year": 2020,
        "exp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "hist-export-net-kvarh": 0,
        "hist-imp-msp-kvarh": 0,
        "hist-import-net-kvarh": 0,
        "hist-kwh": 0,
        "hist-start": utc_datetime(2020, 1, 1, 0, 0),
        "imp-msp-kvar": 0,
        "imp-msp-kvarh": 0,
        "msp-kva": 0.0,
        "start-date": utc_datetime(2020, 1, 1, 0, 0),
        "status": "X",
        "utc-day": 1,
        "utc-day-of-week": 2,
        "utc-decimal-hour": 0.0,
        "utc-hour": 0,
        "utc-is-bank-holiday": False,
        "utc-is-month-end": False,
        "utc-minute": 0,
        "utc-month": 1,
        "utc-year": 2020,
        "msp-kwh": 0,
        "msp-kw": 0,
    }
    assert ss.hh_data[0] == expected


def test_hh_use_ilr(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    participant = Participant.insert(sess, "CALB", "Calb")
    market_role = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role, "None core", vf, None, None)
    Contract.insert_non_core(
        sess, "cfd_in_period_tracking", "", {}, vf, None, {"rate_gbp_per_kwh": 0.10}
    )
    Contract.insert_non_core(
        sess,
        "cfd_forecast_ilr_tra",
        "",
        {},
        vf,
        to_utc(ct_datetime(2020, 1, 1)),
        {"record": {"Interim_Levy_Rate_GBP_Per_MWh": "100"}},
    )
    Contract.insert_non_core(
        sess,
        "cfd_advanced_forecast_ilr_tra",
        "",
        {},
        vf,
        None,
        {"sensitivity": {"Base Case": {"Interim Levy Rate_GBP_Per_MWh": 100}}},
    )
    Contract.insert_non_core(
        sess,
        "cfd_reconciled_daily_levy_rates",
        "",
        {},
        vf,
        None,
        {"rate_gbp_per_kwh": 0.30},
    )
    Contract.insert_non_core(
        sess,
        "cfd_operational_costs_levy",
        "",
        {},
        vf,
        None,
        {"record": {"Effective_OCL_Rate_GBP_Per_MWh": 0.20}},
    )
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion", vf, None, None)
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
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    supply = site.insert_e_supply(
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
    sess.commit()
    caches = {}
    ss = SupplySource(
        sess,
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2021, 1, 1)),
        supply.eras[0],
        True,
        caches,
    )
    hh(ss)
    expected = {
        "anti-msp-kw": 0,
        "anti-msp-kwh": 0,
        "cfd-rate": 0.10020000000000001,
        "ct-day": 1,
        "ct-day-of-week": 2,
        "ct-decimal-hour": 0.0,
        "ct-is-bank-holiday": False,
        "ct-is-month-end": False,
        "ct-month": 1,
        "ct-year": 2020,
        "exp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "hist-export-net-kvarh": 0,
        "hist-imp-msp-kvarh": 0,
        "hist-import-net-kvarh": 0,
        "hist-kwh": 0,
        "hist-start": utc_datetime(2020, 1, 1, 0, 0),
        "imp-msp-kvar": 0,
        "imp-msp-kvarh": 0,
        "msp-kva": 0.0,
        "start-date": utc_datetime(2020, 1, 1, 0, 0),
        "status": "X",
        "utc-day": 1,
        "utc-day-of-week": 2,
        "utc-decimal-hour": 0.0,
        "utc-hour": 0,
        "utc-is-bank-holiday": False,
        "utc-is-month-end": False,
        "utc-minute": 0,
        "utc-month": 1,
        "utc-year": 2020,
        "msp-kwh": 0,
        "msp-kw": 0,
    }
    assert ss.hh_data[0] == expected
