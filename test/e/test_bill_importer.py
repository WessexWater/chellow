import csv
from collections import deque
from io import BytesIO, TextIOWrapper

from flask import g, render_template

from sqlalchemy import select

from chellow.e.bill_importer import BillImport, find_parser_names
from chellow.models import (
    Bill,
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
    VoltageLevel,
    insert_bill_types,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_status(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
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
        utc_datetime(1996, 1, 1),
        None,
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31),
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    bill_import = BillImport(batch)
    bill_import.isAlive = mocker.Mock(return_value=True)
    bill_import.status()


def test_BillImport_run(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
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
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
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
        utc_datetime(1996, 1, 1),
        None,
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, vf, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31),
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    insert_bill_types(sess)

    data = [
        "N",
        "sla;dkjhgf8u",
        "22 7867 6232 781",
        "sdalhgfuwr",
        "2025-01-01 00:00",
        "2025-03-01 00:00",
        "2025-03-31 23:30",
        "34",
        "81.53",
        "12.89",
        "16.88",
        "{}",
        "Element",
        "nrg",
        "2025-03-01 00:00",
        "2025-03-31 23:30",
        "81.53",
        '{"nrg-kwh": 981}',
    ]

    with BytesIO() as f:
        text_stream = TextIOWrapper(f, write_through=True)
        writer = csv.writer(text_stream)
        writer.writerow(data)
        f.seek(0)

        batch.insert_file(sess, "file 1", f.read(), "csv")
    sess.commit()
    importer = BillImport(batch, now=to_utc(ct_datetime(2025, 1, 1)))
    importer.run()
    sess.rollback()
    assert importer.failed_bills == []
    assert importer.log == deque(
        [
            "2025-01-01 00:00:00 - All the bills have been successfully loaded and "
            "attached to the batch.",
            "2025-01-01 00:00:00 - Starting to parse the file file 1 with 'csv'.",
            "2025-01-01 00:00:00 - Importing bills from batch b1.",
        ]
    )
    bill = sess.scalars(select(Bill)).one()
    assert len(bill.elements) == 1


def test_supplier_bill_import_html(mocker, app):
    with app.app_context():
        with app.test_request_context():
            g.user = None
            g.config = {}
            batch = mocker.Mock()
            failed_bills = [{"error": "MPAN not found"}]
            failed_max_registers = 0
            render_template(
                "/e/supplier_bill_import.html",
                batch=batch,
                failed_bills=failed_bills,
                failed_max_registers=failed_max_registers,
            )


def test_find_parser_names():
    assert len(find_parser_names()) > 0
