from chellow.e.mdd_importer import (
    _import_MTC_in_PES_Area,
    _import_Meter_Timeswitch_Class,
    _import_Valid_MTC_LLFC_Combination,
    _import_Valid_MTC_LLFC_SSC_Combination,
    _import_Valid_MTC_LLFC_SSC_PC_Combination,
    _import_Valid_MTC_SSC_Combination,
    import_mdd,
)
from chellow.models import (
    Contract,
    MarketRole,
    MeterPaymentType,
    MeterType,
    Mtc,
    MtcLlfcSsc,
    MtcParticipant,
    MtcSsc,
    Participant,
    Pc,
    Ssc,
    VoltageLevel,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


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
    repo_url = "rateserver"
    lookup = {
        f"{repo_url}/contents": {
            "json": [{"type": "dir", "url": f"{repo_url}/contents/2022"}],
        },
        f"{repo_url}/contents/2022": {
            "json": [
                {
                    "type": "dir",
                    "url": f"{repo_url}/contents/2022/electricity",
                    "name": "electricity",
                }
            ],
        },
        f"{repo_url}/contents/2022/electricity": {
            "json": [
                {
                    "type": "dir",
                    "url": f"{repo_url}/contents/2022/electricity/mdd",
                    "name": "mdd",
                }
            ],
        },
        f"{repo_url}/contents/2022/electricity/mdd": {
            "json": [
                {
                    "type": "dir",
                    "url": f"{repo_url}/contents/2022/electricity/mdd/50",
                    "name": "50",
                    "path": "2022/mdd/50",
                }
            ],
        },
        f"{repo_url}/contents/2022/electricity/mdd/50": {
            "json": [
                {
                    "type": "file",
                    "download_url": "download/Market_Participant",
                    "name": "Market_Participant_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/Market_Role",
                    "name": "Market_Role_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/Market_Participant_Role",
                    "name": "Market_Participant_Role_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/Line_Loss_Factor_Class",
                    "name": "Line_Loss_Factor_Class_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/Meter_Timeswitch_Class",
                    "name": "Meter_Timeswitch_Class_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/MTC_in_PES_Area",
                    "name": "MTC_in_PES_Area_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/MTC_Meter_Type",
                    "name": "MTC_Meter_Type_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/Standard_Settlement_Configuration",
                    "name": "Standard_Settlement_Configuration_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/Valid_MTC_LLFC_Combination",
                    "name": "Valid_MTC_LLFC_Combination_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/Valid_MTC_SSC_Combination",
                    "name": "Valid_MTC_SSC_Combination_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/Valid_MTC_LLFC_SSC_Combination",
                    "name": "Valid_MTC_LLFC_SSC_Combination_50.csv",
                },
                {
                    "type": "file",
                    "download_url": "download/Valid_MTC_LLFC_SSC_PC_Combination",
                    "name": "Valid_MTC_LLFC_SSC_PC_Combination_50.csv",
                },
            ],
        },
        "download/Market_Participant": {"text": "\n"},
        "download/Market_Role": {"text": "\n"},
        "download/Market_Participant_Role": {"text": "\n"},
        "download/Line_Loss_Factor_Class": {"text": "\n"},
        "download/Meter_Timeswitch_Class": {"text": "\n"},
        "download/MTC_in_PES_Area": {"text": "\n"},
        "download/MTC_Meter_Type": {"text": "\n"},
        "download/Standard_Settlement_Configuration": {"text": "\n"},
        "download/Valid_MTC_LLFC_Combination": {"text": "\n"},
        "download/Valid_MTC_SSC_Combination": {"text": "\n"},
        "download/Valid_MTC_LLFC_SSC_Combination": {"text": "\n"},
        "download/Valid_MTC_LLFC_SSC_PC_Combination": {"text": "\n"},
    }

    def mock_session_get(self, url):
        response_data = lookup[url]
        mock_response = mocker.Mock()
        try:
            mock_response.json.return_value = response_data["json"]
        except KeyError:
            pass
        try:
            mock_response.text = response_data["text"]
        except KeyError:
            pass
        return mock_response

    mocker.patch("chellow.e.mdd_importer.requests.Session.get", mock_session_get)
    vf = to_utc(ct_datetime(1996, 4, 1))
    MeterType.insert(sess, "C5", "A c5 meter", vf, None)
    MeterPaymentType.insert(sess, "CR", "credit", vf, None)
    calb_participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    calb_participant.insert_party(sess, market_role_Z, "NonCore", vf, None, "")
    Contract.insert_non_core(sess, "configuration", "", {}, vf, None, {})
    sess.commit()

    def logger(msg):
        pass

    import_mdd(sess, repo_url, logger)
