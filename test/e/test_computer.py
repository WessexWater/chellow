from chellow.e.computer import (
    SiteSource,
    SupplySource,
    _find_hhs,
    _find_pair,
    _init_hh_data,
    _make_reads,
    _set_status,
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
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_SiteSource_init_hh_data(sess, mocker):
    """New style channels"""
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
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, vf, None, {}
    )
    dc_contract = Contract.insert_dc(sess, "Fus DC", participant, "", {}, vf, None, {})
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fus Sup", participant, "", {}, vf, None, {}
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
    llfc = dno.insert_llfc(sess, "510", "HH HV", voltage_level, False, True, vf, None)
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
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
    era = supply.eras[0]
    channel = era.insert_channel(sess, True, "ACTIVE")
    data_raw = [
        {
            "start_date": utc_datetime(2009, 8, 10),
            "value": 10,
            "status": "A",
        }
    ]
    channel.add_hh_data(sess, data_raw)

    sess.commit()

    caches = {}
    start_date = utc_datetime(2009, 7, 31, 23, 00)
    finish_date = utc_datetime(2009, 7, 31, 23, 00)
    fdate = utc_datetime(2010, 7, 31, 23, 00)
    ds = SiteSource(sess, site, start_date, finish_date, fdate, caches)

    actual_datum = ds.hh_data[0]
    expected_datum = {
        "hist-start": utc_datetime(2009, 7, 31, 23, 0),
        "start-date": utc_datetime(2009, 7, 31, 23, 0),
        "ct-day": 1,
        "utc-month": 7,
        "utc-day": 31,
        "utc-decimal-hour": 23.0,
        "utc-year": 2009,
        "utc-hour": 23,
        "utc-minute": 0,
        "ct-year": 2009,
        "ct-month": 8,
        "ct-decimal-hour": 0.0,
        "ct-day-of-week": 5,
        "utc-day-of-week": 4,
        "utc-is-bank-holiday": False,
        "ct-is-bank-holiday": False,
        "utc-is-month-end": False,
        "ct-is-month-end": False,
        "status": "E",
        "imp-msp-kvarh": 0,
        "imp-msp-kvar": 0,
        "exp-msp-kvarh": 0,
        "exp-msp-kvar": 0,
        "msp-kva": 0,
        "msp-kw": 0,
        "msp-kwh": 0,
        "hist-import-net-kvarh": 0,
        "hist-export-net-kvarh": 0,
        "anti-msp-kwh": 0,
        "anti-msp-kw": 0,
        "hist-imp-msp-kvarh": 0,
        "hist-kwh": 0,
        "hist-import-net-kwh": 0,
        "hist-export-net-kwh": 0,
        "hist-import-gen-kwh": 0,
        "hist-export-gen-kwh": 0,
        "hist-import-3rd-party-kwh": 0,
        "hist-export-3rd-party-kwh": 0,
        "hist-used-3rd-party-kwh": 0,
        "used-3rd-party-kwh": 0,
        "hist-used-gen-msp-kwh": 0,
        "used-gen-msp-kwh": 0,
        "import-net-kwh": 0,
        "export-net-kwh": 0,
        "import-gen-kwh": 0,
        "export-gen-kwh": 0,
        "import-3rd-party-kwh": 0,
        "export-3rd-party-kwh": 0,
        "hist-used-kwh": 0,
        "used-kwh": 0,
        "used-gen-msp-kw": 0,
    }
    assert actual_datum == expected_datum


def test_find_pair(mocker):
    sess = mocker.Mock()
    caches = {}
    is_forwards = True
    first_read = {
        "date": utc_datetime(2010, 1, 1),
        "reads": {},
        "msn": "kh",
        "read_type": "N",
    }
    second_read = {
        "date": utc_datetime(2010, 2, 1),
        "reads": {},
        "msn": "kh",
        "read_type": "N",
    }
    read_list = [first_read, second_read]
    pair = _find_pair(sess, caches, is_forwards, read_list)
    assert pair["start-date"] == utc_datetime(2010, 1, 1)


def test_find_hhs_empty_pairs(mocker):
    mocker.patch("chellow.e.computer.is_tpr", return_value=True)
    caches = {}
    sess = mocker.Mock()
    pairs = []
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1)
    hhs = _find_hhs(caches, sess, pairs, chunk_start, chunk_finish)
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            "msp-kw": 0,
            "msp-kwh": 0,
            "hist-kwh": 0,
            "imp-msp-kvar": 0,
            "imp-msp-kvarh": 0,
            "exp-msp-kvar": 0,
            "exp-msp-kvarh": 0,
            "tpr": "00001",
        }
    }


def test_find_hhs_two_pairs(mocker):
    mocker.patch("chellow.e.computer.is_tpr", return_value=True)
    caches = {}
    sess = mocker.Mock()
    pairs = [
        {"start-date": utc_datetime(2010, 1, 1), "tprs": {"00001": 1}},
        {"start-date": utc_datetime(2010, 1, 1, 0, 30), "tprs": {"00001": 1}},
    ]
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1, 0, 30)
    hhs = _find_hhs(caches, sess, pairs, chunk_start, chunk_finish)
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            "msp-kw": 2.0,
            "msp-kwh": 1.0,
            "hist-kwh": 1.0,
            "imp-msp-kvar": 0,
            "imp-msp-kvarh": 0,
            "exp-msp-kvar": 0,
            "exp-msp-kvarh": 0,
            "tpr": "00001",
        },
        utc_datetime(2010, 1, 1, 0, 30): {
            "msp-kw": 2.0,
            "msp-kwh": 1.0,
            "hist-kwh": 1.0,
            "imp-msp-kvar": 0,
            "imp-msp-kvarh": 0,
            "exp-msp-kvar": 0,
            "exp-msp-kvarh": 0,
            "tpr": "00001",
        },
    }


def test_set_status(mocker):
    hhs = {utc_datetime(2012, 2, 1): {}}

    read_list = [{"date": utc_datetime(2012, 1, 1)}]
    forecast_date = utc_datetime(2012, 3, 1)
    _set_status(hhs, read_list, forecast_date)
    assert hhs == {utc_datetime(2012, 2, 1): {"status": "E"}}


def test_make_reads_forwards(mocker):
    is_forwards = True
    msn = "k"
    read_a = {"date": utc_datetime(2018, 3, 10), "msn": msn}
    read_b = {"date": utc_datetime(2018, 3, 13), "msn": msn}
    prev_reads = iter([read_a])
    pres_reads = iter([read_b])
    actual = list(_make_reads(is_forwards, prev_reads, pres_reads))
    expected = [read_a, read_b]
    assert actual == expected


def test_make_reads_forwards_meter_change(mocker):
    is_forwards = True
    dt = utc_datetime(2018, 3, 1)
    read_a = {"date": dt, "msn": "a"}
    read_b = {"date": dt, "msn": "b"}
    prev_reads = iter([read_a])
    pres_reads = iter([read_b])
    actual = list(_make_reads(is_forwards, prev_reads, pres_reads))
    expected = [read_b, read_a]
    assert actual == expected


def test_make_reads_backwards(mocker):
    is_forwards = False
    msn = "k"
    read_a = {"date": utc_datetime(2018, 3, 10), "msn": msn}
    read_b = {"date": utc_datetime(2018, 3, 13), "msn": msn}
    prev_reads = iter([read_a])
    pres_reads = iter([read_b])
    actual = list(_make_reads(is_forwards, prev_reads, pres_reads))
    expected = [read_b, read_a]
    assert actual == expected


def test_init_hh_data(sess, mocker):
    """New style channels"""
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
    source = Source.get_by_code(sess, "net")
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
    era = supply.eras[0]
    channel = era.insert_channel(sess, True, "ACTIVE")
    data_raw = [
        {
            "start_date": utc_datetime(2009, 8, 10),
            "value": 10,
            "status": "A",
        }
    ]
    channel.add_hh_data(sess, data_raw)

    sess.commit()

    caches = {}
    chunk_start = utc_datetime(2009, 7, 31, 23, 00)
    chunk_finish = utc_datetime(2009, 8, 31, 22, 30)
    is_import = True
    full_channels, hhd = _init_hh_data(
        sess, caches, era, chunk_start, chunk_finish, is_import
    )

    assert full_channels

    expected_hhd = {
        utc_datetime(2009, 8, 10): {
            "imp-msp-kvarh": 0.0,
            "imp-msp-kvar": 0.0,
            "exp-msp-kvarh": 0.0,
            "exp-msp-kvar": 0.0,
            "status": "A",
            "hist-kwh": 10.0,
            "msp-kwh": 10.0,
            "msp-kw": 20.0,
        }
    }
    assert hhd == expected_hhd


def test_init_hh_data_export(sess, mocker):
    """New style channels"""
    valid_from = to_utc(ct_datetime(1996, 1, 1))
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
    exp_supplier_contract = Contract.insert_supplier(
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
    mtc = Mtc.insert(
        sess,
        "845",
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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
        "521",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        False,
        valid_from,
        None,
    )
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
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
        None,
        None,
        None,
        None,
        None,
        "22 7867 6232 781",
        "521",
        exp_supplier_contract,
        "7748",
        361,
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

    reactive_channel = era.insert_channel(sess, False, "REACTIVE_IMP")
    reactive_data_raw = [
        {
            "start_date": utc_datetime(2009, 8, 10),
            "value": 5,
            "status": "A",
        }
    ]
    reactive_channel.add_hh_data(sess, reactive_data_raw)
    sess.commit()

    caches = {}
    chunk_start = utc_datetime(2009, 7, 31, 23, 00)
    chunk_finish = utc_datetime(2009, 8, 31, 22, 30)
    is_import = False
    full_channels, hhd = _init_hh_data(
        sess, caches, era, chunk_start, chunk_finish, is_import
    )

    assert full_channels

    expected_hhd = {
        utc_datetime(2009, 8, 10): {
            "imp-msp-kvarh": 5.0,
            "imp-msp-kvar": 10.0,
            "exp-msp-kvarh": 0.0,
            "exp-msp-kvar": 0.0,
            "status": "A",
            "hist-kwh": 10.0,
            "msp-kwh": 10.0,
            "msp-kw": 20.0,
        }
    }
    assert hhd == expected_hhd


def test_SupplySource_init_hh(sess, mocker):
    """Old style channels"""
    valid_from = to_utc(ct_datetime(1996, 1, 1))
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
    exp_supplier_contract = Contract.insert_supplier(
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
    Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(
        sess,
        "845",
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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
        "521",
        "Export (HV)",
        voltage_level,
        False,
        False,
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
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
        None,
        None,
        None,
        None,
        None,
        "22 7867 6232 781",
        "521",
        exp_supplier_contract,
        "7748",
        361,
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
    is_import = False
    ss = SupplySource(
        sess, start_date, finish_date, forecast_date, era, is_import, caches
    )

    assert not ss.full_channels


def test_SupplySource_init_nhh(sess, mocker):
    """Old style channels"""
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
    pc = Pc.insert(sess, "03", "nhh", utc_datetime(2000, 1, 1), None)
    ssc = Ssc.insert(sess, "0393", "unrestricted", True, utc_datetime(2000, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    exp_supplier_contract = Contract.insert_supplier(
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
    Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc = Mtc.insert(
        sess,
        "845",
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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
    llfc_imp = dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
    llfc_exp = dno.insert_llfc(
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
    energisation_status = EnergisationStatus.get_by_code(sess, "D")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, valid_from, None)
    MtcLlfc.insert(sess, mtc_participant, llfc_imp, valid_from, None)
    mtc_llfc_imp_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc_imp, valid_from, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_imp_ssc, pc, valid_from, None)
    MtcLlfc.insert(sess, mtc_participant, llfc_exp, valid_from, None)
    mtc_llfc_exp_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc_exp, valid_from, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_exp_ssc, pc, valid_from, None)
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
        ssc.code,
        energisation_status,
        dtc_meter_type,
        None,
        None,
        None,
        None,
        None,
        "22 7867 6232 781",
        "521",
        exp_supplier_contract,
        "7748",
        361,
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
    is_import = False
    SupplySource(sess, start_date, finish_date, forecast_date, era, is_import, caches)


def test_SiteSource_get_data_sources(mocker):
    mocker.patch.object(SiteSource, "__init__", lambda *x: None)
    mocker.patch("chellow.e.computer.displaced_era")
    ds = SiteSource()
    ds.forecast_date = to_utc(ct_datetime(2010, 1, 1))
    ds.start_date = to_utc(ct_datetime(2008, 1, 1))
    ds.finish_date = to_utc(ct_datetime(2008, 8, 31, 22, 30))
    ds.stream_focus = "gen-used"
    ds.sess = mocker.Mock()
    ds.caches = {}
    ds.site = mocker.Mock()
    ds.era_maps = mocker.Mock()
    ds.deltas = mocker.Mock()

    start_date = to_utc(ct_datetime(2008, 7, 1))
    finish_date = to_utc(ct_datetime(2008, 7, 31, 23, 30))
    result = ds.get_data_sources(start_date, finish_date)
    next(result)


def test_SiteSource_get_data_sources_clock_change(mocker):
    mocker.patch.object(SiteSource, "__init__", lambda *x: None)
    mocker.patch("chellow.e.computer.displaced_era")
    mock_c_months_u = mocker.patch("chellow.e.computer.c_months_u")
    ds = SiteSource()
    ds.forecast_date = to_utc(ct_datetime(2010, 1, 1))
    ds.start_date = to_utc(ct_datetime(2008, 1, 1))
    ds.finish_date = to_utc(ct_datetime(2008, 8, 31, 22, 30))
    ds.stream_focus = "gen-used"
    ds.sess = mocker.Mock()
    ds.caches = {}
    ds.site = mocker.Mock()
    ds.era_maps = mocker.Mock()
    ds.deltas = mocker.Mock()

    start_date = to_utc(ct_datetime(2008, 4, 1))
    finish_date = to_utc(ct_datetime(2008, 4, 30, 23, 30))
    result = ds.get_data_sources(start_date, finish_date)
    try:
        next(result)
    except StopIteration:
        pass
    mock_c_months_u.assert_called_with(
        finish_month=4, finish_year=2008, start_month=4, start_year=2008
    )
