from decimal import Decimal

from chellow.e.computer import SupplySource
from chellow.e.triad import (
    _find_triad_dates,
    _process_triad_hh,
    hh,
    national_grid_import,
)
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


def test_process_triad_hh(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = to_utc(ct_datetime(2023, 7, 31, 23, 30))
    finish_date = to_utc(ct_datetime(2023, 7, 31, 23, 30))
    forecast_from = to_utc(ct_datetime(2020, 1, 1))

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    triad_rate_script = {
        "triad_gbp_per_gsp_kw": {
            "import": {"_L": {"HHTariff(Floored)_£/kW": Decimal(0)}}
        },
    }
    Contract.insert_non_core(
        sess,
        "triad_rates",
        "",
        {},
        vf,
        None,
        triad_rate_script,
    )
    triad_dates_rate_script = {
        "triad_dates": [
            utc_datetime(2021, 12, 2, 16, 30),
            utc_datetime(2022, 1, 5, 17, 00),
            utc_datetime(2022, 1, 20, 17, 00),
        ],
    }
    Contract.insert_non_core(
        sess,
        "triad_dates",
        "",
        {},
        vf,
        None,
        triad_dates_rate_script,
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
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    dno_rate_script = {
        "_L": {
            "bands": {},
            "tariffs": {
                "510_00": {
                    "description": "",
                    "gbp-per-kvarh": 0,
                    "green-gbp-per-kwh": 0,
                }
            },
        },
    }
    Contract.insert_dno(
        sess, dno.dno_code, participant, "", {}, vf, None, dno_rate_script
    )
    meter_type = MeterType.insert(sess, "UM", "Unmetered", vf, None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", vf, None)
    mtc = Mtc.insert(sess, "845", True, False, vf, None)
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "HH COP5",
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
        to_utc(ct_datetime(2000, 1, 1)),
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

    sess.commit()
    caches = {}
    era = supply.eras[0]
    is_import = True
    ds = SupplySource(
        sess, start_date, finish_date, forecast_from, era, is_import, caches
    )
    hh = ds.hh_data[0]
    hh["duos-description"] = "Unmetered"

    rate_period = "monthly"
    est_kw = None
    _process_triad_hh(ds, rate_period, est_kw, hh)
    assert hh == {
        "hist-start": utc_datetime(2019, 7, 31, 22, 30),
        "start-date": utc_datetime(2023, 7, 31, 22, 30),
        "ct-day": 31,
        "utc-month": 7,
        "utc-day": 31,
        "utc-decimal-hour": 22.5,
        "utc-year": 2023,
        "utc-hour": 22,
        "utc-minute": 30,
        "ct-year": 2023,
        "ct-month": 7,
        "ct-decimal-hour": 23.5,
        "ct-day-of-week": 0,
        "utc-day-of-week": 0,
        "utc-is-bank-holiday": False,
        "ct-is-bank-holiday": False,
        "utc-is-month-end": False,
        "ct-is-month-end": True,
        "status": "X",
        "imp-msp-kvarh": 0,
        "imp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "exp-msp-kvar": 0,
        "msp-kw": 0,
        "msp-kwh": 0,
        "msp-kva": 0,
        "hist-import-grid-kvarh": 0,
        "hist-export-grid-kvarh": 0,
        "anti-msp-kwh": 0,
        "anti-msp-kw": 0,
        "hist-imp-msp-kvarh": 0,
        "hist-kwh": 0,
        "duos-description": "Unmetered",
        "triad-estimate-1-date": utc_datetime(2021, 12, 2, 16, 30),
        "triad-estimate-1-gsp-kw": 0,
        "triad-estimate-1-laf": 1,
        "triad-estimate-1-msp-kw": 0,
        "triad-estimate-1-status": "X",
        "triad-estimate-2-date": utc_datetime(2022, 1, 5, 17, 0),
        "triad-estimate-2-gsp-kw": 0,
        "triad-estimate-2-laf": 1,
        "triad-estimate-2-msp-kw": 0,
        "triad-estimate-2-status": "X",
        "triad-estimate-3-date": utc_datetime(2022, 1, 20, 17, 0),
        "triad-estimate-3-gsp-kw": 0,
        "triad-estimate-3-laf": 1,
        "triad-estimate-3-msp-kw": 0,
        "triad-estimate-3-status": "X",
        "triad-estimate-gbp": 0.0,
        "triad-estimate-gsp-kw": 0.0,
        "triad-estimate-months": 1,
        "triad-estimate-rate": 0.0,
    }


def test_find_triad_dates(mocker):
    file_name = "nail_file.pdf"
    file_like = mocker.Mock()
    mock_reader = mocker.Mock()
    lines = [
        "here is the table: ",
        "Date  Settlement ",
        "Period  Net System ",
        "Demand (MW)  ",
        "15/12/2022  35 44,561 ",
        "17/01/2023  35 42,022 ",
        "02/12/2022  36 39,573 ",
        "",
    ]
    page = mocker.Mock()
    page.extract_text = mocker.Mock(return_value="\n".join(lines))
    mock_reader.pages = [page]

    mocker.patch("chellow.e.triad.PdfReader", return_value=mock_reader)
    actual = _find_triad_dates(file_name, file_like)
    expected = {
        "a_file_name": "nail_file.pdf",
        "triad_dates": [
            utc_datetime(2022, 12, 15, 17, 0),
            utc_datetime(2023, 1, 17, 17, 0),
            utc_datetime(2022, 12, 2, 17, 30),
        ],
    }
    assert actual == expected


def test_national_grid_import(mocker, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    triad_rate_script = {
        "triad_gbp_per_gsp_kw": {
            "import": {"_L": {"HHTariff(Floored)_£/kW": Decimal(0)}}
        },
    }
    Contract.insert_non_core(
        sess,
        "triad_rates",
        "",
        {},
        vf,
        None,
        triad_rate_script,
    )
    triad_dates_rate_script = {
        "triad_dates": [
            utc_datetime(2021, 12, 2, 16, 30),
            utc_datetime(2022, 1, 5, 17, 00),
            utc_datetime(2022, 1, 20, 17, 00),
        ],
    }
    Contract.insert_non_core(
        sess,
        "triad_dates",
        "",
        {},
        vf,
        None,
        triad_dates_rate_script,
    )
    sess.commit()

    def log(msg):
        pass

    def set_progress(msg):
        pass

    mocker.patch("chellow.e.triad.api_get", return_value={"result": {"records": []}})

    s = mocker.Mock()
    national_grid_import(sess, log, set_progress, s)


def test_hh(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    start_date = to_utc(ct_datetime(2023, 7, 31, 23, 30))
    finish_date = to_utc(ct_datetime(2023, 7, 31, 23, 30))
    forecast_from = to_utc(ct_datetime(2020, 1, 1))

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    triad_rate_script = {
        "triad_gbp_per_gsp_kw": {
            "import": {"_L": {"HHTariff(Floored)_£/kW": Decimal(0)}}
        },
    }
    Contract.insert_non_core(
        sess,
        "triad_rates",
        "",
        {},
        vf,
        None,
        triad_rate_script,
    )
    triad_dates_rate_script = {
        "triad_dates": [
            utc_datetime(2021, 12, 2, 16, 30),
            utc_datetime(2022, 1, 5, 17, 00),
            utc_datetime(2022, 1, 20, 17, 00),
        ],
    }
    Contract.insert_non_core(
        sess,
        "triad_dates",
        "",
        {},
        vf,
        None,
        triad_dates_rate_script,
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
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    dno_rate_script = {
        "_L": {
            "bands": {},
            "tariffs": {
                "510_00": {
                    "description": "",
                    "gbp-per-kvarh": 0,
                    "green-gbp-per-kwh": 0,
                }
            },
        },
    }
    Contract.insert_dno(
        sess, dno.dno_code, participant, "", {}, vf, None, dno_rate_script
    )
    meter_type = MeterType.insert(sess, "UM", "Unmetered", vf, None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", vf, None)
    mtc = Mtc.insert(sess, "845", True, False, vf, None)
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "HH COP5",
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
        to_utc(ct_datetime(2000, 1, 1)),
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

    sess.commit()
    caches = {}
    era = supply.eras[0]
    is_import = True
    ds = SupplySource(
        sess, start_date, finish_date, forecast_from, era, is_import, caches
    )
    h = ds.hh_data[0]
    h["duos-description"] = "Unmetered"

    rate_period = "monthly"
    est_kw = None
    hh(ds, rate_period=rate_period, est_kw=est_kw)
    assert h == {
        "hist-start": utc_datetime(2019, 7, 31, 22, 30),
        "start-date": utc_datetime(2023, 7, 31, 22, 30),
        "ct-day": 31,
        "utc-month": 7,
        "utc-day": 31,
        "utc-decimal-hour": 22.5,
        "utc-year": 2023,
        "utc-hour": 22,
        "utc-minute": 30,
        "ct-year": 2023,
        "ct-month": 7,
        "ct-decimal-hour": 23.5,
        "ct-day-of-week": 0,
        "utc-day-of-week": 0,
        "utc-is-bank-holiday": False,
        "ct-is-bank-holiday": False,
        "utc-is-month-end": False,
        "ct-is-month-end": True,
        "status": "X",
        "imp-msp-kvarh": 0,
        "imp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "exp-msp-kvar": 0,
        "msp-kw": 0,
        "msp-kwh": 0,
        "msp-kva": 0,
        "hist-import-grid-kvarh": 0,
        "hist-export-grid-kvarh": 0,
        "anti-msp-kwh": 0,
        "anti-msp-kw": 0,
        "hist-imp-msp-kvarh": 0,
        "hist-kwh": 0,
        "duos-description": "Unmetered",
        "triad-estimate-1-date": utc_datetime(2021, 12, 2, 16, 30),
        "triad-estimate-1-gsp-kw": 0,
        "triad-estimate-1-laf": 1,
        "triad-estimate-1-msp-kw": 0,
        "triad-estimate-1-status": "X",
        "triad-estimate-2-date": utc_datetime(2022, 1, 5, 17, 0),
        "triad-estimate-2-gsp-kw": 0,
        "triad-estimate-2-laf": 1,
        "triad-estimate-2-msp-kw": 0,
        "triad-estimate-2-status": "X",
        "triad-estimate-3-date": utc_datetime(2022, 1, 20, 17, 0),
        "triad-estimate-3-gsp-kw": 0,
        "triad-estimate-3-laf": 1,
        "triad-estimate-3-msp-kw": 0,
        "triad-estimate-3-status": "X",
        "triad-estimate-gbp": 0.0,
        "triad-estimate-gsp-kw": 0.0,
        "triad-estimate-months": 1,
        "triad-estimate-rate": 0.0,
    }
