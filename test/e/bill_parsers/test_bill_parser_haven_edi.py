from decimal import Decimal
from io import BytesIO


from chellow.e.bill_parsers.haven_edi import (
    BillElement,
    Parser,
    _process_BTL,
    _process_CCD1,
    _process_CCD3,
    _process_CLO,
    _process_MAN,
    _process_MHD,
    _process_MTR,
)
from chellow.models import (
    Comm,
    Contract,
    Cop,
    DtcMeterType,
    EnergisationStatus,
    GspGroup,
    MarketRole,
    MeasurementRequirement,
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
    Tpr,
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_process_BTL_zeroes(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
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
    pc = Pc.insert(sess, "03", "nhh", vf, None)
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
        "",
        False,
        False,
        meter_type,
        meter_payment_type,
        2,
        vf,
        None,
    )
    ssc = Ssc.insert(sess, "0154", "All", True, vf, None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, vf, None)
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, vf, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
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
        "0154",
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
    elements = {
        "UVLT": ["0"],
        "UTVA": ["0"],
        "TBTL": ["0"],
    }
    headers = {
        "errors": [],
        "issue_date": to_utc(ct_datetime(2024, 1, 1)),
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "mpan_core": "22 7867 6232 781",
        "reads": [],
        "breakdown": {},
        "bill_elements": [
            BillElement(
                gbp=Decimal("10.31"),
                rate=Decimal("0.0001"),
                cons=Decimal("113"),
                titles=None,
                desc="Night",
            )
        ],
        "sess": sess,
        "reference": "ref 01",
        "kwh": Decimal("0"),
        "account": "acc",
        "bill_type_code": "N",
    }
    bill = _process_BTL(elements, headers)
    expected_headers = {
        "errors": [],
        "issue_date": to_utc(ct_datetime(2024, 1, 1)),
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "mpan_core": "22 7867 6232 781",
        "breakdown": {},
        "reads": [],
        "sess": sess,
        "bill_elements": [
            BillElement(
                gbp=Decimal("10.31"),
                rate=Decimal("0.0001"),
                cons=Decimal("113"),
                titles=None,
                desc="Night",
            ),
        ],
        "reference": "ref 01",
        "kwh": Decimal("0"),
        "account": "acc",
        "bill_type_code": "N",
    }
    assert headers == expected_headers
    assert str(bill["net"]) == "0.00"
    expected_bill = {
        "breakdown": {},
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "gross": Decimal("0.00"),
        "issue_date": to_utc(ct_datetime(2024, 1, 1)),
        "mpan_core": "22 7867 6232 781",
        "net": Decimal("0.00"),
        "reads": [],
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "vat": Decimal("0.00"),
        "elements": [
            {
                "breakdown": {
                    "kwh": Decimal("113"),
                    "rate": {Decimal("0.0001")},
                },
                "start_date": to_utc(ct_datetime(2025, 1, 1)),
                "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
                "name": "00221",
                "net": Decimal("10.31"),
            },
        ],
        "reference": "ref 01",
        "kwh": Decimal("0"),
        "account": "acc",
        "bill_type_code": "N",
    }
    assert bill == expected_bill


def test_process_BTL_non_zeroes(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
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
    pc = Pc.insert(sess, "03", "nhh", vf, None)
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
        "",
        False,
        False,
        meter_type,
        meter_payment_type,
        2,
        vf,
        None,
    )
    ssc = Ssc.insert(sess, "0154", "All", True, vf, None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, vf, None)
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, vf, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
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
        "0154",
        energisation_status,
        dtc_meter_type,
        "22 7368 2392 188",
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
    elements = {
        "UVLT": ["11"],
        "UTVA": ["12"],
        "TBTL": ["10"],
    }
    headers = {
        "errors": [],
        "issue_date": to_utc(ct_datetime(2024, 1, 1)),
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "elements": [],
        "mpan_core": "22 7368 2392 188",
        "reads": [],
        "breakdown": {},
        "sess": sess,
        "bill_elements": [
            BillElement(
                gbp=Decimal("10.31"),
                rate=Decimal("0.0001"),
                cons=Decimal("113"),
                titles=None,
                desc="Night",
            ),
        ],
        "sess": sess,
        "reference": "ref 01",
        "kwh": Decimal("0"),
        "bill_type_code": "N",
        "account": "acc",
    }
    bill = _process_BTL(elements, headers)
    expected_headers = {
        "errors": [],
        "issue_date": to_utc(ct_datetime(2024, 1, 1)),
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "elements": [],
        "mpan_core": "22 7368 2392 188",
        "reads": [],
        "breakdown": {},
        "bill_elements": [
            BillElement(
                gbp=Decimal("10.31"),
                rate=Decimal("0.0001"),
                cons=Decimal("113"),
                titles=None,
                desc="Night",
            ),
        ],
        "sess": sess,
        "reference": "ref 01",
        "kwh": Decimal("0"),
        "bill_type_code": "N",
        "account": "acc",
    }
    expected_bill = {
        "kwh": Decimal("0"),
        "net": Decimal("0.11"),
        "vat": Decimal("0.12"),
        "gross": Decimal("0.10"),
        "breakdown": {},
        "elements": [
            {
                "breakdown": {
                    "kwh": Decimal("113"),
                    "rate": {Decimal("0.0001")},
                },
                "name": "00221",
                "net": Decimal("10.31"),
                "start_date": to_utc(ct_datetime(2025, 1, 1)),
                "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
            }
        ],
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "issue_date": to_utc(ct_datetime(2024, 1, 1)),
        "mpan_core": "22 7368 2392 188",
        "reads": [],
        "reference": "ref 01",
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "bill_type_code": "N",
        "account": "acc",
    }
    assert headers == expected_headers
    assert bill == expected_bill


def test_process_MTR_UTLHDR(mocker):
    elements = {}
    headers = {"message_type": "UTLHDR", "breakdown": {}}
    bill = _process_MTR(elements, headers)
    assert bill is None


def test_process_MTR_UTLBIL(mocker):
    elements = {}
    headers = {}
    expected_headers = {}
    _process_MTR(elements, headers)
    assert headers == expected_headers


def test_process_BTL_multiple_charges_one_tpr(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
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
    pc = Pc.insert(sess, "03", "nhh", vf, None)
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
        "",
        False,
        False,
        meter_type,
        meter_payment_type,
        2,
        vf,
        None,
    )
    ssc = Ssc.insert(sess, "0244", "All", True, vf, None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, vf, None)
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, vf, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
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
        "0244",
        energisation_status,
        dtc_meter_type,
        "22 7368 2392 188",
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
    gbp = "10.31"
    cons = "113"
    elements = {
        "UVLT": ["11"],
        "UTVA": ["12"],
        "TBTL": ["10"],
    }
    headers = {
        "sess": sess,
        "message_type": "UTLBIL",
        "breakdown": {},
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            ),
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            ),
        ],
        "mpan_core": "22 7368 2392 188",
        "kwh": 8,
        "reference": "a",
        "issue_date": to_utc(ct_datetime(2025, 1, 1)),
        "account": "acc",
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "net": 0,
        "vat": 0,
        "gross": 0,
        "reads": [
            {
                "msn": "hgkh",
                "mpan": "      ",
                "coefficient": Decimal("0.00001"),
                "units": "kWh",
                "tpr_code": "Day",
                "prev_date": utc_datetime(2020, 3, 31, 22, 30),
                "prev_value": Decimal("1"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2020, 3, 1, 23, 30),
                "pres_value": Decimal("0"),
                "pres_type_code": "N",
            },
        ],
        "bill_type_code": "N",
        "errors": [],
    }
    bill = _process_BTL(elements, headers)
    expected_headers = {
        "mpan_core": "22 7368 2392 188",
        "errors": [],
        "sess": sess,
        "message_type": "UTLBIL",
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            ),
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            ),
        ],
        "kwh": 8,
        "reference": "a",
        "issue_date": to_utc(ct_datetime(2025, 1, 1)),
        "account": "acc",
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "net": 0,
        "vat": 0,
        "gross": 0,
        "breakdown": {},
        "reads": [
            {
                "msn": "hgkh",
                "mpan": "      ",
                "coefficient": Decimal("0.00001"),
                "units": "kWh",
                "tpr_code": "00040",
                "prev_date": utc_datetime(2020, 3, 31, 22, 30),
                "prev_value": Decimal("1"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2020, 3, 1, 23, 30),
                "pres_value": Decimal("0"),
                "pres_type_code": "N",
            }
        ],
        "bill_type_code": "N",
    }
    assert headers == expected_headers
    expected_bill = {
        "breakdown": {},
        "elements": [
            {
                "breakdown": {
                    "kwh": Decimal("113"),
                    "rate": {Decimal("0.0001")},
                },
                "start_date": to_utc(ct_datetime(2025, 1, 1)),
                "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
                "name": "00206",
                "net": Decimal("10.31"),
            },
            {
                "breakdown": {
                    "kwh": Decimal("113"),
                    "rate": {Decimal("0.0001")},
                },
                "start_date": to_utc(ct_datetime(2025, 1, 1)),
                "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
                "name": "00206",
                "net": Decimal("10.31"),
            },
        ],
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "gross": Decimal("0.10"),
        "issue_date": to_utc(ct_datetime(2025, 1, 1)),
        "mpan_core": "22 7368 2392 188",
        "net": Decimal("0.11"),
        "reads": [
            {
                "coefficient": Decimal("0.00001"),
                "mpan": "      ",
                "msn": "hgkh",
                "pres_date": to_utc(ct_datetime(2020, 3, 1, 23, 30)),
                "pres_type_code": "N",
                "pres_value": Decimal("0"),
                "prev_date": to_utc(ct_datetime(2020, 3, 31, 23, 30)),
                "prev_type_code": "N",
                "prev_value": Decimal("1"),
                "tpr_code": "00040",
                "units": "kWh",
            },
        ],
        "vat": Decimal("0.12"),
        "kwh": 8,
        "reference": "a",
        "account": "acc",
        "bill_type_code": "N",
    }
    assert bill == expected_bill


def test_process_BTL_unmetered(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
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
        "",
        False,
        False,
        meter_type,
        meter_payment_type,
        2,
        vf,
        None,
    )
    tpr = Tpr.insert(sess, "00001", True, True)
    ssc = Ssc.insert(sess, "0393", "All", True, vf, None)
    MeasurementRequirement.insert(sess, ssc, tpr)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, vf, None)
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, vf, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    site.insert_e_supply(
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
        "22 7368 2392 188",
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
    gbp = "10.31"
    cons = "113"
    elements = {
        "UVLT": ["11"],
        "UTVA": ["12"],
        "TBTL": ["10"],
    }
    headers = {
        "errors": [],
        "sess": sess,
        "breakdown": {},
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Energy Charges",
            )
        ],
        "mpan_core": "22 7368 2392 188",
        "kwh": 8,
        "reference": "a",
        "issue_date": to_utc(ct_datetime(2025, 1, 1)),
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "account": "acc",
        "reads": [],
        "bill_type_code": "N",
    }
    bill = _process_BTL(elements, headers)
    expected_headers = {
        "errors": [],
        "sess": sess,
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Energy Charges",
            )
        ],
        "kwh": 8,
        "reference": "a",
        "mpan_core": "22 7368 2392 188",
        "account": "acc",
        "issue_date": to_utc(ct_datetime(2025, 1, 1)),
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "breakdown": {},
        "reads": [],
        "bill_type_code": "N",
    }
    assert headers == expected_headers
    expected_bill = {
        "breakdown": {},
        "kwh": 8,
        "reference": "a",
        "mpan_core": "22 7368 2392 188",
        "account": "acc",
        "issue_date": to_utc(ct_datetime(2025, 1, 1)),
        "start_date": to_utc(ct_datetime(2025, 1, 1)),
        "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
        "net": Decimal("0.11"),
        "vat": Decimal("0.12"),
        "gross": Decimal("0.10"),
        "elements": [
            {
                "name": "00001",
                "net": Decimal("10.31"),
                "breakdown": {
                    "rate": {Decimal("0.0001")},
                    "kwh": Decimal("113"),
                },
                "start_date": to_utc(ct_datetime(2025, 1, 1)),
                "finish_date": to_utc(ct_datetime(2025, 1, 31, 23, 30)),
            }
        ],
        "reads": [],
        "bill_type_code": "N",
    }
    assert bill == expected_bill


def test_process_MAN(mocker):
    elements = {
        "MADN": ["20", "0000000000", "6", "00", "001", "002"],
    }

    headers = {}
    _process_MAN(elements, headers)
    expected_headers = {"mpan_core": "20 0000 0000 006"}
    assert headers == expected_headers


def test_process_MHD(mocker):
    message_type = "UTLBIL"
    elements = {"TYPE": [message_type]}

    sess = mocker.Mock()
    headers = {"sess": sess}
    _process_MHD(elements, headers)
    expected_headers = {
        "message_type": message_type,
        "reads": [],
        "errors": [],
        "bill_elements": [],
        "breakdown": {"raw-lines": []},
        "sess": sess,
        "kwh": Decimal("0"),
    }
    assert headers == expected_headers
    assert type(headers["breakdown"]) is type(expected_headers)


def test_process_CCD3(mocker):
    elements = {
        "CCDE": ["3", "", "NRG"],
        "TCOD": ["NIGHT", "Night"],
        "TMOD": ["453043"],
        "CONS": [[]],
        "BPRI": ["10"],
    }

    headers = {
        "bill_elements": [],
        "kwh": Decimal("0"),
    }

    _process_CCD3(elements, headers)

    expected_headers = {
        "kwh": Decimal("0"),
        "bill_elements": [
            BillElement(
                gbp=Decimal("0.00"),
                rate=Decimal("0.0001"),
                cons=Decimal("0"),
                titles=None,
                desc="Night",
            ),
        ],
    }
    assert headers == expected_headers


def test_process_CCD_1(mocker):
    msn = "hgkh"

    elements = {
        "CCDE": ["1", "", "NRG"],
        "TCOD": ["NIGHT", "Night"],
        "TMOD": ["453043"],
        "MTNR": [msn],
        "CONS": [[]],
        "BPRI": ["10"],
        "PRDT": ["200301"],
        "PVDT": ["200331"],
        "MLOC": [""],
        "PRRD": ["0", "00", "1", "00"],
        "ADJF": ["", "1"],
    }

    headers = {
        "reads": [],
    }

    _process_CCD1(elements, headers)

    expected_headers = {
        "reads": [
            {
                "msn": msn,
                "mpan": "      ",
                "coefficient": Decimal("0.00001"),
                "units": "kWh",
                "tpr_code": "453043",
                "prev_date": utc_datetime(2020, 3, 31, 22, 30),
                "prev_value": Decimal("1"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2020, 3, 1, 23, 30),
                "pres_value": Decimal("0"),
                "pres_type_code": "N",
            }
        ]
    }
    assert headers == expected_headers


def test_process_CLO(mocker):
    account = "accnt"

    elements = {"CLOC": [account, ""]}

    headers = {}

    _process_CLO(elements, headers)

    expected_headers = {
        "account": "",
    }
    assert headers == expected_headers


def test_make_raw_bills(sess):
    file_lines = [
        "MHD=2+UTLBIL:3'",
        "MTR=6'",
    ]
    f = BytesIO(b"\n".join(n.encode("utf8") for n in file_lines))

    parser = Parser(f)
    parser.make_raw_bills()


def test_Parser(mocker, sess):
    file_lines = [
        "STX=ANA:1+3832776:Fusion PLC+771:Fusion PLC+130214:090426+8472+"
        "PASSWORD+UTLHDR'",
        "END=251'",
    ]
    f = BytesIO(b"\n".join(n.encode("utf8") for n in file_lines))
    parser = Parser(f)
    parser.make_raw_bills()
