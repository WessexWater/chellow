from decimal import Decimal

from sqlalchemy import select

from chellow.general_import import (
    _parse_breakdown,
    general_import_era,
    general_import_g_batch,
    general_import_g_bill,
    general_import_g_era,
    general_import_g_supply,
    general_import_llfc,
    general_import_site,
    general_import_supply,
)
from chellow.models import (
    Comm,
    Contract,
    Cop,
    DtcMeterType,
    EnergisationStatus,
    GBill,
    GContract,
    GDn,
    GReadingFrequency,
    GUnit,
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
    insert_bill_types,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_g_read_types,
    insert_g_reading_frequencies,
    insert_g_units,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, hh_format, to_utc, utc_datetime


def test_general_import_g_batch(mocker):
    sess = mocker.Mock()
    action = "insert"
    vals = ["CH4U", "batch 8883", "Apr 2019"]
    args = []
    general_import_g_batch(sess, action, vals, args)


def test_general_import_g_bill(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site_code = "22488"
    site = Site.insert(sess, site_code, "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "non core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    g_contract_name = "Fusion 2020"
    g_contract = GContract.insert_supplier(sess, g_contract_name, "", {}, vf, None, {})
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    mprn = "87614362"
    msn = "hgeu8rhg"
    site.insert_g_supply(
        sess,
        mprn,
        "main",
        g_exit_zone,
        utc_datetime(2010, 1, 1),
        None,
        msn,
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    batch_name = "b1"
    g_contract.insert_g_batch(sess, batch_name, "batch 1")
    insert_bill_types(sess)
    sess.commit()

    action = "insert"
    vals = [
        g_contract_name,
        batch_name,
        mprn,
        "2019-09-08 00:00",
        "2019-10-01 00:00",
        "2019-10-31 23:30",
        "0.00",
        "0.00",
        "0.00",
        "77hwgtlll",
        "7876hrwlju",
        "N",
        "{}",
        "0",
    ]
    args = []
    general_import_g_bill(sess, action, vals, args)


def test_general_import_g_bill_reads(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site_code = "22488"
    site = Site.insert(sess, site_code, "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_code = "M3"
    g_unit = GUnit.get_by_code(sess, g_unit_code)
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "non core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    g_contract_name = "Fusion 2020"
    g_contract = GContract.insert_supplier(sess, g_contract_name, "", {}, vf, None, {})
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    mprn = "87614362"
    msn = "hgeu8rhg"
    site.insert_g_supply(
        sess,
        mprn,
        "main",
        g_exit_zone,
        utc_datetime(2010, 1, 1),
        None,
        msn,
        1,
        g_unit,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    batch_reference = "b1"
    g_contract.insert_g_batch(sess, batch_reference, "batch 1")
    insert_bill_types(sess)
    insert_g_read_types(sess)
    sess.commit()
    msn = "88hgkdshjf"
    correction_factor_str = "1"
    correction_factor = Decimal("1")
    calorific_value_str = "39"
    calorific_value = Decimal(calorific_value_str)
    prev_value = Decimal("988")
    prev_date = utc_datetime(2019, 10, 1)
    prev_type_code = "E"
    pres_value = Decimal("1200")
    pres_date = utc_datetime(2019, 10, 31, 23, 30)
    pres_type_code = "A"

    action = "insert"
    vals = [
        g_contract_name,
        batch_reference,
        mprn,
        "2019-09-08 01:00",
        "2019-10-01 01:00",
        "2019-10-31 23:30",
        "0.00",
        "0.00",
        "0.00",
        "77hwgtlll",
        "7876hrwlju",
        "N",
        "{}",
        "0",
        msn,
        g_unit_code,
        correction_factor_str,
        calorific_value_str,
        hh_format(prev_date),
        str(prev_value),
        prev_type_code,
        hh_format(pres_date),
        str(pres_value),
        pres_type_code,
    ]
    args = []
    general_import_g_bill(sess, action, vals, args)

    g_bill = sess.scalars(select(GBill)).one()
    g_read = g_bill.g_reads[0]

    assert g_read.msn == msn
    assert g_read.g_unit == g_unit
    assert g_read.correction_factor == correction_factor
    assert g_read.calorific_value == calorific_value
    assert g_read.prev_value == prev_value
    assert g_read.prev_date == prev_date
    assert g_read.prev_type.code == prev_type_code
    assert g_read.pres_value == pres_value
    assert g_read.pres_date == pres_date
    assert g_read.pres_type.code == pres_type_code


def test_general_import_g_era_insert(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site_code = "22488"
    site = Site.insert(sess, site_code, "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "non core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    g_contract = GContract.insert_supplier(sess, "Fusion 2020", "", {}, vf, None, {})
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    mprn = "87614362"
    msn = "hgeu8rhg"
    site.insert_g_supply(
        sess,
        mprn,
        "main",
        g_exit_zone,
        utc_datetime(2010, 1, 1),
        None,
        msn,
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    new_aq = "10"
    new_soq = "20"

    action = "insert"
    vals = [
        mprn,
        "2019-09-08 00:00",
        site_code,
        "{no change}",
        "1",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        new_aq,
        new_soq,
    ]
    args = []
    general_import_g_era(sess, action, vals, args)

    expected_args = [
        ("MPRN", "87614362"),
        ("Start Date", "2019-09-08 00:00"),
        ("Site Code", site_code),
        ("Meter Serial Number", "{no change}"),
        ("Correction Factor", "1"),
        ("Unit", "{no change}"),
        ("Supplier Contract Name", "{no change}"),
        ("Account", "{no change}"),
        ("Reading Frequency", "{no change}"),
        ("AQ", new_aq),
        ("SOQ", new_soq),
    ]

    assert args == expected_args


def test_general_import_g_era_insert_no_change(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "non core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    g_contract = GContract.insert_supplier(sess, "Fusion 2020", "", {}, vf, None, {})
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    mprn = "87614362"
    msn = "hgeu8rhg"
    site.insert_g_supply(
        sess,
        mprn,
        "main",
        g_exit_zone,
        utc_datetime(2010, 1, 1),
        None,
        msn,
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    action = "insert"
    vals = [
        mprn,
        "2019-09-08 00:00",
        "{no change}",
        "{no change}",
        "1",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
    ]
    args = []
    general_import_g_era(sess, action, vals, args)
    expected_args = [
        ("MPRN", "87614362"),
        ("Start Date", "2019-09-08 00:00"),
        ("Site Code", "{no change}"),
        ("Meter Serial Number", "{no change}"),
        ("Correction Factor", "1"),
        ("Unit", "{no change}"),
        ("Supplier Contract Name", "{no change}"),
        ("Account", "{no change}"),
        ("Reading Frequency", "{no change}"),
        ("AQ", "{no change}"),
        ("SOQ", "{no change}"),
    ]

    assert args == expected_args


def test_general_import_g_era_update(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "non core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    g_contract = GContract.insert_supplier(sess, "Fusion 2020", "", {}, vf, None, {})
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    mprn = "87614362"
    msn = "hgeu8rhg"
    site.insert_g_supply(
        sess,
        mprn,
        "main",
        g_exit_zone,
        utc_datetime(2010, 1, 1),
        None,
        msn,
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )

    action = "update"
    vals = [
        mprn,
        "2019-09-08 00:00",
        "{no change}",
        "{no change}",
        "A Mop Contract",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
    ]
    args = []
    general_import_g_era(sess, action, vals, args)
    expected_args = [
        ("MPRN", "87614362"),
        ("date", "2019-09-08 00:00"),
        ("Start Date", "{no change}"),
        ("Finish Date", "{no change}"),
        ("Meter Serial Number", "A Mop Contract"),
        ("Correction Factor", "{no change}"),
        ("Unit", "{no change}"),
        ("Supplier Contract Name", "{no change}"),
        ("Account", "{no change}"),
        ("Reading Frequency", "{no change}"),
        ("AQ", "{no change}"),
        ("SOQ", "{no change}"),
    ]

    assert args == expected_args


def test_general_import_g_supply_insert(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site_code = "22488"
    Site.insert(sess, site_code, "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone_code = "EA1"
    g_ldz.insert_g_exit_zone(sess, g_exit_zone_code)
    insert_g_units(sess)
    g_unit_code = "M3"
    GUnit.get_by_code(sess, g_unit_code)
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "non core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    g_contract_name = "Fusion 2020"
    GContract.insert_supplier(sess, g_contract_name, "", {}, vf, None, {})
    insert_g_reading_frequencies(sess)
    g_reading_frequency_code = "M"
    GReadingFrequency.get_by_code(sess, g_reading_frequency_code)
    mprn = "87614362"
    msn = "hgeu8rhg"
    aq = "10"
    soq = "20"
    g_supply_name = "1"
    start_date = "2019-09-08 00:00"
    finish_date = ""
    correction_factor = "1"
    account = "acc1"

    action = "insert"
    vals = [
        site_code,
        mprn,
        g_supply_name,
        g_exit_zone_code,
        start_date,
        finish_date,
        msn,
        correction_factor,
        g_unit_code,
        g_contract_name,
        account,
        g_reading_frequency_code,
        aq,
        soq,
    ]
    args = []
    general_import_g_supply(sess, action, vals, args)

    expected_args = [
        ("Site Code", site_code),
        ("MPRN", mprn),
        ("Supply Name", g_supply_name),
        ("Exit Zone", g_exit_zone_code),
        ("Start Date", start_date),
        ("Finish Date", finish_date),
        ("Meter Serial Number", msn),
        ("Correction Factor", correction_factor),
        ("Unit of Measurement", g_unit_code),
        ("Supplier Contract", g_contract_name),
        ("Account", account),
        ("Reading Frequency", g_reading_frequency_code),
        ("AQ", aq),
        ("SOQ", soq),
    ]

    assert args == expected_args


def test_parse_breakdown():
    breakdown_str = '{"date": 2009-05-12T03:00:00Z}'
    expected = {"date": utc_datetime(2009, 5, 12, 3)}
    actual = _parse_breakdown(breakdown_str)
    assert actual == expected


def test_general_import_era_insert(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
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
    exp_supplier_contract = Contract.insert_supplier(
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
        sess, "521", "Export (HV)", voltage_level, False, False, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
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

    sess.commit()

    action = "insert"
    vals = [
        "22 7867 6232 781",
        "2020-10-01 00:00",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "Fusion Supplier 2000",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
    ]
    args = []
    general_import_era(sess, action, vals, args)


def test_general_import_era_insert_nhh(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
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
    pc = Pc.insert(sess, "01", "nhh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    exp_supplier_contract = Contract.insert_supplier(
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
        sess, "521", "Export (HV)", voltage_level, False, False, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    ssc_code = "0393"
    ssc = Ssc.insert(sess, ssc_code, "All", True, vf, None)

    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, vf, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, vf, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, vf, None)
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
        ssc_code,
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

    sess.commit()

    action = "insert"
    vals = [
        "22 7867 6232 781",
        "2020-10-01 00:00",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
    ]
    args = []
    general_import_era(sess, action, vals, args)


def test_general_import_era_update_hh(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
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
    pc = Pc.insert(sess, "00", "HH", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    exp_supplier_contract = Contract.insert_supplier(
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
        sess, "521", "Export (HV)", voltage_level, False, False, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
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
    action = "update"
    vals = [
        "2278676232781",
        "2019-09-08 00:00",
        "{no change}",
        "{no change}",
        "Fusion",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
    ]
    args = []
    general_import_era(sess, action, vals, args)


def test_general_import_era_update_nhh(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
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
    pc = Pc.insert(sess, "01", "nhh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    exp_supplier_contract = Contract.insert_supplier(
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
        sess, "521", "Export (HV)", voltage_level, False, False, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    ssc_code = "0393"
    ssc = Ssc.insert(sess, ssc_code, "All", True, vf, None)

    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, vf, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, vf, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, vf, None)
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
        ssc_code,
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
    action = "update"
    vals = [
        "2278676232781",
        "2019-09-08 00:00",
        "{no change}",
        "{no change}",
        "Fusion",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
        "{no change}",
    ]
    args = []
    general_import_era(sess, action, vals, args)


def test_general_import_llfc_insert(sess):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "27"
    )
    insert_voltage_levels(sess)
    sess.commit()

    action = "insert"
    vals = [
        "27",
        "A1A",
        "LV:LV A Agg Band 0",
        "LV",
        "False",
        "True",
        "2020-10-21 00:00",
        "",
    ]
    args = []
    general_import_llfc(sess, action, vals, args)


def test_general_import_llfc_update(sess):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "10"
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    dno.insert_llfc(
        sess,
        "328",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        to_utc(ct_datetime(2020, 4, 1)),
        None,
    )
    sess.commit()

    action = "update"
    vals = [
        "10",
        "328",
        "2020-04-01 00:00",
        "Reserved EHV 33kV - Import",
        "HV",
        "False",
        "True",
        "",
    ]
    args = []
    general_import_llfc(sess, action, vals, args)


def test_general_import_llfc_update_is_import_no_change(sess):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "10"
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    dno.insert_llfc(
        sess,
        "328",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        to_utc(ct_datetime(2020, 4, 1)),
        None,
    )
    sess.commit()

    action = "update"
    vals = [
        "10",
        "328",
        "2020-04-01 00:00",
        "Reserved EHV 33kV - Import",
        "HV",
        "False",
        "{no change}",
        "",
    ]
    args = []
    general_import_llfc(sess, action, vals, args)


def test_general_import_llfc_update_valid_to_no_change(sess):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "10"
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    dno.insert_llfc(
        sess,
        "328",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        to_utc(ct_datetime(2020, 4, 1)),
        None,
    )
    sess.commit()

    action = "update"
    vals = [
        "10",
        "328",
        "2020-04-01 00:00",
        "Reserved EHV 33kV - Import",
        "HV",
        "False",
        "{no change}",
        "{no change}",
    ]
    args = []
    general_import_llfc(sess, action, vals, args)


def test_general_import_site_update(sess):
    site_code = "CI017"
    site_name = "Water Works"
    Site.insert(sess, site_code, site_name)
    sess.commit()

    action = "update"
    vals = [
        site_code,
        "{no change}",
        "{no change}",
    ]
    args = []
    general_import_site(sess, action, vals, args)

    site = sess.scalars(select(Site)).one()
    assert site.code == site_code
    assert site.name == site_name


def test_general_import_supply_insert_HH(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site_code = "CI017"
    Site.insert(sess, site_code, "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    mop_contract_name = "Fusion"
    Contract.insert_mop(sess, mop_contract_name, participant, "", {}, vf, None, {})
    dc_contract_name = "Fusion DC 2000"
    Contract.insert_dc(sess, dc_contract_name, participant, "", {}, vf, None, {})
    Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop_code = "5"
    Cop.get_by_code(sess, cop_code)
    insert_comms(sess)
    comm_code = "GSM"
    Comm.get_by_code(sess, comm_code)
    supplier_contract_name = "Fusion 2000"
    Contract.insert_supplier(
        sess, supplier_contract_name, participant, "", {}, vf, None, {}
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", vf, None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", vf, None)
    mtc_code = "845"
    mtc = Mtc.insert(sess, mtc_code, False, True, vf, None)
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
    llfc_code = "521"
    llfc = dno.insert_llfc(sess, llfc_code, "Imp", voltage_level, False, True, vf, None)
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source_code = "grid"
    Source.get_by_code(sess, source_code)
    insert_energisation_statuses(sess)
    energisation_status_code = "E"
    EnergisationStatus.get_by_code(sess, energisation_status_code)
    gsp_group_code = "_L"
    GspGroup.insert(sess, gsp_group_code, "South Western")
    insert_dtc_meter_types(sess)
    dtc_meter_type_code = "H"
    supply_name = "Bob"
    start_date = vf
    msn = "khgsa;kh"

    sess.commit()

    action = "insert"
    vals = [
        site_code,
        source_code,
        "",
        supply_name,
        gsp_group_code,
        hh_format(start_date),
        "",
        mop_contract_name,
        "22 7867 6232 781",
        dc_contract_name,
        "22 7867 6232 781",
        msn,
        "22",
        "00",
        mtc_code,
        cop_code,
        comm_code,
        "",
        energisation_status_code,
        dtc_meter_type_code,
        "22 7867 6232 781",
        llfc_code,
        "0",
        supplier_contract_name,
        "22 7867 6232 781",
    ]
    args = []
    general_import_supply(sess, action, vals, args)


def test_general_import_supply_insert_NHH(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site_code = "CI017"
    Site.insert(sess, site_code, "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    mop_contract_name = "Fusion"
    Contract.insert_mop(sess, mop_contract_name, participant, "", {}, vf, None, {})
    dc_contract_name = "Fusion DC 2000"
    Contract.insert_dc(sess, dc_contract_name, participant, "", {}, vf, None, {})
    pc_code = "01"
    pc = Pc.insert(sess, pc_code, "nhh", vf, None)
    insert_cops(sess)
    cop_code = "5"
    Cop.get_by_code(sess, cop_code)
    insert_comms(sess)
    comm_code = "GSM"
    Comm.get_by_code(sess, comm_code)
    supplier_contract_name = "Fusion 2000"
    Contract.insert_supplier(
        sess, supplier_contract_name, participant, "", {}, vf, None, {}
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", vf, None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", vf, None)
    mtc_code = "845"
    mtc = Mtc.insert(sess, mtc_code, False, True, vf, None)
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
    llfc_code = "521"
    llfc = dno.insert_llfc(sess, llfc_code, "Imp", voltage_level, False, True, vf, None)
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source_code = "grid"
    Source.get_by_code(sess, source_code)
    insert_energisation_statuses(sess)
    energisation_status_code = "E"
    EnergisationStatus.get_by_code(sess, energisation_status_code)
    gsp_group_code = "_L"
    GspGroup.insert(sess, gsp_group_code, "South Western")
    insert_dtc_meter_types(sess)
    dtc_meter_type_code = "N"
    supply_name = "Bob"
    start_date = vf
    msn = "khgsa;kh"
    ssc_code = "0393"
    ssc = Ssc.insert(sess, ssc_code, "All", True, vf, None)

    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, vf, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, vf, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, vf, None)
    sess.commit()

    action = "insert"
    vals = [
        site_code,
        source_code,
        "",
        supply_name,
        gsp_group_code,
        hh_format(start_date),
        "",
        mop_contract_name,
        "22 7867 6232 781",
        dc_contract_name,
        "22 7867 6232 781",
        msn,
        "22",
        pc_code,
        mtc_code,
        cop_code,
        comm_code,
        ssc_code,
        energisation_status_code,
        dtc_meter_type_code,
        "22 7867 6232 781",
        llfc_code,
        "0",
        supplier_contract_name,
        "22 7867 6232 781",
    ]
    args = []
    general_import_supply(sess, action, vals, args)
