from decimal import Decimal
from io import StringIO

from chellow.models import (
    BillType,
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
    ReadType,
    Site,
    Source,
    Tpr,
    User,
    UserRole,
    VoltageLevel,
    insert_bill_types,
    insert_comms,
    insert_cops,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_219 import content
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_content(mocker, sess):
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
    dno = participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
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
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
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
    batch = imp_supplier_contract.insert_batch(sess, "a", "batch")

    insert_bill_types(sess)
    bill_type = BillType.get_by_code(sess, "N")
    bill = batch.insert_bill(
        sess,
        "xxx",
        "543",
        to_utc(ct_datetime(2020, 2, 3)),
        to_utc(ct_datetime(2020, 1, 3)),
        to_utc(ct_datetime(2020, 1, 6)),
        Decimal("0"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        bill_type,
        {},
        supply,
    )
    tpr = Tpr.insert(sess, "00001", False, True)
    read_type = ReadType.insert(sess, "A", "Actual")
    bill.insert_read(
        sess,
        tpr,
        Decimal(1),
        "kWh",
        "5457339",
        "3782897",
        to_utc(ct_datetime(2020, 1, 3)),
        Decimal("66"),
        read_type,
        to_utc(ct_datetime(2020, 1, 5)),
        Decimal("100"),
        read_type,
    )

    sess.commit()
    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_219.open_file", return_value=mock_file)
    year = 2020
    month = 1
    months = 1
    supply_id = supply.id
    content(year, month, months, supply_id, user.id)
    actual = mock_file.getvalue()
    expected_lines = [
        [
            "Duration Start",
            "Duration Finish",
            "Supply Id",
            "Import MPAN Core",
            "Export MPAN Core",
            "Batch Reference",
            "Bill Id",
            "Bill Reference",
            "Bill Issue Date",
            "Bill Type",
            "Register Read Id",
            "TPR",
            "Coefficient",
            "Previous Read Date",
            "Previous Read Value",
            "Previous Read Type",
            "Present Read Date",
            "Present Read Value",
            "Present Read Type",
        ],
        [
            "2020-01-01 00:00",
            "2020-01-31 23:30",
            "1",
            "22 7867 6232 781",
            "",
            "a",
            "1",
            "543",
            "2020-02-03 00:00",
            "N",
            "1",
            "00001",
            "1",
            "2020-01-03 00:00",
            "66",
            "A",
            "2020-01-05 00:00",
            "100",
            "A",
        ],
    ]
    expected = "\n".join(",".join(line) for line in expected_lines) + "\n"
    assert actual == expected
