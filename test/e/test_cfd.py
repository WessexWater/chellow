from chellow.e.cfd import (
    _find_quarter_rs,
    _reconciled_quarters,
    hh,
    import_forecast_ilr_tra,
)
from chellow.e.computer import SupplySource
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


def test_reconciled_quarters(mocker):
    s = mocker.Mock()
    search_from = to_utc(ct_datetime(2023, 1, 1))
    log = mocker.Mock()
    result = [
        {"Settlement_Date": "2023-03-30", "Settlement_Run_Type": "DF"},
        {"Settlement_Date": "2023-03-30", "Settlement_Run_Type": "RF"},
        {"Settlement_Date": "2023-03-31", "Settlement_Run_Type": "DF"},
        {"Settlement_Date": "2023-03-31", "Settlement_Run_Type": "RF"},
    ]
    mocker.patch("chellow.e.cfd.api_records", return_value=result)
    actual = _reconciled_quarters(log, s, search_from)
    expected = {}
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
    assert actual is False


def test_import_forecast_ilr_tra(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "CALB", "Calb")
    market_role = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role, "None core", vf, None, None)
    sess.commit()

    s = mocker.Mock()
    mock_request = mocker.Mock()
    req_j = {
        "success": True,
        "fields": [],
        "records": [],
    }
    mock_request.json = mocker.Mock(return_value=req_j)
    s.get = mocker.Mock(return_value=mock_request)
    log = mocker.Mock()
    set_progress = mocker.Mock()
    import_forecast_ilr_tra(sess, log, set_progress, s)


def test_import_forecast_ilr_tra_blank_lines(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "CALB", "Calb")
    market_role = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role, "None core", vf, None, None)
    sess.commit()

    s = mocker.Mock()
    mock_request = mocker.Mock()
    req_j = {
        "success": True,
        "fields": [
            {"id": "_id", "type": "int"},
            {"id": "Quarterly_Obligation_Period", "type": "text"},
            {"id": "Period_Start", "type": "text"},
            {"id": "Period_End", "type": "text"},
            {"id": "Interim_Levy_Rate_GBP_Per_MWh", "type": "text"},
            {"id": "Total_Reserve_Amount_GBP", "type": "text"},
            {"id": "Eligible_Demand_MWh", "type": "text"},
            {"id": "BMRP_GBP_Per_MWh", "type": "text"},
            {"id": "IMRP_GBP_Per_MWh", "type": "text"},
            {"id": "Adjusted_ILR_GBP_Per_MWh", "type": "text"},
            {"id": "Additional_TRA_GBP", "type": "text"},
        ],
        "records": [[1, "", "", "", "", "", "", "", "", "", ""]],
    }
    mock_request.json = mocker.Mock(return_value=req_j)
    s.get = mocker.Mock(return_value=mock_request)
    log = mocker.Mock()
    set_progress = mocker.Mock()
    import_forecast_ilr_tra(sess, log, set_progress, s)


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
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
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
        "cfd-rates": {
            "interim": 0.1,
            "operational": 0.0002,
        },
        "ct-day": 1,
        "ct-day-of-week": 2,
        "ct-decimal-hour": 0.0,
        "ct-is-bank-holiday": False,
        "ct-is-month-end": False,
        "ct-month": 1,
        "ct-year": 2020,
        "exp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "hist-export-grid-kvarh": 0,
        "hist-imp-msp-kvarh": 0,
        "hist-import-grid-kvarh": 0,
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
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
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
        "cfd-rates": {
            "interim": 0.1,
            "operational": 0.0002,
        },
        "ct-day": 1,
        "ct-day-of-week": 2,
        "ct-decimal-hour": 0.0,
        "ct-is-bank-holiday": False,
        "ct-is-month-end": False,
        "ct-month": 1,
        "ct-year": 2020,
        "exp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "hist-export-grid-kvarh": 0,
        "hist-imp-msp-kvarh": 0,
        "hist-import-grid-kvarh": 0,
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
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
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
        "cfd-rates": {
            "interim": 0.1,
            "operational": 0.0002,
        },
        "ct-day": 1,
        "ct-day-of-week": 2,
        "ct-decimal-hour": 0.0,
        "ct-is-bank-holiday": False,
        "ct-is-month-end": False,
        "ct-month": 1,
        "ct-year": 2020,
        "exp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "hist-export-grid-kvarh": 0,
        "hist-imp-msp-kvarh": 0,
        "hist-import-grid-kvarh": 0,
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
