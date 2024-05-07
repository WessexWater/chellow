from io import BytesIO, StringIO
from zipfile import ZIP_DEFLATED, ZipFile

from utils import match

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
from chellow.reports.report_169 import content
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_handle_request(mocker, client, rsess):
    user = User.get_by_email_address(rsess, "admin@example.com")
    MockThread = mocker.patch("chellow.reports.report_169.threading.Thread")

    channel_type = "used"

    query_string = {
        "start_year": "2020",
        "start_month": "06",
        "start_day": "01",
        "finish_year": "2020",
        "finish_month": "06",
        "finish_day": "01",
        "channel_type": channel_type,
    }
    response = client.get("/reports/169", query_string=query_string)

    match(response, 303)

    expected_args = (
        to_utc(ct_datetime(2020, 6, 1)),
        to_utc(ct_datetime(2020, 6, 1, 23, 30)),
        False,
        channel_type,
        False,
        None,
        None,
        user.id,
    )

    MockThread.assert_called_with(target=content, args=expected_args)


def test_content(mocker, client, rsess):
    user = User.get_by_email_address(rsess, "admin@example.com")

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mock_open_file = mocker.patch(
        "chellow.reports.report_169.open_file", return_value=mock_file
    )
    start_date = to_utc(ct_datetime(2020, 6, 1))
    finish_date = to_utc(ct_datetime(2020, 6, 1, 23, 30))
    imp_related = True
    channel_type = "used"
    is_zipped = False
    supply_id = None
    mpan_cores = None
    user_id = user.id
    content(
        start_date,
        finish_date,
        imp_related,
        channel_type,
        is_zipped,
        supply_id,
        mpan_cores,
        user_id,
    )
    call_args = mock_open_file.call_args
    arg_name, arg_user = call_args[0]
    assert arg_name == "supplies_hh_data_202006012330.csv"
    assert arg_user.id == user.id

    expected = [
        "import_mpan_core",
        "export_mpan_core",
        "is_hh",
        "is_import_related",
        "channel_type",
        "hh_start_clock_time",
        "total",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "10",
        "11",
        "12",
        "13",
        "14",
        "15",
        "16",
        "17",
        "18",
        "19",
        "20",
        "21",
        "22",
        "23",
        "24",
        "25",
        "26",
        "27",
        "28",
        "29",
        "30",
        "31",
        "32",
        "33",
        "34",
        "35",
        "36",
        "37",
        "38",
        "39",
        "40",
        "41",
        "42",
        "43",
        "44",
        "45",
        "46",
        "47",
        "48",
        "49",
        "50",
    ]
    assert mock_file.getvalue() == ",".join(expected) + "\n"


def test_content_zip(mocker, sess):
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
    Contract.insert_dno(sess, dno.dno_code, participant, "", {}, vf, None, {})
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

    sess.commit()

    f = BytesIO()
    zf = ZipFile(f, "w", ZIP_DEFLATED)
    mocker.patch("chellow.reports.report_169.open_file", return_value=zf)
    start_date = to_utc(ct_datetime(2020, 6, 1))
    finish_date = to_utc(ct_datetime(2020, 6, 1, 23, 30))
    imp_related = True
    channel_type = "ACTIVE"
    is_zipped = True
    supply_id = None
    mpan_cores = None
    content(
        start_date,
        finish_date,
        imp_related,
        channel_type,
        is_zipped,
        supply_id,
        mpan_cores,
        user_id,
    )
    with ZipFile(f, "r") as zf:
        namelist = zf.namelist()
        assert namelist == ["22_7867_6232_781_None_1.csv"]
