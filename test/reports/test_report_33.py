import csv
from io import StringIO

from utils import match_tables

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
    User,
    UserRole,
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)

from chellow.reports.report_33 import _process, content
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_content(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
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
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    supply_id = supply.id

    sess.commit()
    f = StringIO()
    mocker.patch("chellow.reports.report_33.open_file", return_value=f)
    date = utc_datetime(2024, 1, 1)
    mpan_cores = None
    content(user_id, date, supply_id, mpan_cores)


def test_process_2010(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
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
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
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
        {
            "tariffs": {"510": {"day-gbp-per-kwh": 1, "night-gbp-per-kwh": 1}},
            "lafs": {"hv": {"other": 1}},
        },
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
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
        utc_datetime(1996, 1, 1),
        None,
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

    sess.commit()
    f = StringIO()
    mocker.patch("chellow.reports.report_33.open_file", return_value=f)
    date = utc_datetime(2010, 1, 1)
    supply_id = supply.id
    mpan_cores = None
    _process(sess, f, date, supply_id, mpan_cores)
    f.seek(0)
    actual = list(csv.reader(f))
    expected = [
        [
            "Date",
            "Import MPAN Core",
            "Export MPAN Core",
            "Physical Site Id",
            "Physical Site Name",
            "Other Site Ids",
            "Other Site Names",
            "Supply Id",
            "Source",
            "Generator Type",
            "GSP Group",
            "DNO Name",
            "Voltage Level",
            "Is Substations",
            "Metering Type",
            "Mandatory HH",
            "PC",
            "MTC",
            "CoP",
            "Comms Type",
            "SSC Code",
            "SSC Description",
            "Energisation Status",
            "Number Of Registers",
            "MOP Contract",
            "Mop Account",
            "DC Contract",
            "DC Account",
            "Meter Serial Number",
            "Meter Installation Date",
            "Latest Normal Meter Read Date",
            "Latest Normal Meter Read Type",
            "Latest DC Bill Date",
            "Latest MOP Bill Date",
            "Supply Start Date",
            "Supply Finish Date",
            "DTC Meter Type",
            "tnuos_band",
            "Import ACTIVE?",
            "Import REACTIVE_IMPORT?",
            "Import REACTIVE_EXPORT?",
            "Export ACTIVE?",
            "Export REACTIVE_IMPORT?",
            "Export REACTIVE_EXPORT?",
            "Import Agreed Supply Capacity (kVA)",
            "Import LLFC Code",
            "Import LLFC Description",
            "Import Supplier Contract",
            "Import Supplier Account",
            "Import Mandatory kW",
            "Latest Import Supplier Bill Date",
            "Export Agreed Supply Capacity (kVA)",
            "Export LLFC Code",
            "Export LLFC Description",
            "Export Supplier Contract",
            "Export Supplier Account",
            "Export Mandatory kW",
            "Latest Export Supplier Bill Date",
        ],
        [
            "2010-01-01 00:00",
            "22 7867 6232 781",
            "",
            "CI017",
            "Water Works",
            "",
            "",
            "1",
            "net",
            "",
            "_L",
            "22",
            "HV",
            "False",
            "hh",
            "no",
            "00",
            "845",
            "5",
            "GSM",
            "",
            "",
            "E",
            "",
            "Fusion",
            "773",
            "Fusion DC 2000",
            "ghyy3",
            "hgjeyhuw",
            "2000-01-01 00:00",
            "hh",
            "",
            "",
            "",
            "2000-01-01 00:00",
            "",
            "H",
            "",
            "false",
            "false",
            "false",
            "false",
            "false",
            "false",
            "361",
            "510",
            "PC 5-8 & HH HV",
            "Fusion Supplier 2000",
            "7748",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
    ]
    match_tables(expected, actual)


def test_process_2024(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
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
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
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
        {
            "_L": {
                "bands": {},
                "tariffs": {
                    "510": {
                        "description": "HV Site Specific Band 1",
                        "gbp-per-kvarh": 1,
                        "green-gbp-per-kwh": 1,
                    }
                },
            },
        },
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
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
        utc_datetime(1996, 1, 1),
        None,
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

    sess.commit()
    f = StringIO()
    mocker.patch("chellow.reports.report_33.open_file", return_value=f)
    date = utc_datetime(2024, 1, 1)
    supply_id = supply.id
    mpan_cores = None
    _process(sess, f, date, supply_id, mpan_cores)
    f.seek(0)
    actual = list(csv.reader(f))
    expected = [
        [
            "Date",
            "Import MPAN Core",
            "Export MPAN Core",
            "Physical Site Id",
            "Physical Site Name",
            "Other Site Ids",
            "Other Site Names",
            "Supply Id",
            "Source",
            "Generator Type",
            "GSP Group",
            "DNO Name",
            "Voltage Level",
            "Is Substations",
            "Metering Type",
            "Mandatory HH",
            "PC",
            "MTC",
            "CoP",
            "Comms Type",
            "SSC Code",
            "SSC Description",
            "Energisation Status",
            "Number Of Registers",
            "MOP Contract",
            "Mop Account",
            "DC Contract",
            "DC Account",
            "Meter Serial Number",
            "Meter Installation Date",
            "Latest Normal Meter Read Date",
            "Latest Normal Meter Read Type",
            "Latest DC Bill Date",
            "Latest MOP Bill Date",
            "Supply Start Date",
            "Supply Finish Date",
            "DTC Meter Type",
            "tnuos_band",
            "Import ACTIVE?",
            "Import REACTIVE_IMPORT?",
            "Import REACTIVE_EXPORT?",
            "Export ACTIVE?",
            "Export REACTIVE_IMPORT?",
            "Export REACTIVE_EXPORT?",
            "Import Agreed Supply Capacity (kVA)",
            "Import LLFC Code",
            "Import LLFC Description",
            "Import Supplier Contract",
            "Import Supplier Account",
            "Import Mandatory kW",
            "Latest Import Supplier Bill Date",
            "Export Agreed Supply Capacity (kVA)",
            "Export LLFC Code",
            "Export LLFC Description",
            "Export Supplier Contract",
            "Export Supplier Account",
            "Export Mandatory kW",
            "Latest Export Supplier Bill Date",
        ],
        [
            "2024-01-01 00:00",
            "22 7867 6232 781",
            "",
            "CI017",
            "Water Works",
            "",
            "",
            "1",
            "net",
            "",
            "_L",
            "22",
            "HV",
            "False",
            "hh",
            "no",
            "00",
            "845",
            "5",
            "GSM",
            "",
            "",
            "E",
            "",
            "Fusion",
            "773",
            "Fusion DC 2000",
            "ghyy3",
            "hgjeyhuw",
            "2000-01-01 00:00",
            "hh",
            "",
            "",
            "",
            "2000-01-01 00:00",
            "",
            "H",
            "HV1",
            "false",
            "false",
            "false",
            "false",
            "false",
            "false",
            "361",
            "510",
            "PC 5-8 & HH HV",
            "Fusion Supplier 2000",
            "7748",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
    ]
    match_tables(expected, actual)
