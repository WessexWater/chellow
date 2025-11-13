import csv

from io import StringIO

from utils import match, match_tables

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
from chellow.reports.report_channel_snags import content
from chellow.utils import ct_datetime, to_utc


def test_do_get_as_csv(mocker, sess, client):
    mock_Thread = mocker.patch("chellow.reports.report_channel_snags.threading.Thread")
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    user = User.get_by_email_address(sess, "admin@example.com")
    user_id = user.id
    dc_contract_id = dc_contract.id
    sess.commit()
    f = StringIO()
    mocker.patch("chellow.reports.report_channel_snags.open_file", return_value=f)
    days_hidden = 0
    is_ignored = True
    show_settlement = "both"
    only_ongoing = True
    as_csv = True
    days_long_hidden = ""
    now = to_utc(ct_datetime(2025, 10, 31, 0, 0))
    query_string = {
        "days_hidden": days_hidden,
        "show_settlement": show_settlement,
        "is_ignored": is_ignored,
        "only_ongoing": only_ongoing,
        "dc_contract_id": dc_contract_id,
        "as_csv": as_csv,
        "days_long_hidden": days_long_hidden,
        "now_year": 2025,
        "now_month": 10,
        "now_day": 31,
        "now_hour": 0,
        "now_minute": 0,
    }
    response = client.get("/reports/channel_snags", query_string=query_string)
    match(response, 303)

    args = (
        dc_contract_id,
        days_hidden,
        is_ignored,
        user_id,
        only_ongoing,
        show_settlement,
        None,
        now,
    )
    mock_Thread.assert_called_with(target=content, args=args)


def test_do_get_as_html(mocker, sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    dc_contract_id = dc_contract.id
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)

    mop_contract = Contract.insert_mop(
        sess, "Fusion Mop Contract", participant, "", {}, vf, None, {}
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
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        to_utc(ct_datetime(2000, 1, 1)),
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
    era = supply.eras[0]
    era.insert_channel(sess, True, "ACTIVE")
    sess.commit()

    days_hidden = 0
    is_ignored = True
    show_settlement = "both"
    only_ongoing = True
    days_long_hidden = ""
    query_string = {
        "days_hidden": days_hidden,
        "show_settlement": show_settlement,
        "is_ignored": is_ignored,
        "only_ongoing": only_ongoing,
        "dc_contract_id": dc_contract_id,
        "days_long_hidden": days_long_hidden,
    }
    response = client.get("/reports/channel_snags", query_string=query_string)
    match(response, 200)


def test_content(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    dc_contract_id = dc_contract.id

    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)

    mop_contract = Contract.insert_mop(
        sess, "Fusion Mop Contract", participant, "", {}, vf, None, {}
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
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        to_utc(ct_datetime(2000, 1, 1)),
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
    era = supply.eras[0]
    era.insert_channel(sess, True, "ACTIVE")
    sess.commit()
    f = StringIO()
    f.close = mocker.Mock()
    mocker.patch("chellow.reports.report_channel_snags.open_file", return_value=f)
    days_hidden = 0
    is_ignored = True
    days_since_finished = ""
    show_settlement = "both"
    days_long_hidden = None
    now = to_utc(ct_datetime(2025, 10, 30, 0, 0))
    content(
        dc_contract_id,
        days_hidden,
        is_ignored,
        user_id,
        days_since_finished,
        show_settlement,
        days_long_hidden,
        now,
    )
    f.seek(0)
    actual = list(csv.reader(f))
    expected = [
        [
            "contract",
            "hidden_days",
            "chellow_ids",
            "imp_mpan_core",
            "exp_mpan_core",
            "site_code",
            "site_name",
            "snag_description",
            "channel_types",
            "start_date",
            "finish_date",
            "is_ignored",
            "days_since_finished",
            "duration",
        ],
        [
            "Fusion DC 2000",
            "0",
            "1",
            "22 7867 6232 781",
            "",
            "CI017",
            "Water Works",
            "Missing",
            "True_ACTIVE",
            "2000-01-01 00:00",
            "",
            "False",
            "",
            "9434",
        ],
    ]
    match_tables(expected, actual)


def test_content_not_show_settlement(mocker, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
    dc_contract_id = dc_contract.id
    sess.commit()

    f = StringIO()
    f.close = mocker.Mock()
    mocker.patch("chellow.reports.report_channel_snags.open_file", return_value=f)
    days_hidden = 0
    is_ignored = True
    days_since_finished = ""
    show_settlement = "no"
    days_long_hidden = ""
    now = to_utc(ct_datetime(2025, 10, 30, 0, 0))
    content(
        dc_contract_id,
        days_hidden,
        is_ignored,
        user_id,
        days_since_finished,
        show_settlement,
        days_long_hidden,
        now,
    )
    f.seek(0)
    actual = list(csv.reader(f))
    expected = [
        [
            "contract",
            "hidden_days",
            "chellow_ids",
            "imp_mpan_core",
            "exp_mpan_core",
            "site_code",
            "site_name",
            "snag_description",
            "channel_types",
            "start_date",
            "finish_date",
            "is_ignored",
            "days_since_finished",
            "duration",
        ]
    ]
    match_tables(expected, actual)
