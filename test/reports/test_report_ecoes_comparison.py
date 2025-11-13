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
    ReportRun,
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
from chellow.reports.report_ecoes_comparison import _process
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_process(mocker, sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
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
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)
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
        utc_datetime(1996, 1, 1),
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
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
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

    site.insert_e_supply(
        sess,
        source,
        None,
        "Dave",
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
        None,
        energisation_status,
        dtc_meter_type,
        "22 7868 6232 789",
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
    report_run = ReportRun.insert(
        sess,
        "ecoes_comparison",
        None,
        "ecoes_comparison",
        {},
    )

    sess.commit()
    f = StringIO()
    ecoes_lines = [
        "titles",
        ",".join(
            (
                "2278676232781",
                "address-line-1",
                "address-line-2",
                "address-line-3",
                "address-line-4",
                "address-line-5",
                "address-line-6",
                "address-line-7",
                "address-line-8",
                "address-line-9",
                "post-code",
                "supplier",
                "12/10/2022",
                "mtc",
                "12/10/2022",
                "llfc",
                "12/10/2022",
                "pc",
                "",
                "measurement-class",
                "energisation-status",
                "da",
                "dc",
                "mop",
                "12/10/2022",
                "gsp-group",
                "12/10/2022",
                "dno",
                "msn",
                "12/10/2022",
                "meter-type",
                "map-id",
            ),
        ),
        ",".join(
            (
                "2278686232789",
                "address-line-1",
                "address-line-2",
                "address-line-3",
                "address-line-4",
                "address-line-5",
                "address-line-6",
                "address-line-7",
                "address-line-8",
                "address-line-9",
                "post-code",
                "supplier",
                "12/10/2022",
                "mtc",
                "12/10/2022",
                "llfc",
                "12/10/2022",
                "pc",
                "",
                "measurement-class",
                "energisation-status",
                "da",
                "dc",
                "mop",
                "12/10/2022",
                "gsp-group",
                "12/10/2022",
                "dno",
                "msn",
                "12/10/2022",
                "meter-type",
                "map-id",
            ),
        ),
    ]
    exclude_mpan_cores = []
    ignore_mpan_cores_msn = []
    show_ignored = True

    _process(
        sess,
        ecoes_lines,
        exclude_mpan_cores,
        ignore_mpan_cores_msn,
        f,
        show_ignored,
        report_run,
    )
    expected = [
        [
            "mpan_core",
            "mpan_core_no_spaces",
            "ecoes_pc",
            "chellow_pc",
            "ecoes_mtc",
            "ecoes_mtc_date",
            "chellow_mtc",
            "ecoes_llfc",
            "ecoes_llfc_from",
            "chellow_llfc",
            "ecoes_ssc",
            "chellow_ssc",
            "ecoes_es",
            "chellow_es",
            "ecoes_supplier",
            "ecoes_supplier_registration_from",
            "chellow_supplier",
            "chellow_supplier_contract_name",
            "ecoes_dc",
            "chellow_dc",
            "ecoes_mop",
            "ecoes_mop_appoint_date",
            "chellow_mop",
            "ecoes_gsp_group",
            "ecoes_gsp_effective_from",
            "chellow_gsp_group",
            "ecoes_msn",
            "ecoes_msn_install_date",
            "chellow_msn",
            "ecoes_meter_type",
            "chellow_meter_type",
            "ignored",
            "problem",
        ],
        [
            "22 7867 6232 781",
            "2278676232781",
            "pc",
            "00",
            "mtc",
            "2022-10-12 00:00",
            "845",
            "llfc",
            "2022-10-12 00:00",
            "510",
            "",
            "",
            "energisation-status",
            "E",
            "supplier",
            "2022-10-12 00:00",
            "CALB",
            "Fusion Supplier 2000",
            "dc",
            "CALB",
            "mop",
            "2022-10-12 00:00",
            "CALB",
            "gsp-group",
            "2022-10-12 00:00",
            "_L",
            "msn",
            "2022-10-12 00:00",
            "hgjeyhuw",
            "meter-type",
            "H",
            "False",
            "The energisation statuses don't match. Can't parse the PC. Can't parse "
            "the MTC. The LLFCs don't match. The supplier codes don't match. The DC "
            "codes don't match. The MOP codes don't match. The GSP group codes don't "
            "match. The meter serial numbers don't match. The DTC meter types don't "
            "match.",
        ],
        [
            "22 7868 6232 789",
            "2278686232789",
            "pc",
            "00",
            "mtc",
            "2022-10-12 00:00",
            "845",
            "llfc",
            "2022-10-12 00:00",
            "510",
            "",
            "",
            "energisation-status",
            "E",
            "supplier",
            "2022-10-12 00:00",
            "CALB",
            "Fusion Supplier 2000",
            "dc",
            "CALB",
            "mop",
            "2022-10-12 00:00",
            "CALB",
            "gsp-group",
            "2022-10-12 00:00",
            "_L",
            "msn",
            "2022-10-12 00:00",
            "hgjeyhuw",
            "meter-type",
            "H",
            "False",
            "The energisation statuses don't match. Can't parse the PC. Can't parse "
            "the MTC. The LLFCs don't match. The supplier codes don't match. The DC "
            "codes don't match. The MOP codes don't match. The GSP group codes don't "
            "match. The meter serial numbers don't match. The DTC meter types don't "
            "match.",
        ],
    ]
    f.seek(0)
    actual = [line for line in csv.reader(f)]
    match_tables(expected, actual)


def test_process_in_chellow_not_ecoes(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
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
    dno.insert_llfc(sess, "521", "Export (HV)", voltage_level, False, False, vf, None)
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
        "Dave",
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
        None,
        energisation_status,
        dtc_meter_type,
        "22 7868 6232 789",
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
    report_run = ReportRun.insert(
        sess,
        "ecoes_comparison",
        None,
        "ecoes_comparison",
        {},
    )

    sess.commit()
    f = StringIO()
    ecoes_lines = ["titles"]
    exclude_mpan_cores = []
    ignore_mpan_cores_msn = []
    show_ignored = True

    _process(
        sess,
        ecoes_lines,
        exclude_mpan_cores,
        ignore_mpan_cores_msn,
        f,
        show_ignored,
        report_run,
    )
    expected = [
        [
            "mpan_core",
            "mpan_core_no_spaces",
            "ecoes_pc",
            "chellow_pc",
            "ecoes_mtc",
            "ecoes_mtc_date",
            "chellow_mtc",
            "ecoes_llfc",
            "ecoes_llfc_from",
            "chellow_llfc",
            "ecoes_ssc",
            "chellow_ssc",
            "ecoes_es",
            "chellow_es",
            "ecoes_supplier",
            "ecoes_supplier_registration_from",
            "chellow_supplier",
            "chellow_supplier_contract_name",
            "ecoes_dc",
            "chellow_dc",
            "ecoes_mop",
            "ecoes_mop_appoint_date",
            "chellow_mop",
            "ecoes_gsp_group",
            "ecoes_gsp_effective_from",
            "chellow_gsp_group",
            "ecoes_msn",
            "ecoes_msn_install_date",
            "chellow_msn",
            "ecoes_meter_type",
            "chellow_meter_type",
            "ignored",
            "problem",
        ],
        [
            "22 7868 6232 789",
            "2278686232789",
            "",
            "00",
            "",
            "",
            "845",
            "",
            "",
            "510",
            "",
            "",
            "",
            "E",
            "",
            "",
            "CALB",
            "Fusion Supplier 2000",
            "",
            "CALB",
            "",
            "",
            "CALB",
            "",
            "",
            "_L",
            "",
            "",
            "hgjeyhuw",
            "",
            "H",
            "False",
            "In Chellow, but not in ECOES.",
        ],
    ]
    f.seek(0)
    actual = list(csv.reader(f))
    match_tables(expected, actual)


def test_process_dtc_none(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
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
    dno.insert_llfc(sess, "521", "Export (HV)", voltage_level, False, False, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")

    site.insert_e_supply(
        sess,
        source,
        None,
        "Dave",
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
        None,
        energisation_status,
        None,
        "22 7868 6232 789",
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
    report_run = ReportRun.insert(
        sess,
        "ecoes_comparison",
        None,
        "ecoes_comparison",
        {},
    )

    sess.commit()
    f = StringIO()
    ecoes_lines = [
        "titles",
        ",".join(
            (
                "2278686232789",
                "address-line-1",
                "address-line-2",
                "address-line-3",
                "address-line-4",
                "address-line-5",
                "address-line-6",
                "address-line-7",
                "address-line-8",
                "address-line-9",
                "post-code",
                "CALB",
                "12/10/2022",
                "845",
                "12/10/2022",
                "510",
                "12/10/2022",
                "00",
                "",
                "measurement-class",
                "E",
                "CALB",
                "CALB",
                "CALB",
                "12/10/2022",
                "_L",
                "12/10/2022",
                "22",
                "hgjeyhuw",
                "12/10/2022",
                "",
                "map-id",
            ),
        ),
    ]
    exclude_mpan_cores = []
    ignore_mpan_cores_msn = []
    show_ignored = True

    _process(
        sess,
        ecoes_lines,
        exclude_mpan_cores,
        ignore_mpan_cores_msn,
        f,
        show_ignored,
        report_run,
    )
    expected = [
        [
            "mpan_core",
            "mpan_core_no_spaces",
            "ecoes_pc",
            "chellow_pc",
            "ecoes_mtc",
            "ecoes_mtc_date",
            "chellow_mtc",
            "ecoes_llfc",
            "ecoes_llfc_from",
            "chellow_llfc",
            "ecoes_ssc",
            "chellow_ssc",
            "ecoes_es",
            "chellow_es",
            "ecoes_supplier",
            "ecoes_supplier_registration_from",
            "chellow_supplier",
            "chellow_supplier_contract_name",
            "ecoes_dc",
            "chellow_dc",
            "ecoes_mop",
            "ecoes_mop_appoint_date",
            "chellow_mop",
            "ecoes_gsp_group",
            "ecoes_gsp_effective_from",
            "chellow_gsp_group",
            "ecoes_msn",
            "ecoes_msn_install_date",
            "chellow_msn",
            "ecoes_meter_type",
            "chellow_meter_type",
            "ignored",
            "problem",
        ],
    ]
    f.seek(0)
    actual = list(csv.reader(f))
    match_tables(expected, actual)
