from decimal import Decimal

import chellow.general_import
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
from chellow.utils import ct_datetime, hh_format, to_utc, utc_datetime


def test_general_import_g_batch(mocker):
    sess = mocker.Mock()
    action = "insert"
    vals = ["CH4U", "batch 8883", "Apr 2019"]
    args = []
    chellow.general_import.general_import_g_batch(sess, action, vals, args)


def test_general_import_g_bill(mocker):
    c = mocker.patch("chellow.general_import.GContract", autospec=True)
    c.get_supplier_by_name.return_value = chellow.general_import.GContract(
        False, "CH4U", "{}", "{}"
    )

    mocker.patch("chellow.models.GBatch", autospec=True)
    batch = chellow.models.GBatch(1, 2, 3, 4)
    batch.g_contract = chellow.general_import.GContract(False, "CH4U", "{}", "{}")
    c.get_g_batch_by_reference.return_value = batch

    sess = mocker.Mock()
    action = "insert"
    vals = [
        "CH4U",
        "batch 8883",
        "759288812",
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
    chellow.general_import.general_import_g_bill(sess, action, vals, args)


def test_general_import_g_bill_reads(mocker):
    c = mocker.patch("chellow.general_import.GContract", autospec=True)
    contract = chellow.general_import.GContract(False, "CH4U", "{}", "{}")
    c.get_supplier_by_name.return_value = contract

    mocker.patch("chellow.models.GBatch", autospec=True)
    batch = chellow.models.GBatch("CH4U", "{}", "{}", 4)
    contract.get_g_batch_by_reference.return_value = batch

    mocker.patch("chellow.models.GBill", autospec=True)
    bill = chellow.models.GBill(
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
        mocker.Mock(),
    )
    batch.insert_g_bill.return_value = bill

    sess = mocker.Mock()
    msn = "88hgkdshjf"
    g_unit_code = "M3"
    g_unit_class = mocker.patch("chellow.general_import.GUnit", autospec=True)
    g_unit = chellow.general_import.GUnit(g_unit_code, "", 1)
    g_unit_class.get_by_code.return_value = g_unit
    correction_factor = Decimal("1")
    calorific_value = Decimal("39")
    prev_value = Decimal("988")
    prev_date = utc_datetime(2019, 10, 1)
    prev_type_code = "E"
    pres_value = Decimal("1200")
    pres_date = utc_datetime(2019, 10, 31, 23, 30)
    pres_type_code = "A"

    g_read_type_class = mocker.patch("chellow.general_import.GReadType", autospec=True)
    prev_type = chellow.general_import.GReadType(prev_type_code, "")
    pres_type = chellow.general_import.GReadType(pres_type_code, "")
    g_read_type_class.get_by_code.side_effect = [prev_type, pres_type]

    action = "insert"
    vals = [
        "CH4U",
        "batch 8883",
        "759288812",
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
        str(correction_factor),
        str(calorific_value),
        hh_format(prev_date),
        str(prev_value),
        prev_type_code,
        hh_format(pres_date),
        str(pres_value),
        pres_type_code,
    ]
    args = []
    chellow.general_import.general_import_g_bill(sess, action, vals, args)
    bill.insert_g_read.assert_called_with(
        sess,
        msn,
        g_unit,
        correction_factor,
        calorific_value,
        prev_value,
        prev_date,
        prev_type,
        pres_value,
        pres_date,
        pres_type,
    )


def test_parse_breakdown():
    breakdown_str = '{"date": 2009-05-12T03:00:00Z}'
    expected = {"date": utc_datetime(2009, 5, 12, 3)}
    actual = chellow.general_import._parse_breakdown(breakdown_str)
    assert actual == expected


def test_general_import_era_insert(sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, valid_from, None, bank_holiday_rate_script
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
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    exp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, valid_from, None, {}
    )
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
        valid_from,
        None,
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "521", "Export (HV)", voltage_level, False, False, valid_from, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
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
    chellow.general_import.general_import_era(sess, action, vals, args)


def test_general_import_era_update(mocker):
    MockSupply = mocker.patch("chellow.general_import.Supply", autospec=True)

    mock_supply = mocker.Mock()

    MockSupply.get_by_mpan_core.return_value = mock_supply

    mock_era = mocker.Mock()
    mock_era.properties = "{}"

    mock_supply.find_era_at.return_value = mock_era

    sess = mocker.Mock()
    action = "update"
    vals = [
        "CH4U",
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
    chellow.general_import.general_import_era(sess, action, vals, args)


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
    chellow.general_import.general_import_llfc(sess, action, vals, args)


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
    chellow.general_import.general_import_llfc(sess, action, vals, args)


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
    chellow.general_import.general_import_llfc(sess, action, vals, args)


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
    chellow.general_import.general_import_llfc(sess, action, vals, args)
