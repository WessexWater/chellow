import csv
from decimal import Decimal
from io import StringIO

from utils import match_tables

from chellow.models import (
    BillType,
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
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_219 import content
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_content(mocker, sess):
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
    source = Source.get_by_code(sess, "grid")
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
    supply_id = supply.id
    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id
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
    content(year, month, months, supply_id, user_id)
    mock_file.seek(0)
    actual = list(csv.reader(mock_file))
    expected = [
        [
            "duration_start",
            "duration_finish",
            "site_code",
            "site_name",
            "supply_id",
            "imp_mpan_core",
            "exp_mpan_core",
            "batch_reference",
            "bill_id",
            "bill_reference",
            "bill_issue_date",
            "bill_type",
            "register_read_id",
            "tpr",
            "coefficient",
            "prev_read_date",
            "prev_read_value",
            "prev_read_type",
            "pres_read_date",
            "pres_read_value",
            "pres_read_type",
        ],
        [
            "2020-01-01 00:00",
            "2020-01-31 23:30",
            "CI017",
            "Water Works",
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
    match_tables(expected, actual)
