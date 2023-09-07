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
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_187 import content
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_content_no_data(mocker, sess):
    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_187.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_187.chellow.dloads.make_names",
        return_value=("a", "b"),
    )
    mocker.patch("chellow.reports.report_187.os.rename")
    start_date = to_utc(ct_datetime(2023, 7, 5))
    finish_date = to_utc(ct_datetime(2023, 7, 18, 22, 30))
    supply_id = None
    mpan_cores = None
    is_zipped = False
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    sess.commit()
    content(start_date, finish_date, supply_id, mpan_cores, is_zipped, user.id)
    expected = [
        "Site Code",
        "Imp MPAN Core",
        "Exp Mpan Core",
        "HH Start Clock-Time",
        "Import ACTIVE kWh",
        "Import ACTIVE Status",
        "Import ACTIVE Modified",
        "Import REACTIVE_IMP kVArh",
        "Import REACTIVE_IMP Status",
        "Import REACTIVE_IMP Modified",
        "Import REACTIVE_EXP kVArh",
        "Import REACTIVE_EXP Status",
        "Import REACTIVE_EXP Modified",
        "Export ACTIVE kWh",
        "Export ACTIVE Status",
        "Export ACTIVE Modified",
        "Export REACTIVE_IMP kVArh",
        "Export REACTIVE_IMP Status",
        "Export REACTIVE_IMP Modified",
        "Export REACTIVE_EXP kVArh",
        "Export REACTIVE_EXP Status",
        "Export REACTIVE_EXP Modified",
    ]
    assert mock_file.getvalue() == ",".join(f'"{v}"' for v in expected) + "\n"


def test_content(mocker, sess):
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

    mop_contract = Contract.insert_mop(sess, "Mop 2", participant, "", {}, vf, None, {})

    dc_contract = Contract.insert_dc(sess, "DC 2000", participant, "", {}, vf, None, {})
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    imp_supplier_contract = Contract.insert_supplier(
        sess, "Sup 2000", participant, "", {}, vf, None, {}
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
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    sess.commit()

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_187.open", return_value=mock_file)
    mocker.patch(
        "chellow.reports.report_187.chellow.dloads.make_names",
        return_value=("a", "b"),
    )
    mocker.patch("chellow.reports.report_187.os.rename")
    start_date = to_utc(ct_datetime(2023, 7, 18, 22, 30))
    finish_date = to_utc(ct_datetime(2023, 7, 18, 22, 30))
    supply_id = None
    mpan_cores = None
    is_zipped = False
    content(start_date, finish_date, supply_id, mpan_cores, is_zipped, user.id)
    expected = [
        [
            "Site Code",
            "Imp MPAN Core",
            "Exp Mpan Core",
            "HH Start Clock-Time",
            "Import ACTIVE kWh",
            "Import ACTIVE Status",
            "Import ACTIVE Modified",
            "Import REACTIVE_IMP kVArh",
            "Import REACTIVE_IMP Status",
            "Import REACTIVE_IMP Modified",
            "Import REACTIVE_EXP kVArh",
            "Import REACTIVE_EXP Status",
            "Import REACTIVE_EXP Modified",
            "Export ACTIVE kWh",
            "Export ACTIVE Status",
            "Export ACTIVE Modified",
            "Export REACTIVE_IMP kVArh",
            "Export REACTIVE_IMP Status",
            "Export REACTIVE_IMP Modified",
            "Export REACTIVE_EXP kVArh",
            "Export REACTIVE_EXP Status",
            "Export REACTIVE_EXP Modified",
        ],
        ["CI017", "22 7867 6232 781", "", "2023-07-18 22:30"],
    ]

    print(mock_file.getvalue())
    expected_str = "".join(
        (",".join(f'"{v}"' for v in line) + "\n") for line in expected
    )
    assert mock_file.getvalue() == expected_str
