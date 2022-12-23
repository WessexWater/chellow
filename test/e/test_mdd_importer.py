from sqlalchemy import select

from chellow.e.mdd_importer import (
    _import_MTC_in_PES_Area,
    _import_Market_Participant_Role,
    _import_Measurement_Requirement,
    _import_Meter_Timeswitch_Class,
    _import_Time_Pattern_Regime,
    _import_Valid_MTC_LLFC_Combination,
    _import_Valid_MTC_LLFC_SSC_Combination,
    _import_Valid_MTC_LLFC_SSC_PC_Combination,
    _import_Valid_MTC_SSC_Combination,
    rate_server_import,
)
from chellow.models import (
    Contract,
    MarketRole,
    MeasurementRequirement,
    MeterPaymentType,
    MeterType,
    Mtc,
    MtcLlfcSsc,
    MtcParticipant,
    MtcSsc,
    Participant,
    Pc,
    Ssc,
    Tpr,
    VoltageLevel,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_import_Market_Participant_Role_R(sess):
    participant_code = "EDFI"
    Participant.insert(sess, participant_code, "hyde participant")
    market_role_code = "R"
    MarketRole.insert(sess, market_role_code, "dno")
    sess.commit()

    rows = [
        [
            participant_code,
            market_role_code,
            "16/04/2009",
            "17/12/2014",
            "UK Power Networks (IDNO)",
            "Energy House",
            "Hazelwick Avenue",
            "Three Bridges",
            "Crawley",
            "West Sussex",
            "",
            "",
            "",
            "RH10 1EX",
            "28",
        ]
    ]
    ctx = {}
    _import_Market_Participant_Role(sess, rows, ctx)


def test_import_Measurement_Requirement(sess):
    Ssc.insert(sess, "0001", "All", True, to_utc(ct_datetime(2000, 1, 1)), None)
    Tpr.insert(sess, "00205", True, True)
    rows = [["0001", "00205"]]
    ctx = {}
    _import_Measurement_Requirement(sess, rows, ctx)


def test_import_Measurement_Requirement_no_ongoing_ssc(sess):
    """Check that we get the latest SSC, even when there isn't an ongoing one"""
    Ssc.insert(
        sess,
        "0001",
        "All",
        True,
        to_utc(ct_datetime(2000, 1, 1)),
        to_utc(ct_datetime(2001, 1, 1, 23, 30)),
    )
    latest_ssc = Ssc.insert(
        sess,
        "0001",
        "All",
        True,
        to_utc(ct_datetime(2001, 1, 2)),
        to_utc(ct_datetime(2002, 1, 1)),
    )
    Tpr.insert(sess, "00205", True, True)
    sess.commit()
    rows = [["0001", "00205"]]
    ctx = {}
    _import_Measurement_Requirement(sess, rows, ctx)

    mr = sess.execute(select(MeasurementRequirement)).scalar()
    assert mr.ssc == latest_ssc


def test_import_Meter_Timeswitch_Class(sess):
    rows = [
        [
            "1",
            "01/04/1996",
            "",
            "",
            "F",
            "F",
            "",
            "",
            "",
            "",
            "",
        ]
    ]
    ctx = {}
    _import_Meter_Timeswitch_Class(sess, rows, ctx)


def test_import_Meter_Timeswitch_Class_no_tpr_count(sess):
    vf = to_utc(ct_datetime(1996, 4, 1))
    MeterType.insert(sess, "C5", "A c5 meter", vf, None)
    MeterPaymentType.insert(sess, "CR", "credit", vf, None)
    rows = [
        [
            "845",
            "01/04/1996",
            "",
            "HH COP5 And Above With Comms",
            "T",
            "F",
            "C5",
            "CR",
            "Y",
            "H",
            "",
        ]
    ]
    ctx = {}
    _import_Meter_Timeswitch_Class(sess, rows, ctx)


def test_import_MTC_in_PES_Area(sess):
    vf = to_utc(ct_datetime(1996, 4, 1))
    participant_code = "HYDE"
    Participant.insert(sess, participant_code, "hyde participant")
    mtc_code = "001"
    Mtc.insert(
        sess,
        mtc_code,
        False,
        False,
        vf,
        None,
    )
    MeterType.insert(sess, "UN", "A c5 meter", vf, None)
    MeterPaymentType.insert(sess, "TS", "credit", vf, None)
    rows = [
        [
            mtc_code,
            "01/04/1996",
            "HYDE",
            "01/04/1996",
            "",
            "Unrestricted, Single rate",
            "UN",
            "TS",
            "N",
            "N",
            "1",
        ]
    ]
    ctx = {}
    _import_MTC_in_PES_Area(sess, rows, ctx)


def test_import_Time_Pattern_Regime(sess):
    rows = [["00001", "C", "N"]]
    ctx = {}
    _import_Time_Pattern_Regime(sess, rows, ctx)


def test_import_Valid_MTC_LLFC_Combination(sess):
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    participant_code = "HYDE"
    participant = Participant.insert(sess, participant_code, "hyde participant")
    mtc_code = "001"
    mtc = Mtc.insert(
        sess,
        mtc_code,
        False,
        False,
        valid_from,
        None,
    )
    meter_type = MeterType.insert(sess, "UN", "A c5 meter", valid_from, None)
    meter_payment_type = MeterPaymentType.insert(sess, "TS", "credit", valid_from, None)
    MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "desc",
        True,
        True,
        meter_type,
        meter_payment_type,
        1,
        valid_from,
        None,
    )
    dno_role = MarketRole.insert(sess, "R", "dno")
    dno = participant.insert_party(sess, dno_role, "dno", valid_from, None, "10")
    insert_voltage_levels(sess)
    vl = VoltageLevel.get_by_code(sess, "HV")
    dno.insert_llfc(sess, "H85", "llfc h85", vl, False, True, valid_from, None)
    rows = [
        [
            mtc_code,
            "01/04/1996",
            participant_code,
            "01/04/1996",
            "H85",
            "01/04/2021",
            "",
        ]
    ]
    ctx = {}
    _import_Valid_MTC_LLFC_Combination(sess, rows, ctx)


def test_import_Valid_MTC_SSC_Combination(sess):
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    participant_code = "HYDE"
    participant = Participant.insert(sess, participant_code, "hyde participant")
    mtc_code = "001"
    mtc = Mtc.insert(
        sess,
        mtc_code,
        False,
        False,
        valid_from,
        None,
    )
    meter_type = MeterType.insert(sess, "UN", "A c5 meter", valid_from, None)
    meter_payment_type = MeterPaymentType.insert(sess, "TS", "credit", valid_from, None)
    mtc_participant_valid_from = to_utc(ct_datetime(2005, 12, 2))
    MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "desc",
        True,
        True,
        meter_type,
        meter_payment_type,
        1,
        mtc_participant_valid_from,
        None,
    )
    ssc_code = "0721"
    Ssc.insert(sess, ssc_code, "desc", True, valid_from, None)
    rows = [
        [
            mtc_code,
            "01/04/1996",
            participant_code,
            "02/12/2005",
            ssc_code,
            "02/12/2005",
            "",
        ]
    ]
    ctx = {}
    _import_Valid_MTC_SSC_Combination(sess, rows, ctx)


def test_import_Valid_MTC_LLFC_SSC_Combination(sess):
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    participant_code = "HYDE"
    participant = Participant.insert(sess, participant_code, "hyde participant")
    mtc_code = "001"
    mtc = Mtc.insert(
        sess,
        mtc_code,
        False,
        False,
        valid_from,
        None,
    )
    meter_type = MeterType.insert(sess, "UN", "A c5 meter", valid_from, None)
    meter_payment_type = MeterPaymentType.insert(sess, "TS", "credit", valid_from, None)
    mtc_participant_valid_from = to_utc(ct_datetime(2005, 12, 2))
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "desc",
        True,
        True,
        meter_type,
        meter_payment_type,
        1,
        mtc_participant_valid_from,
        None,
    )
    ssc_code = "0721"
    ssc = Ssc.insert(sess, ssc_code, "desc", True, valid_from, None)
    dno_role = MarketRole.insert(sess, "R", "dno")
    dno = participant.insert_party(sess, dno_role, "dno", valid_from, None, "10")
    insert_voltage_levels(sess)
    vl = VoltageLevel.get_by_code(sess, "HV")
    llfc_code = "183"
    dno.insert_llfc(sess, llfc_code, "llfc h85", vl, False, True, valid_from, None)
    MtcSsc.insert(sess, mtc_participant, ssc, to_utc(ct_datetime(2005, 12, 2)), None)
    rows = [
        [
            mtc_code,
            "01/04/1996",
            participant_code,
            "02/12/2005",
            ssc_code,
            "02/12/2005",
            llfc_code,
            "01/04/2006",
            "",
        ]
    ]
    ctx = {}
    _import_Valid_MTC_LLFC_SSC_Combination(sess, rows, ctx)


def test_import_Valid_MTC_LLFC_SSC_PC_Combination(sess):
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    participant_code = "HYDE"
    participant = Participant.insert(sess, participant_code, "hyde participant")
    mtc_code = "001"
    mtc = Mtc.insert(
        sess,
        mtc_code,
        False,
        False,
        valid_from,
        None,
    )
    meter_type = MeterType.insert(sess, "UN", "A c5 meter", valid_from, None)
    meter_payment_type = MeterPaymentType.insert(sess, "TS", "credit", valid_from, None)
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "desc",
        True,
        True,
        meter_type,
        meter_payment_type,
        1,
        to_utc(ct_datetime(2009, 4, 16)),
        None,
    )
    ssc_code = "0721"
    ssc = Ssc.insert(sess, ssc_code, "desc", True, valid_from, None)
    dno_role = MarketRole.insert(sess, "R", "dno")
    dno = participant.insert_party(sess, dno_role, "dno", valid_from, None, "10")
    insert_voltage_levels(sess)
    vl = VoltageLevel.get_by_code(sess, "HV")
    llfc_code = "183"
    llfc = dno.insert_llfc(
        sess, llfc_code, "llfc h85", vl, False, True, valid_from, None
    )
    pc_code = "00"
    Pc.insert(sess, pc_code, "hh", utc_datetime(2000, 1, 1), None)
    mtc_ssc = MtcSsc.insert(
        sess, mtc_participant, ssc, to_utc(ct_datetime(2009, 4, 16)), None
    )
    mtc_llfc_ssc = MtcLlfcSsc.insert(
        sess, mtc_ssc, llfc, to_utc(ct_datetime(2009, 4, 16)), None
    )
    rows = [
        [
            mtc_code,
            "01/04/1996",
            participant_code,
            "16/04/2009",
            ssc_code,
            "16/04/2009",
            llfc_code,
            "16/04/2009",
            pc_code,
            "17/03/2010",
            "20/08/2014",
            "F",
        ]
    ]
    ctx = {}
    _import_Valid_MTC_LLFC_SSC_PC_Combination(sess, rows, ctx)
    combos = mtc_llfc_ssc.mtc_llfc_ssc_pcs
    assert len(combos) == 1

    combo = combos[0]

    assert combo.valid_to == to_utc(ct_datetime(2014, 8, 20, 23, 30))


def test_import_mdd(mocker, sess):
    vf = to_utc(ct_datetime(1996, 4, 1))
    MeterType.insert(sess, "C5", "A c5 meter", vf, None)
    MeterPaymentType.insert(sess, "CR", "credit", vf, None)
    calb_participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    calb_participant.insert_party(sess, market_role_Z, "NonCore", vf, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, vf, None, {})
    sess.commit()

    log = mocker.Mock()
    set_progress = mocker.Mock()

    mocker.patch("chellow.e.mdd_importer.download", return_value=b"\n")

    path_list = (
        ("2022", "electricity", "mdd", "50", "Clock_Interval_50.csv"),
        ("2022", "electricity", "mdd", "50", "GSP_Group_50.csv"),
        ("2022", "electricity", "mdd", "50", "Line_Loss_Factor_Class_50.csv"),
        ("2022", "electricity", "mdd", "50", "Market_Participant_50.csv"),
        ("2022", "electricity", "mdd", "50", "Market_Role_50.csv"),
        ("2022", "electricity", "mdd", "50", "Market_Participant_Role_50.csv"),
        ("2022", "electricity", "mdd", "50", "Measurement_Requirement_50.csv"),
        ("2022", "electricity", "mdd", "50", "Meter_Timeswitch_Class_50.csv"),
        ("2022", "electricity", "mdd", "50", "MTC_in_PES_Area_50.csv"),
        ("2022", "electricity", "mdd", "50", "MTC_Meter_Type_50.csv"),
        ("2022", "electricity", "mdd", "50", "MTC_Payment_Type_50.csv"),
        ("2022", "electricity", "mdd", "50", "Profile_Class_50.csv"),
        (
            "2022",
            "electricity",
            "mdd",
            "50",
            "Standard_Settlement_Configuration_50.csv",
        ),
        ("2022", "electricity", "mdd", "50", "Time_Pattern_Regime_50.csv"),
        ("2022", "electricity", "mdd", "50", "Valid_MTC_LLFC_Combination_50.csv"),
        ("2022", "electricity", "mdd", "50", "Valid_MTC_SSC_Combination_50.csv"),
        ("2022", "electricity", "mdd", "50", "Valid_MTC_LLFC_SSC_Combination_50.csv"),
        (
            "2022",
            "electricity",
            "mdd",
            "50",
            "Valid_MTC_LLFC_SSC_PC_Combination_50.csv",
        ),
    )
    paths = tuple((p, "") for p in path_list)
    s = mocker.Mock()

    rate_server_import(sess, log, set_progress, s, paths)


def test_import_mdd_two_versions(mocker, sess):
    mocker.patch("chellow.e.mdd_importer.download", return_value=b"\n")

    path_list = (
        ("2022", "electricity", "mdd", "49"),
        ("2022", "electricity", "mdd", "50", "Clock_Interval_50.csv"),
        ("2022", "electricity", "mdd", "50", "GSP_Group_50.csv"),
        ("2022", "electricity", "mdd", "50", "Line_Loss_Factor_Class_50.csv"),
        ("2022", "electricity", "mdd", "50", "Market_Participant_50.csv"),
        ("2022", "electricity", "mdd", "50", "Market_Role_50.csv"),
        ("2022", "electricity", "mdd", "50", "Market_Participant_Role_50.csv"),
        ("2022", "electricity", "mdd", "50", "Meter_Timeswitch_Class_50.csv"),
        ("2022", "electricity", "mdd", "50", "Measurement_Requirement_50.csv"),
        ("2022", "electricity", "mdd", "50", "MTC_in_PES_Area_50.csv"),
        ("2022", "electricity", "mdd", "50", "MTC_Meter_Type_50.csv"),
        ("2022", "electricity", "mdd", "50", "MTC_Payment_Type_50.csv"),
        ("2022", "electricity", "mdd", "50", "Profile_Class_50.csv"),
        (
            "2022",
            "electricity",
            "mdd",
            "50",
            "Standard_Settlement_Configuration_50.csv",
        ),
        ("2022", "electricity", "mdd", "50", "Time_Pattern_Regime_50.csv"),
        ("2022", "electricity", "mdd", "50", "Valid_MTC_LLFC_Combination_50.csv"),
        ("2022", "electricity", "mdd", "50", "Valid_MTC_SSC_Combination_50.csv"),
        ("2022", "electricity", "mdd", "50", "Valid_MTC_LLFC_SSC_Combination_50.csv"),
        (
            "2022",
            "electricity",
            "mdd",
            "50",
            "Valid_MTC_LLFC_SSC_PC_Combination_50.csv",
        ),
    )
    paths = tuple((p, "") for p in path_list)

    vf = to_utc(ct_datetime(1996, 4, 1))
    MeterType.insert(sess, "C5", "A c5 meter", vf, None)
    MeterPaymentType.insert(sess, "CR", "credit", vf, None)
    calb_participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    calb_participant.insert_party(sess, market_role_Z, "NonCore", vf, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, vf, None, {})
    sess.commit()

    log = mocker.Mock()
    set_progress = mocker.Mock()
    s = mocker.Mock()
    rate_server_import(sess, log, set_progress, s, paths)
