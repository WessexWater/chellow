from collections import defaultdict
from decimal import Decimal

from chellow.e.computer import SiteSource, SupplySource
from chellow.e.duos import datum_2010_04_01, datum_2012_02_23, duos_vb
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
    MtcLlfcSsc,
    MtcLlfcSscPc,
    MtcParticipant,
    MtcSsc,
    Participant,
    Pc,
    Site,
    Source,
    Ssc,
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, hh_range, to_utc, utc_datetime


def test_duos_vb_unmetered(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    caches = {"dno": {"22": {}}}
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

    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
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
    Ssc.insert(sess, "0393", "All", True, vf, None)
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2000, 1, 31, 23, 30),
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
        None,
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
    dno_rates = {
        "_L": {
            "bands": [],
            "ums_bands": [
                {
                    "band": "black",
                    "weekend": False,
                    "start-decimal-hour": Decimal(0.5),
                    "finish-decimal-hour": Decimal(1),
                    "start-month": 1,
                    "finish-month": 12,
                },
                {
                    "band": "yellow",
                    "weekend": False,
                    "start-decimal-hour": Decimal(1),
                    "finish-decimal-hour": Decimal(1.5),
                    "start-month": 1,
                    "finish-month": 12,
                },
            ],
            "tariffs": {
                "510": {
                    "description": "Unmetered Supplies",
                    "gbp-per-kvarh": 0,
                    "black-gbp-per-kwh": Decimal("0.83"),
                    "green-gbp-per-kwh": Decimal("0.72"),
                    "yellow-gbp-per-kwh": Decimal("0.32"),
                    "gbp-per-mpan-per-day": 0,
                    "gbp-per-kva-per-day": 0,
                }
            },
        }
    }
    Contract.insert_dno(sess, dno.dno_code, participant, "", {}, vf, None, dno_rates)

    start_date = to_utc(ct_datetime(2019, 2, 1))
    finish_date = to_utc(ct_datetime(2019, 2, 1, 1, 0))

    for hh in hh_range(caches, start_date, finish_date):
        llfc.insert_laf(sess, hh, 1)

    era = supply.eras[0]

    ds = SupplySource(
        sess,
        start_date,
        finish_date,
        to_utc(ct_datetime(2025, 1, 1)),
        era,
        True,
        caches,
    )

    sess.commit()

    duos_vb(ds)

    assert ds.hh_data == [
        {
            "anti-msp-kw": 0,
            "anti-msp-kwh": 0,
            "ct-day": 1,
            "ct-day-of-week": 4,
            "ct-decimal-hour": 0.0,
            "ct-is-bank-holiday": False,
            "ct-is-month-end": False,
            "ct-month": 2,
            "ct-year": 2019,
            "duos-description": "Unmetered Supplies",
            "duos-reactive-kvarh": 0.0,
            "duos-green-gbp": 0.0,
            "duos-green-kwh": 0,
            "duos-green-rate": 0.72,
            "exp-msp-kvar": 0,
            "exp-msp-kvarh": 0,
            "gsp-kw": 0.0,
            "gsp-kwh": 0.0,
            "hist-export-grid-kvarh": 0,
            "hist-imp-msp-kvarh": 0,
            "hist-import-grid-kvarh": 0,
            "hist-kwh": 0,
            "hist-start": utc_datetime(2019, 2, 1, 0, 0),
            "imp-msp-kvar": 0,
            "imp-msp-kvarh": 0,
            "laf": 1.0,
            "msp-kva": 0.0,
            "msp-kw": 0,
            "msp-kwh": 0,
            "start-date": utc_datetime(2019, 2, 1, 0, 0),
            "status": "X",
            "utc-day": 1,
            "utc-day-of-week": 4,
            "utc-decimal-hour": 0.0,
            "utc-hour": 0,
            "utc-is-bank-holiday": False,
            "utc-is-month-end": False,
            "utc-minute": 0,
            "utc-month": 2,
            "utc-year": 2019,
        },
        {
            "anti-msp-kw": 0,
            "anti-msp-kwh": 0,
            "ct-day": 1,
            "ct-day-of-week": 4,
            "ct-decimal-hour": 0.5,
            "ct-is-bank-holiday": False,
            "ct-is-month-end": False,
            "ct-month": 2,
            "ct-year": 2019,
            "duos-description": "Unmetered Supplies",
            "duos-reactive-kvarh": 0.0,
            "duos-black-gbp": 0.0,
            "duos-black-kwh": 0,
            "duos-black-rate": 0.83,
            "exp-msp-kvar": 0,
            "exp-msp-kvarh": 0,
            "gsp-kw": 0.0,
            "gsp-kwh": 0.0,
            "hist-export-grid-kvarh": 0,
            "hist-imp-msp-kvarh": 0,
            "hist-import-grid-kvarh": 0,
            "hist-kwh": 0,
            "hist-start": utc_datetime(2019, 2, 1, 0, 30),
            "imp-msp-kvar": 0,
            "imp-msp-kvarh": 0,
            "laf": 1.0,
            "msp-kva": 0.0,
            "msp-kw": 0,
            "msp-kwh": 0,
            "start-date": utc_datetime(2019, 2, 1, 0, 30),
            "status": "X",
            "utc-day": 1,
            "utc-day-of-week": 4,
            "utc-decimal-hour": 0.5,
            "utc-hour": 0,
            "utc-is-bank-holiday": False,
            "utc-is-month-end": False,
            "utc-minute": 30,
            "utc-month": 2,
            "utc-year": 2019,
        },
        {
            "anti-msp-kw": 0,
            "anti-msp-kwh": 0,
            "ct-day": 1,
            "ct-day-of-week": 4,
            "ct-decimal-hour": 1.0,
            "ct-is-bank-holiday": False,
            "ct-is-month-end": False,
            "ct-month": 2,
            "ct-year": 2019,
            "duos-description": "Unmetered Supplies",
            "duos-reactive-kvarh": 0.0,
            "duos-yellow-gbp": 0.0,
            "duos-yellow-kwh": 0,
            "duos-yellow-rate": 0.32,
            "exp-msp-kvar": 0,
            "exp-msp-kvarh": 0,
            "gsp-kw": 0.0,
            "gsp-kwh": 0.0,
            "hist-export-grid-kvarh": 0,
            "hist-imp-msp-kvarh": 0,
            "hist-import-grid-kvarh": 0,
            "hist-kwh": 0,
            "hist-start": utc_datetime(2019, 2, 1, 1, 0),
            "imp-msp-kvar": 0,
            "imp-msp-kvarh": 0,
            "laf": 1.0,
            "msp-kva": 0.0,
            "msp-kw": 0,
            "msp-kwh": 0,
            "start-date": utc_datetime(2019, 2, 1, 1, 0),
            "status": "X",
            "utc-day": 1,
            "utc-day-of-week": 4,
            "utc-decimal-hour": 1.0,
            "utc-hour": 1,
            "utc-is-bank-holiday": False,
            "utc-is-month-end": False,
            "utc-minute": 0,
            "utc-month": 2,
            "utc-year": 2019,
        },
    ]


def test_duos_availability_from_to(mocker, sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    caches = {"dno": {"22": {}}}
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", to_utc(ct_datetime(2000, 1, 1)), None, "22"
    )
    dno_contract = Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        valid_from,
        None,
        {},
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
        to_utc(ct_datetime(1996, 1, 1)),
        None,
    )

    month_from = to_utc(ct_datetime(2019, 2, 1))
    month_to = to_utc(ct_datetime(2019, 2, 28, 23, 30))

    for hh in hh_range(caches, month_from, month_to):
        llfc.insert_laf(sess, hh, 1)

    sess.commit()

    ds = mocker.Mock()
    ds.dno_code = "22"
    ds.dno_contract = dno_contract
    ds.gsp_group_code = "_L"
    ds.llfc_code = "510"
    ds.is_displaced = False
    ds.sc = 0
    ds.supplier_bill = defaultdict(int)
    ds.supplier_rate_sets = defaultdict(set)
    ds.get_data_sources = mocker.Mock(return_value=[])
    ds.caches = caches
    ds.sess = sess
    dno_rates = {
        "_L": {
            "bands": {},
            "tariffs": {
                "510": {
                    "gbp-per-kvarh": 0,
                    "green-gbp-per-kwh": 0,
                    "gbp-per-mpan-per-day": 0,
                    "gbp-per-kva-per-day": 0,
                }
            },
        }
    }
    ds.hh_rate = mocker.Mock(return_value=dno_rates)

    hh = {
        "start-date": ct_datetime(2019, 2, 28, 23, 30),
        "ct-decimal-hour": 23.5,
        "ct-is-month-end": True,
        "ct-day-of-week": 3,
        "ct-year": 2019,
        "ct-month": 2,
        "msp-kwh": 0,
        "imp-msp-kvarh": 0,
        "exp-msp-kvarh": 0,
    }
    datum_2010_04_01(ds, hh)

    ds.get_data_sources.assert_called_with(month_from, month_to)


def test_lafs_hist(mocker, sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    caches = {"dno": {"22": {}}}
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    insert_voltage_levels(sess)
    vl = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(sess, "510", "5", vl, False, True, valid_from, None)

    hist_laf = 1.5
    start_date = to_utc(ct_datetime(2019, 2, 28, 23, 30))
    hist_date = to_utc(ct_datetime(2018, 2, 28, 23, 30))
    llfc.insert_laf(sess, hist_date, hist_laf)

    sess.commit()

    ds = mocker.Mock()
    ds.start_date = start_date
    ds.finish_date = start_date
    ds.history_start = hist_date
    ds.history_finish = hist_date
    ds.dno_code = "22"
    ds.gsp_group_code = "_L"
    ds.llfc_code = "510"
    ds.is_displaced = False
    ds.sc = 0
    ds.supplier_bill = defaultdict(int)
    ds.supplier_rate_sets = defaultdict(set)
    ds.get_data_sources = mocker.Mock(return_value=iter([ds]))
    ds.caches = caches
    ds.sess = sess
    dno_rates = {
        "_L": {
            "bands": {},
            "tariffs": {
                "510": {
                    "description": "LV Sub Generation Site Specific",
                    "gbp-per-kvarh": 0,
                    "green-gbp-per-kwh": 0,
                    "gbp-per-mpan-per-day": 0,
                    "gbp-per-kva-per-day": 0,
                }
            },
        }
    }
    ds.hh_rate = mocker.Mock(return_value=dno_rates)

    hh = {
        "hist-start": hist_date,
        "start-date": start_date,
        "ct-decimal-hour": 23.5,
        "ct-is-month-end": True,
        "ct-day-of-week": 3,
        "ct-year": 2019,
        "ct-month": 2,
        "msp-kwh": 0,
        "msp-kw": 0,
        "msp-kva": 0,
        "imp-msp-kvarh": 0,
        "imp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "exp-msp-kvar": 0,
    }
    ds.hh_data = [hh]
    datum_2012_02_23(ds, hh)

    assert caches["dno"]["22"]["lafs"]["510"][start_date] == hist_laf


def test_lafs_forecast_none(mocker, sess):
    dno_code = "22"
    caches = {"dno": {dno_code: {}}}
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", to_utc(ct_datetime(2000, 1, 1)), None, "22"
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc_code = "510"
    dno.insert_llfc(
        sess,
        llfc_code,
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        to_utc(ct_datetime(1996, 1, 1)),
        None,
    )

    start_date = to_utc(ct_datetime(2019, 2, 28, 23, 30))
    hist_date = to_utc(ct_datetime(2018, 2, 28, 23, 30))

    sess.commit()

    ds = mocker.Mock()
    ds.forecast_date = hist_date
    ds.start_date = start_date
    ds.finish_date = start_date
    ds.history_start = hist_date
    ds.history_finish = hist_date
    ds.dno_code = dno_code
    ds.gsp_group_code = "_L"
    ds.llfc_code = llfc_code
    ds.is_displaced = False
    ds.sc = 0
    ds.supplier_bill = defaultdict(int)
    ds.supplier_rate_sets = defaultdict(set)
    ds.get_data_sources = mocker.Mock(return_value=iter([ds]))
    ds.caches = caches
    ds.sess = sess
    dno_rates = {
        "_L": {
            "bands": {},
            "tariffs": {
                llfc_code: {
                    "description": "LV Sub Generation Site Specific",
                    "gbp-per-kvarh": 0,
                    "green-gbp-per-kwh": 0,
                    "gbp-per-mpan-per-day": 0,
                    "gbp-per-kva-per-day": 0,
                }
            },
        }
    }
    ds.hh_rate = mocker.Mock(return_value=dno_rates)

    hh = {
        "hist-start": hist_date,
        "start-date": start_date,
        "ct-decimal-hour": 23.5,
        "ct-is-month-end": True,
        "ct-day-of-week": 3,
        "ct-year": 2019,
        "ct-month": 2,
        "msp-kwh": 0,
        "msp-kw": 0,
        "msp-kva": 0,
        "imp-msp-kvarh": 0,
        "imp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "exp-msp-kvar": 0,
    }
    ds.hh_data = [hh]
    datum_2012_02_23(ds, hh)

    assert caches["dno"][dno_code]["lafs"][llfc_code][start_date] == 1


def test_lafs_forecast(mocker, sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    caches = {"dno": {"22": {}}}
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    insert_voltage_levels(sess)
    vl = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(sess, "510", "HV", vl, False, True, valid_from, None)

    forecast_date = to_utc(ct_datetime(2018, 5, 31, 23, 30))
    llfc.insert_laf(sess, forecast_date, 1.4)

    sess.commit()

    hist_date = to_utc(ct_datetime(2018, 2, 28, 23, 30))
    start_date = to_utc(ct_datetime(2019, 2, 28, 23, 30))

    ds = mocker.Mock()
    ds.start_date = start_date
    ds.finish_date = start_date
    ds.history_start = hist_date
    ds.history_finish = hist_date
    ds.forecast_date = forecast_date
    ds.dno_code = "22"
    ds.gsp_group_code = "_L"
    ds.llfc_code = "510"
    ds.is_displaced = False
    ds.sc = 0
    ds.supplier_bill = defaultdict(int)
    ds.supplier_rate_sets = defaultdict(set)
    ds.get_data_sources = mocker.Mock(return_value=iter([ds]))
    ds.caches = caches
    ds.sess = sess
    dno_rates = {
        "_L": {
            "bands": {},
            "tariffs": {
                "510": {
                    "description": "LV Sub Generation Site Specific",
                    "gbp-per-kvarh": 0,
                    "green-gbp-per-kwh": 0,
                    "gbp-per-mpan-per-day": 0,
                    "gbp-per-kva-per-day": 0,
                }
            },
        }
    }
    ds.hh_rate = mocker.Mock(return_value=dno_rates)

    hh = {
        "hist-start": hist_date,
        "start-date": start_date,
        "ct-decimal-hour": 23.5,
        "ct-is-month-end": True,
        "ct-day-of-week": 3,
        "ct-year": 2019,
        "ct-month": 2,
        "msp-kwh": 0,
        "msp-kw": 0,
        "msp-kva": 0,
        "imp-msp-kvarh": 0,
        "imp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "exp-msp-kvar": 0,
    }
    ds.hh_data = [hh]
    datum_2012_02_23(ds, hh)


def test_SiteSource(sess):
    valid_from = utc_datetime(1996, 1, 1)
    site = Site.insert(sess, "CI017", "Water Works")
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
        sess, market_role_M, "Fusion Mop Ltd", valid_from, None, None
    )
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, valid_from, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, valid_from, None, {}
    )
    pc = Pc.insert(sess, "03", "nhh", utc_datetime(2000, 1, 1), None)
    ssc = Ssc.insert(sess, "0393", "unrestricted", True, utc_datetime(2000, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    dno_rates = {
        "tariffs": {
            "510": {
                "day-gbp-per-kwh": 0,
                "night-gbp-per-kwh": 0,
                "reactive-gbp-per-kvarh": 0,
            }
        },
        "lafs": {"hv": {"other": 0}},
    }
    Contract.insert_dno(
        sess, dno.dno_code, participant, "", {}, valid_from, None, dno_rates
    )
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
        sess, "510", "PC 5-8 & HH HV", voltage_level, True, True, valid_from, None
    )
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "D")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, valid_from, None)
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, valid_from, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, valid_from, None)
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
        dc_contract,
        "hgjeyhuw",
        dno,
        pc,
        "845",
        cop,
        comm,
        ssc.code,
        energisation_status,
        dtc_meter_type,
        "22 7867 6232 781",
        "510",
        supplier_contract,
        "7748",
        361,
        None,
        None,
        None,
        None,
        None,
    )
    era = supply.eras[0]
    active_channel = era.insert_channel(sess, False, "ACTIVE")
    active_data_raw = [
        {
            "start_date": utc_datetime(2009, 8, 10),
            "value": 10,
            "status": "A",
        }
    ]
    active_channel.add_hh_data(sess, active_data_raw)
    era.insert_channel(sess, True, "REACTIVE_IMP")

    sess.commit()

    caches = {}
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    finish_date = utc_datetime(2009, 8, 31, 22, 30)
    forecast_date = utc_datetime(2019, 8, 31, 22, 30)
    ss = SiteSource(sess, site, start_date, finish_date, forecast_date, caches, era=era)
    duos_vb(ss)
