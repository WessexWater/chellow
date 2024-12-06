from csv import reader
from decimal import Decimal
from io import StringIO


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
    Site,
    Source,
    User,
    UserRole,
    VoltageLevel,
    insert_bill_types,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_generator_types,
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_bills import content
from chellow.utils import ct_datetime, to_utc, utc_datetime


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
    supply = site.insert_e_supply(
        sess,
        source_grid,
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

    batch = imp_supplier_contract.insert_batch(sess, "b", "b")
    insert_bill_types(sess)
    bill_type = BillType.get_by_code(sess, "N")
    batch.insert_bill(
        sess,
        "acc",
        "ref",
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2019, 1, 1)),
        to_utc(ct_datetime(2019, 1, 31)),
        Decimal("0"),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        bill_type,
        {"vat": {5: {"net": 3, "vat": 6}}},
        supply,
    )

    editor = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "xxx", editor, None)
    user_id = user.id

    sess.commit()

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_bills.open_file", return_value=mock_file)

    content(user_id, batch.id)
    mock_file.seek(0)
    table = [row for row in reader(mock_file)]

    expected = [
        [
            "supplier_contract",
            "batch_reference",
            "bill_reference",
            "imp_mpan_core",
            "account",
            "issued",
            "from",
            "to",
            "kwh",
            "net",
            "vat",
            "gross",
            "type",
            "vat_1_percent",
            "vat_1_net",
            "vat_1_vat",
            "vat_2_percent",
            "vat_2_net",
            "vat_2_vat",
            "breakdown",
        ],
        [
            "Fusion Supplier 2000",
            "b",
            "ref",
            "22 7867 6232 781",
            "acc",
            "2020-01-01 00:00",
            "2019-01-01 00:00",
            "2019-01-31 00:00",
            "0",
            "0.00",
            "0.00",
            "0.00",
            "N",
            "",
            "3",
            "6",
            "",
            "",
            "",
            '{\n  "vat": {\n    5: {\n      "net": 3,'
            '\n      "vat": 6,\n    },\n  },\n}',
        ],
    ]
    print(table)
    assert expected == table
