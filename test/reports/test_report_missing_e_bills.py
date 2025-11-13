from csv import reader
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
    ReportRun,
    Site,
    Source,
    User,
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_generator_types,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_missing_bills import content
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_content(mocker, sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
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
    source_grid = Source.get_by_code(sess, "grid")
    insert_generator_types(sess)
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source_grid,
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

    user = User.get_by_id(sess, 1)
    user_id = user.id

    report_run = ReportRun.insert(
        sess,
        "missing_e_bills",
        user,
        "missing_e_bills",
        {},
    )
    report_run_id = report_run.id
    dc_contract_id = dc_contract.id
    sess.commit()

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch(
        "chellow.reports.report_missing_bills.open_file", return_value=mock_file
    )
    months_length = 1
    finish_date = utc_datetime(2000, 1, 1)

    content(user_id, report_run_id, dc_contract_id, months_length, finish_date)
    mock_file.seek(0)
    table = [row for row in reader(mock_file)]

    expected = [
        [
            "contract_name",
            "month_start",
            "month_finish",
            "site_code",
            "site_name",
            "imp_mpan_core",
            "exp_mpan_core",
            "account",
        ],
        [
            "Fusion DC 2000",
            "2000-01-01 00:00",
            "2000-01-31 23:30",
            "CI017",
            "Water Works",
            "22 7867 6232 781",
            "",
            "",
        ],
    ]

    match_tables(expected, table)
    response = client.get(f"/report_runs/{report_run_id}")
    match(response, 200)


def test_content_multiple_months(mocker, sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
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
    source_grid = Source.get_by_code(sess, "grid")
    insert_generator_types(sess)
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source_grid,
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

    user = User.get_by_id(sess, 1)
    user_id = user.id

    report_run = ReportRun.insert(
        sess,
        "missing_e_bills",
        user,
        "missing_e_bills",
        {},
    )
    report_run_id = report_run.id
    dc_contract_id = dc_contract.id
    sess.commit()

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch(
        "chellow.reports.report_missing_bills.open_file", return_value=mock_file
    )
    months_length = 2
    finish_date = utc_datetime(2020, 1, 1)

    content(user_id, report_run_id, dc_contract_id, months_length, finish_date)
    mock_file.seek(0)
    table = [row for row in reader(mock_file)]

    expected = [
        [
            "contract_name",
            "month_start",
            "month_finish",
            "site_code",
            "site_name",
            "imp_mpan_core",
            "exp_mpan_core",
            "account",
        ],
        [
            "Fusion DC 2000",
            "2019-12-01 00:00",
            "2019-12-31 23:30",
            "CI017",
            "Water Works",
            "22 7867 6232 781",
            "",
            "",
        ],
        [
            "Fusion DC 2000",
            "2020-01-01 00:00",
            "2020-01-31 23:30",
            "CI017",
            "Water Works",
            "22 7867 6232 781",
            "",
            "",
        ],
    ]

    match_tables(expected, table)
    response = client.get(f"/report_runs/{report_run_id}")
    match(response, 200)


def test_content_bst(mocker, sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
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
    source_grid = Source.get_by_code(sess, "grid")
    insert_generator_types(sess)
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source_grid,
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

    user = User.get_by_id(sess, 1)
    user_id = user.id

    report_run = ReportRun.insert(
        sess,
        "missing_e_bills",
        user,
        "missing_e_bills",
        {},
    )
    report_run_id = report_run.id
    dc_contract_id = dc_contract.id
    sess.commit()

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch(
        "chellow.reports.report_missing_bills.open_file", return_value=mock_file
    )
    months_length = 1
    finish_date = to_utc(ct_datetime(2000, 7, 1))

    content(user_id, report_run_id, dc_contract_id, months_length, finish_date)
    mock_file.seek(0)
    table = [row for row in reader(mock_file)]

    expected = [
        [
            "contract_name",
            "month_start",
            "month_finish",
            "site_code",
            "site_name",
            "imp_mpan_core",
            "exp_mpan_core",
            "account",
        ],
        [
            "Fusion DC 2000",
            "2000-07-01 00:00",
            "2000-07-31 23:30",
            "CI017",
            "Water Works",
            "22 7867 6232 781",
            "",
            "",
        ],
    ]

    match_tables(expected, table)
    response = client.get(f"/report_runs/{report_run_id}")
    match(response, 200)
