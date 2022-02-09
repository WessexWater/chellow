from io import StringIO

from chellow.models import (
    Comm,
    Contract,
    Cop,
    EnergisationStatus,
    GspGroup,
    MarketRole,
    MeterPaymentType,
    MeterType,
    OldMtc,
    OldValidMtcLlfcSscPc,
    Participant,
    Pc,
    ReportRun,
    Site,
    Source,
    Ssc,
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_ecoes_comparison import _meter_type, _process
from chellow.utils import utc_datetime


def test_process(mocker, sess):
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
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
    dno.insert_llfc(
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
                "registration-from",
                "mtc",
                "mtc-date",
                "llfc",
                "llfc-from",
                "pc",
                "",
                "measurement-class",
                "energisation-status",
                "da",
                "dc",
                "mop",
                "mop-appoint-date",
                "gsp-group",
                "gsp-effective-from",
                "dno",
                "msn",
                "meter-install-date",
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
                "registration-from",
                "mtc",
                "mtc-date",
                "llfc",
                "llfc-from",
                "pc",
                "",
                "measurement-class",
                "energisation-status",
                "da",
                "dc",
                "mop",
                "mop-appoint-date",
                "gsp-group",
                "gsp-effective-from",
                "dno",
                "msn",
                "meter-install-date",
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
            "chellow_mtc",
            "ecoes_llfc",
            "chellow_llfc",
            "ecoes_ssc",
            "chellow_ssc",
            "ecoes_es",
            "chellow_es",
            "ecoes_supplier",
            "chellow_supplier",
            "chellow_supplier_contract_name",
            "ecoes_dc",
            "chellow_dc",
            "ecoes_mop",
            "chellow_mop",
            "ecoes_gsp_group",
            "chellow_gsp_group",
            "ecoes_msn",
            "chellow_msn",
            "ecoes_msn_install_date",
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
            "845",
            "llfc",
            "510",
            "",
            "",
            "energisation-status",
            "E",
            "supplier",
            "CALB",
            "Fusion Supplier 2000",
            "dc",
            "CALB",
            "mop",
            "CALB",
            "gsp-group",
            "_L",
            "msn",
            "hgjeyhuw",
            "meter-install-date",
            "meter-type",
            "H",
            "False",
            "The energisation statuses don't match. Can't parse the PC. Can't parse "
            "the MTC. The LLFCs don't match. The supplier codes don't match. The DC "
            "codes don't match. The MOP codes don't match. The GSP group codes don't "
            "match. The meter serial numbers don't match. The meter types don't match. "
            "See https://dtc.mrasco.com/DataItem.aspx?ItemCounter=0483 ",
        ],
        [
            "22 7868 6232 789",
            "2278686232789",
            "pc",
            "00",
            "mtc",
            "845",
            "llfc",
            "510",
            "",
            "",
            "energisation-status",
            "E",
            "supplier",
            "CALB",
            "Fusion Supplier 2000",
            "dc",
            "CALB",
            "mop",
            "CALB",
            "gsp-group",
            "_L",
            "msn",
            "hgjeyhuw",
            "meter-install-date",
            "meter-type",
            "H",
            "False",
            "The energisation statuses don't match. Can't parse the PC. Can't parse "
            "the MTC. The LLFCs don't match. The supplier codes don't match. The DC "
            "codes don't match. The MOP codes don't match. The GSP group codes don't "
            "match. The meter serial numbers don't match. The meter types don't match. "
            "See https://dtc.mrasco.com/DataItem.aspx?ItemCounter=0483 ",
        ],
    ]
    assert f.getvalue() == "\n".join(",".join(line) for line in expected) + "\n"


def test_process_in_chellow_not_ecoes(mocker, sess):
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
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
    dno.insert_llfc(
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
            "chellow_mtc",
            "ecoes_llfc",
            "chellow_llfc",
            "ecoes_ssc",
            "chellow_ssc",
            "ecoes_es",
            "chellow_es",
            "ecoes_supplier",
            "chellow_supplier",
            "chellow_supplier_contract_name",
            "ecoes_dc",
            "chellow_dc",
            "ecoes_mop",
            "chellow_mop",
            "ecoes_gsp_group",
            "chellow_gsp_group",
            "ecoes_msn",
            "chellow_msn",
            "ecoes_msn_install_date",
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
            "845",
            "",
            "510",
            "",
            "",
            "",
            "E",
            "",
            "CALB",
            "Fusion Supplier 2000",
            "",
            "CALB",
            "",
            "CALB",
            "",
            "_L",
            "",
            "hgjeyhuw",
            "",
            "",
            "H",
            "False",
            '"In Chellow, but not in ECOES."',
        ],
    ]
    assert f.getvalue() == "\n".join(",".join(line) for line in expected) + "\n"


def test_meter_type(mocker, sess):
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
    pc = Pc.insert(sess, "02", "nhh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    ssc = Ssc.insert(sess, "0393", "unrestricted", True, utc_datetime(2000, 1), None)
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
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    old_mtc = OldMtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    OldValidMtcLlfcSscPc.insert(
        sess, old_mtc, llfc, ssc, pc, utc_datetime(1996, 1, 1), None
    )

    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Dave",
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
        ssc,
        energisation_status,
        {},
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

    era = supply.eras[0]

    _meter_type(
        era,
    )
