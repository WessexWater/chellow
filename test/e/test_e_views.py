from decimal import Decimal
from io import BytesIO

from sqlalchemy import event, text
from sqlalchemy.orm import Session

from utils import match, match_repeat

from zish import dumps

from chellow.e import hh_importer
from chellow.e.views import (
    duration_report_get,
    get_era_bundles,
)
from chellow.models import (
    BatchFile,
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
    MtcLlfcSsc,
    MtcLlfcSscPc,
    MtcParticipant,
    MtcSsc,
    Participant,
    Pc,
    Site,
    Source,
    Ssc,
    VoltageLevel,
    insert_bill_types,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_read_types,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_comms_get(sess, client):
    insert_comms(sess)
    sess.commit()

    response = client.get("/e/comms")
    match(response, 200)


def test_comm_get(sess, client):
    insert_comms(sess)
    sess.commit()

    response = client.get("/e/comms/3")
    match(response, 200)


def test_channel_add_post(sess, client):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", valid_from, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
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
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
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
    era = supply.eras[0]
    sess.commit()

    data = {"imp_related": "true", "channel_type": "ACTIVE"}
    response = client.post(f"/e/eras/{era.id}/add_channel", data=data)
    match(response, 303)


def test_channel_snag_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
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
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
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
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
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
        utc_datetime(2020, 1, 1),
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
        "22 0470 7514 535",
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
    channel = era.insert_channel(sess, False, "ACTIVE")
    channel.add_snag(
        sess,
        "Missing",
        utc_datetime(2003, 8, 2, 23, 30),
        utc_datetime(2004, 7, 6, 22, 30),
    )
    sess.commit()

    regex = [r"<th>Ignored\?</th>\s*" r"<td>\s*" r"Not ignored\s*" r"</td>\s*"]
    response = client.get("/e/channel_snags/1")

    match(response, 200, "".join(regex))


def test_duration_report_get(mocker):
    mock_render_template = mocker.patch(
        "chellow.e.views.render_template", autospec=True
    )
    ct_now = ct_datetime(2021, 4, 5)
    duration_report_get(ct_now)
    month_start = to_utc(ct_datetime(2021, 3, 1))
    month_finish = to_utc(ct_datetime(2021, 3, 31, 23, 30))
    mock_render_template.assert_called_with(
        "duration_report.html",
        month_start=month_start,
        month_finish=month_finish,
    )


def test_dc_batches_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant.insert_party(sess, market_role_C, "Fusion", valid_from, None, None)
    contract = Contract.insert_dc(
        sess,
        "Fusion DC",
        participant,
        "",
        {},
        valid_from,
        None,
        {},
    )
    contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    response = client.get(f"/e/dc_batches?dc_contract_id={contract.id}")
    match(response, 200)


def test_dc_batch_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant.insert_party(sess, market_role_C, "Fusion", valid_from, None, None)
    contract = Contract.insert_dc(
        sess,
        "Fusion DC",
        participant,
        "",
        {},
        valid_from,
        None,
        {},
    )
    batch = contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    response = client.get(f"/e/dc_batches/{batch.id}")
    match(response, 200)


def test_dc_batch_upload_file_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant.insert_party(
        sess, market_role_C, "Fusion Dc Ltd", valid_from, None, None
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion", participant, "", {}, valid_from, None, {}
    )
    batch = dc_contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    response = client.get(f"/e/dc_batches/{batch.id}/upload_file")
    match(response, 200)


def test_dc_batch_file_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant.insert_party(
        sess, market_role_C, "Fusion Dc Ltd", valid_from, None, None
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion", participant, "", {}, valid_from, None, {}
    )
    batch = dc_contract.insert_batch(sess, "b1", "batch 1")
    batch_file = batch.insert_file(sess, "bills.csv", b"a bill", "csv")
    sess.commit()

    response = client.get(f"/e/dc_batch_files/{batch_file.id}")
    match(response, 200)


def test_dc_batch_file_edit_get(sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant.insert_party(sess, market_role_C, "Fusion Dc Ltd", vf, None, None)
    dc_contract = Contract.insert_dc(sess, "Fusion", participant, "", {}, vf, None, {})
    batch = dc_contract.insert_batch(sess, "b1", "batch 1")
    batch_file = batch.insert_file(sess, "bills.csv", b"a bill", "csv")
    sess.commit()

    response = client.get(f"/e/dc_batch_files/{batch_file.id}/edit")
    match(response, 200)


def test_dc_contract_edit_post_error(sess, client):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_dc(
        sess, "Lowri Beck", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    sess.commit()

    data = {}

    response = client.post(f"/e/dc_contracts/{contract.id}/edit", data=data)

    match(response, 400, r"Lowri Beck")


def test_dc_contract_get(sess, client):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_dc(
        sess, "Lowri Beck", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    sess.commit()

    response = client.get(f"/e/dc_contracts/{contract.id}")

    match(response, 200)


def test_dc_contracts_add_post(sess, client):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )

    sess.commit()

    data = {
        "participant_id": str(participant.id),
        "name": "NHH DC contract",
        "start_year": "2000",
        "start_month": "01",
        "start_day": "03",
        "start_hour": "00",
        "start_minute": "00",
        "has_finished": "false",
    }
    response = client.post("/e/dc_contracts/add", data=data)

    match(response, 303, r"/dc_contracts/2")

    # The post has the effect of starting the new importer thread. This line
    # is to stop the thread.
    hh_importer.shutdown()


def test_dc_contracts_hh_imports_get(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    contract = Contract.insert_dc(sess, "DC 2000", participant, "", {}, vf, None, {})
    sess.commit()

    response = client.get(f"/e/dc_contracts/{contract.id}/hh_imports")
    match(response, 200)


def test_dc_contracts_hh_imports_post(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    contract = Contract.insert_dc(sess, "DC 2000", participant, "", {}, vf, None, {})
    sess.commit()

    file_name = "hh.simple.csv"
    f = BytesIO(b"MPAN core, Channel Type, Time, Value, Status\n")

    data = {"import_file": (f, file_name)}
    response = client.post(f"/e/dc_contracts/{contract.id}/hh_imports", data=data)
    match(response, 303)
    match_repeat(
        client, f"/e/dc_contracts/{contract.id}/hh_imports/0", "completed successfully"
    )


def test_dc_auto_importer_get(sess, client):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_dc(
        sess, "DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    sess.commit()

    response = client.get(f"/e/dc_contracts/{contract.id}/auto_importer")

    match(response, 200)


def test_dc_auto_importer_post(mocker, sess, client):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_dc(
        sess, "DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    sess.commit()

    mocker.patch("chellow.e.views.chellow.e.hh_importer")

    response = client.post(f"/e/dc_contracts/{contract.id}/auto_importer")

    match(response, 303)


def test_dc_contract_edit_delete(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_C, "DC Ltd.", vf, None, None)
    contract = Contract.insert_dc(sess, "DC 2000", participant, "", {}, vf, None, {})
    sess.commit()

    response = client.delete(f"/e/dc_contracts/{contract.id}/edit")

    match(response, 303)


def test_dc_contract_edit_post(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    party = participant.insert_party(sess, market_role_C, "DC Ltd.", vf, None, None)
    properties = {"sora": "ai"}
    contract = Contract.insert_dc(
        sess, "DC 2000", participant, "", properties, vf, None, {}
    )
    sess.commit()

    data = {
        "party_id": str(party.id),
        "name": "Dynamat data",
        "charge_script": """
def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    bill = ds.dc_bill
    for hh in ds.hh_data:
        if hh['utc-is-month-end']:
            bill['net-gbp'] += 7
""",
    }

    response = client.post(f"/e/dc_contracts/{contract.id}/edit", data=data)

    match(response, 303)
    sess.rollback()
    assert contract.make_properties() == properties


def test_dc_rate_script_add_post(sess, client):
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    sess.commit()

    data = {
        "start_year": "2010",
        "start_month": "05",
        "start_day": "01",
        "start_hour": "01",
        "start_minute": "00",
        "insert": "Insert",
    }
    response = client.post(
        f"/e/dc_contracts/{dc_contract.id}/add_rate_script", data=data
    )

    match(response, 303, r"/dc_rate_scripts/3")


def test_dc_rate_script_edit_get(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    dc_rate_script = dc_contract.rate_scripts[0]
    sess.commit()

    response = client.get(f"/e/dc_rate_scripts/{dc_rate_script.id}/edit")

    match(response, 200)


def test_dc_bill_import(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, valid_from, None, {}
    )
    batch = dc_contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    data = {"import_bills": "Import Bills"}
    response = client.post(f"/e/dc_batches/{batch.id}", data=data)
    match(response, 303, r"/dc_bill_imports/0")

    response = client.get("/e/dc_bill_imports/0")
    match(
        response,
        200,
        r"All the bills have been successfully loaded and attached to the batch\.",
    )


def test_dtc_meter_types(client):
    response = client.get("/e/dtc_meter_types")

    match(response, 200)


def test_em_site(sess, client):
    site = Site.insert(sess, "CI017", "Water Works")
    sess.commit()

    response = client.get(f"/e/sites/{site.id}/energy_management")

    match(response, 200)


def test_em_totals(sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        vf,
        None,
        bank_holiday_rate_script,
    )
    sess.commit()

    client.get(f"/e/sites/{site.id}/energy_management/totals")

    response = match_repeat(
        client, f"/e/sites/{site.id}/energy_management/totals?mem_id=0", "table"
    )

    assert response.status_code == 286


def test_em_hh_data(sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        vf,
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, vf, None, {}
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
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
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
        "22 0470 7514 535",
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
    channel = era.insert_channel(sess, True, "ACTIVE")
    hh_dict = {
        "start_date": to_utc(ct_datetime(2020, 1, 1)),
        "status": "A",
        "value": Decimal("88.7"),
    }
    channel.add_hh_data(sess, [hh_dict])
    sess.commit()

    response = client.get(
        f"/e/sites/{site.id}/energy_management/hh_data?year=2020&month=01"
    )

    match(response, 200, "88.7")


def test_era_edit_get(client, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
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
        utc_datetime(2020, 1, 1),
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
        "22 0470 7514 535",
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

    sess.commit()

    response = client.get(f"/e/eras/{era.id}/edit")

    match(response, 200)


def test_era_edit_form_get(client, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
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
        utc_datetime(2020, 1, 1),
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
        "22 0470 7514 535",
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

    sess.commit()

    query_string = {"pc_id": pc.id, "mtc_participant_id": mtc_participant.id}

    response = client.get(f"/e/eras/{era.id}/edit/form", query_string=query_string)

    patterns = [
        r'<select name="energisation_status_id">\s*'
        r'<option value="2">De-Energised</option>\s*'
        r'<option value="1" selected>Energised</option>\s*'
        r"</select>",
        r'<select name="comm_id">',
    ]
    match(response, 200, *patterns)


def test_era_edit_form_get_ended_llfc(client, sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop", vf, None, None)
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
        vf,
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
        vf,
        to_utc(ct_datetime(2023, 1, 1)),
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
        utc_datetime(2020, 1, 1),
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
        "22 0470 7514 535",
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

    sess.commit()

    query_string = {
        "is_ended": "true",
        "pc_id": pc.id,
        "mtc_participant_id": mtc_participant.id,
        "has_imp_mpan": "true",
    }

    response = client.get(f"/e/eras/{era.id}/edit/form", query_string=query_string)

    patterns = [
        r'<select name="imp_llfc_id">\s*'
        r'<option value="1">510 PC 5-8 &amp; HH HV</option>\s*'
        r"</select>",
    ]
    match(response, 200, *patterns)


def test_dno_rate_script_edit_post(sess, client):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "WPD")
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    dno_contract = Contract.insert_dno(
        sess, dno.dno_code, participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    rs = dno_contract.rate_scripts[0]
    sess.commit()

    data = {
        "script": "{}",
        "has_finished": "false",
        "start_year": 2022,
        "start_month": 10,
        "start_day": 1,
        "start_hour": 0,
        "start_minute": 0,
    }

    response = client.post(f"/e/dno_rate_scripts/{rs.id}/edit", data=data)

    match(response, 303)


def test_era_edit_post_hh(client, sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
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
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
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
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
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
        utc_datetime(2020, 1, 1),
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
        "22 0470 7514 535",
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

    sess.commit()

    data = {
        "start_year": "2000",
        "start_month": "01",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
        "mop_contract_id": str(mop_contract.id),
        "mop_account": "773",
        "dc_contract_id": str(dc_contract.id),
        "dc_account": "ghyy3",
        "msn": "hgjeyhuw",
        "pc_id": str(pc.id),
        "mtc_participant_id": mtc_participant.id,
        "cop_id": str(cop.id),
        "comm_id": str(comm.id),
        "ssc_id": "",
        "energisation_status_id": str(energisation_status.id),
        "dtc_meter_type_id": str(dtc_meter_type.id),
        "has_imp_mpan": "true",
        "imp_mpan_core": "22 0470 7514 535",
        "imp_llfc_id": llfc.id,
        "imp_supplier_contract_id": str(imp_supplier_contract.id),
        "imp_supplier_account": "7748",
        "imp_sc": "361",
    }
    response = client.post(f"/e/eras/{era.id}/edit", data=data)

    patterns = []
    match(response, 303, *patterns)


def test_era_edit_post_nhh(client, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    pc = Pc.insert(sess, "03", "hh", utc_datetime(2000, 1, 1), None)
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
    mtc = Mtc.insert(
        sess,
        "845",
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    ssc = Ssc.insert(sess, "0001", "All", True, utc_datetime(1996, 1), None)
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, valid_from, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, valid_from, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, valid_from, None)
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2020, 1, 1),
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
        ssc.code,
        energisation_status,
        dtc_meter_type,
        "22 0470 7514 535",
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

    sess.commit()

    data = {
        "start_year": "2000",
        "start_month": "01",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
        "mop_contract_id": str(mop_contract.id),
        "mop_account": "773",
        "dc_contract_id": str(dc_contract.id),
        "dc_account": "ghyy3",
        "msn": "hgjeyhuw",
        "pc_id": str(pc.id),
        "mtc_participant_id": mtc_participant.id,
        "cop_id": str(cop.id),
        "comm_id": str(comm.id),
        "ssc_id": ssc.id,
        "energisation_status_id": str(energisation_status.id),
        "dtc_meter_type_id": str(dtc_meter_type.id),
        "has_imp_mpan": "true",
        "imp_mpan_core": "22 0470 7514 535",
        "imp_llfc_id": llfc.id,
        "imp_supplier_contract_id": str(imp_supplier_contract.id),
        "imp_supplier_account": "7748",
        "imp_sc": "361",
    }
    response = client.post(f"/e/eras/{era.id}/edit", data=data)

    patterns = []
    match(response, 303, *patterns)


def test_era_edit_post_fail(client, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
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
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
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
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
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
        utc_datetime(2020, 1, 1),
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
        "22 0470 7514 535",
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

    sess.commit()

    data = {}
    response = client.post(f"/e/eras/{era.id}/edit", data=data)

    match(response, 400)


def test_get_era_bundles_bill_after_supply_end(sess, client):
    """Check that a bill starting after the end of a supply still gets
    shown.
    """
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
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
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31),
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    insert_bill_types(sess)
    bill_type_N = BillType.get_by_code(sess, "N")
    batch.insert_bill(
        sess,
        "ytgeklf",
        "s77349",
        utc_datetime(2020, 2, 10),
        utc_datetime(2020, 2, 2),
        utc_datetime(2020, 3, 1),
        Decimal(0),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        bill_type_N,
        {},
        supply,
    )
    sess.commit()

    bundles = get_era_bundles(sess, supply)

    assert len(bundles[0]["imp_bills"]["bill_dicts"]) == 1


def test_get_era_bundles_bill_in_correct_era(sess, client):
    """Where there's more than one era, check that a bill starting in a
    previous era actuall appears in that era.
    """
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    participant = Participant.insert(sess, "hhak", "AK Industries")
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
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
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
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31),
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
    supply.insert_era_at(sess, utc_datetime(2020, 1, 15))
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    insert_bill_types(sess)
    bill_type_N = BillType.get_by_code(sess, "N")
    batch.insert_bill(
        sess,
        "ytgeklf",
        "s77349",
        utc_datetime(2020, 2, 10),
        utc_datetime(2020, 1, 2),
        utc_datetime(2020, 1, 3),
        Decimal(0),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        bill_type_N,
        {},
        supply,
    )
    sess.commit()

    bundles = get_era_bundles(
        sess, supply, latest_start_date=to_utc(ct_datetime(2022, 5, 1))
    )

    assert len(bundles[0]["imp_bills"]["bill_dicts"]) == 0
    assert len(bundles[1]["imp_bills"]["bill_dicts"]) == 1


def test_llfc_eidt_post(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        vf,
        None,
    )
    sess.commit()

    data = {"voltage_level_id": voltage_level.id}
    response = client.post(f"/e/llfcs/{llfc.id}/edit", data=data)
    match(response, 303)


def test_mop_batches_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_M = MarketRole.insert(sess, "M", "MOP")
    participant.insert_party(sess, market_role_M, "Fusion", valid_from, None, None)
    contract = Contract.insert_mop(
        sess,
        "Fusion MOP",
        participant,
        "",
        {},
        valid_from,
        None,
        {},
    )
    contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    response = client.get(f"/e/mop_batches?mop_contract_id={contract.id}")
    match(response, 200)


def test_mop_batch_import_bills_full(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    participant = Participant.insert(sess, "hhak", "AK Industries")
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
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", valid_from, None)
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    data = {"import_bills": "Import Bills"}
    response = client.post(f"/e/mop_batches/{batch.id}", data=data)
    match(response, 303, r"/mop_bill_imports/0")

    response = client.get("/e/mop_bill_imports/0")
    match(
        response,
        200,
        r"All the bills have been successfully loaded and attached to " r"the batch\.",
    )


def test_mop_batch_upload_file_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", valid_from, None, None
    )
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, valid_from, None, {}
    )
    batch = mop_contract.insert_batch(sess, "b1", "batch 1")
    batch.insert_file(sess, "bills.csv", b"a bill", "csv")
    sess.commit()

    response = client.get(f"/e/mop_batches/{batch.id}/upload_file")
    match(response, 200)


def test_mop_batch_upload_file_post(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    file_name = "bills.xlsx"
    file_bytes = b"a bill"
    f = BytesIO(file_bytes)

    data = {"parser_name": "activity_mop_stark_xlsx", "import_file": (f, file_name)}
    response = client.post(f"/e/mop_batches/{batch.id}/upload_file", data=data)
    match(response, 303, r"/e/mop_batches/1#batch_file_1")

    sess.rollback()
    batch_file = BatchFile.get_by_id(sess, 1)

    assert batch_file.data == file_bytes


def test_mop_contract_edit_delete(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_M = MarketRole.insert(sess, "M", "MOP")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_M, "MOP Ltd.", vf, None, None)
    contract = Contract.insert_mop(sess, "MOP 2000", participant, "", {}, vf, None, {})
    sess.commit()

    response = client.delete(f"/e/mop_contracts/{contract.id}/edit")

    match(response, 303)


def test_mop_batch_file_get(sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_M = MarketRole.insert(sess, "M", "MOP")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    contract = Contract.insert_mop(sess, "Fusion", participant, "", {}, vf, None, {})
    batch = contract.insert_batch(sess, "b1", "batch 1")
    batch_file = batch.insert_file(sess, "bills.csv", b"a bill", "csv")
    sess.commit()

    response = client.get(f"/e/mop_batch_files/{batch_file.id}")
    match(response, 200)


def test_mop_rate_script_edit_get(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_M = MarketRole.insert(sess, "M", "HH Dc")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_M, "Fusion MOP", vf, None, None)
    mop_contract = Contract.insert_mop(
        sess, "Fusion MOP", participant, "", {}, vf, None, {}
    )
    mop_rate_script = mop_contract.rate_scripts[0]
    sess.commit()

    response = client.get(f"/e/mop_rate_scripts/{mop_rate_script.id}/edit")

    match(response, 200)


def test_mtcs_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    Mtc.insert(sess, "001", True, True, valid_from, None)
    sess.commit()
    response = client.get("/e/mtcs")
    match(response, 200)


def test_mtc_participants(sess, client):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    sess.commit()
    response = client.get(
        "/e/mtc_participants", query_string={"participant_id": participant.id}
    )

    match(response, 200)


def test_mtc_participant(sess, client):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    mtc = Mtc.insert(sess, "001", True, True, valid_from, None)
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "an mtc participant",
        True,
        True,
        meter_type,
        meter_payment_type,
        3,
        valid_from,
        None,
    )

    sess.commit()
    response = client.get(f"/e/mtc_participants/{mtc_participant.id}")

    match(response, 200)


def test_mtc_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    mtc = Mtc.insert(sess, "001", True, True, valid_from, None)
    sess.commit()
    response = client.get(f"/e/mtcs/{mtc.id}")
    match(response, 200)


def test_mtc_ssc(sess, client):
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_R, "WPD", utc_datetime(2000, 1, 1), None, "22"
    )
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    mtc = Mtc.insert(sess, "001", True, True, valid_from, None)
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "an mtc participant",
        True,
        True,
        meter_type,
        meter_payment_type,
        3,
        valid_from,
        None,
    )
    ssc = Ssc.insert(sess, "0001", "All", True, utc_datetime(1996, 1), None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, valid_from, None)

    sess.commit()
    response = client.get(f"/e/mtc_sscs/{mtc_ssc.id}")

    match(response, 200)


def test_mtc_llfc_ssc_pcs_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")
    mtc = Mtc.insert(sess, "001", True, True, valid_from, None)
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
    mtc_participant = MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "an mtc participant",
        True,
        True,
        meter_type,
        meter_payment_type,
        3,
        valid_from,
        None,
    )
    ssc = Ssc.insert(sess, "0001", "All", True, utc_datetime(1996, 1), None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, valid_from, None)
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
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, valid_from, None)
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    combo = MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, valid_from, None)

    sess.commit()
    response = client.get(f"/e/mtc_llfc_ssc_pcs/{combo.id}")

    match(response, 200)


def test_mtc_llfc_ssc_pc_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 4, 1))
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(sess, market_role_R, "WPD", valid_from, None, "22")

    sess.commit()
    query_string = {
        "dno_id": dno.id,
    }
    response = client.get("/e/mtc_llfc_ssc_pcs", query_string=query_string)

    match(response, 200)


class Sess:
    def __init__(self, *results):
        self.it = iter(results)

    def query(self, *arg):
        return self

    def join(self, *arg):
        return self

    def order_by(self, *arg):
        return self

    def filter(self, *arg):
        return self

    def scalar(self, *arg):
        return next(self.it)

    def first(self, *arg):
        return next(self.it)


def test_read_add_get_no_existing_era(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
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
        sess, "Fusion", participant, "", {}, vf, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    insert_cops(sess)
    insert_comms(sess)
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
    insert_sources(sess)
    pc = Pc.insert(sess, "00", "", vf, None)
    cop = Cop.get_by_code(sess, "5")
    comm = Comm.get_by_code(sess, "GSM")
    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
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
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31),
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    insert_bill_types(sess)
    bill_type_N = BillType.get_by_code(sess, "N")
    bill = batch.insert_bill(
        sess,
        "xx",
        "4432",
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2018, 1, 3)),
        to_utc(ct_datetime(2018, 1, 5)),
        Decimal("482"),
        Decimal("5.67"),
        Decimal("0.00"),
        Decimal("8.55"),
        bill_type_N,
        {"vat": {5: {"vat": Decimal("0"), "net": Decimal("34.66")}}},
        supply,
    )
    insert_read_types(sess)

    sess.commit()

    response = client.get(f"/e/supplier_bills/{bill.id}/add_read")
    patterns = []
    match(response, 200, *patterns)


def test_read_add_get_existing_era(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
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
        sess, "Fusion", participant, "", {}, vf, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    insert_cops(sess)
    insert_comms(sess)
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
    insert_sources(sess)
    pc = Pc.insert(sess, "00", "", vf, None)
    cop = Cop.get_by_code(sess, "5")
    comm = Comm.get_by_code(sess, "GSM")
    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
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
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31),
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    insert_bill_types(sess)
    bill_type_N = BillType.get_by_code(sess, "N")
    bill = batch.insert_bill(
        sess,
        "xx",
        "4432",
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2020, 1, 3)),
        to_utc(ct_datetime(2020, 1, 5)),
        Decimal("482"),
        Decimal("5.67"),
        Decimal("0.00"),
        Decimal("8.55"),
        bill_type_N,
        {"vat": {5: {"vat": Decimal("0"), "net": Decimal("34.66")}}},
        supply,
    )
    insert_read_types(sess)

    sess.commit()

    response = client.get(f"/e/supplier_bills/{bill.id}/add_read")
    patterns = [
        r'<select name="present_type_id">\s*'
        r'<option value="1">A Actual Change of Supplier Read</option>'
    ]
    match(response, 200, *patterns)


def test_site_add_e_supply_form_get(client, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
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
    Contract.insert_mop(sess, "Fusion", participant, "", {}, vf, None, {})
    Contract.insert_dc(sess, "Fusion DC 2000", participant, "", {}, vf, None, {})
    insert_cops(sess)
    insert_comms(sess)
    insert_dtc_meter_types(sess)
    Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    Contract.insert_dno(sess, dno.dno_code, participant, "", {}, vf, None, {})
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", vf, None)
    mtc = Mtc.insert(sess, "845", False, True, vf, None)
    mtc_participant_hh = MtcParticipant.insert(
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
    mtc = Mtc.insert(sess, "001", False, True, vf, None)
    MtcParticipant.insert(
        sess,
        mtc,
        participant,
        "nhh",
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
    MtcLlfc.insert(sess, mtc_participant_hh, llfc, vf, None)
    insert_sources(sess)
    insert_energisation_statuses(sess)
    Pc.insert(sess, "00", "", vf, None)

    sess.commit()

    query_string = {
        "dno_id": "",
        "source_id": "",
        "pc_id": "",
        "mtc_participant_id": "",
    }
    response = client.get(
        f"/e/sites/{site.id}/add_e_supply/form", query_string=query_string
    )
    patterns = [
        r'<select name="comm_id">\s*'
        r'<option value="3">GPRS General Packet Radio Service</option>\s*',
        r'<select name="mtc_participant_id">\s*'  # Make sure only HH MTCs are shown
        r'<option value="1">845 HH COP5 And Above With Comms</option>\s*'
        r"</select>\s*",
        r'<select name="dtc_meter_type_id">\s*'
        r'<option value="">Unmetered</option>\s*'
        r'<option value="23">'
        r"2ADEF Single Element with ALCS, Boost "
        r"Function and APC that is compliant with SMETS2"
        r"</option>\s*",
    ]
    match(response, 200, *patterns)


def test_site_add_e_supply_post_hh(sess, client):
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
        sess, "Fusion", participant, "", {}, vf, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
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
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
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
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    sess.commit()

    data = {
        "source_id": source.id,
        "gsp_group_id": gsp_group.id,
        "mop_contract_id": mop_contract.id,
        "dc_contract_id": dc_contract.id,
        "dc_account": "dc1",
        "msn": "jjl4",
        "dno_id": dno.id,
        "pc_id": pc.id,
        "mtc_participant_id": mtc_participant.id,
        "cop_id": cop.id,
        "comm_id": comm.id,
        "ssc_id": "",
        "dtc_meter_type_id": dtc_meter_type.id,
        "start_year": "2021",
        "start_month": "01",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
        "mop_account": "ma1",
        "imp_mpan_core": "22 6644 1123 880",
        "imp_supplier_contract_id": imp_supplier_contract.id,
        "imp_supplier_account": "sup1",
        "imp_sc": "200",
        "imp_llfc_id": llfc.id,
        "energisation_status_id": energisation_status.id,
        "name": "main",
    }
    response = client.post(f"/e/sites/{site.id}/add_e_supply", data=data)
    match(response, 303, "/e/supplies")


def test_site_add_e_supply_post_nhh(sess, client):
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
        sess, "Fusion", participant, "", {}, vf, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    pc = Pc.insert(sess, "03", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
    )
    dno = participant.insert_party(sess, market_role_R, "WPD", vf, None, "22")
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
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
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    ssc = Ssc.insert(sess, "0001", "All", True, utc_datetime(1996, 1, 1), None)
    MtcLlfc.insert(sess, mtc_participant, llfc, vf, None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, vf, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, vf, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, vf, None)
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    sess.commit()

    data = {
        "source_id": source.id,
        "gsp_group_id": gsp_group.id,
        "mop_contract_id": mop_contract.id,
        "dc_contract_id": dc_contract.id,
        "dc_account": "dc1",
        "msn": "jjl4",
        "dno_id": dno.id,
        "pc_id": pc.id,
        "mtc_participant_id": mtc_participant.id,
        "cop_id": cop.id,
        "comm_id": comm.id,
        "ssc_id": ssc.id,
        "dtc_meter_type_id": dtc_meter_type.id,
        "start_year": "2021",
        "start_month": "01",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
        "mop_account": "ma1",
        "imp_mpan_core": "22 6644 1123 880",
        "imp_supplier_contract_id": imp_supplier_contract.id,
        "imp_supplier_account": "sup1",
        "imp_sc": "200",
        "imp_llfc_id": llfc.id,
        "energisation_status_id": energisation_status.id,
        "name": "main",
    }
    response = client.post(f"/e/sites/{site.id}/add_e_supply", data=data)
    match(response, 303)


def test_site_add_e_supply_post_fail(client, sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess,
        "bank_holidays",
        "",
        {},
        vf,
        None,
        bank_holiday_rate_script,
    )
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
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    insert_comms(sess)
    cop = Cop.get_by_code(sess, "5")
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
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(sess, "CR", "Credit", vf, None)
    mtc = Mtc.insert(sess, "845", False, True, vf, None)
    MtcParticipant.insert(
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
    dno.insert_llfc(sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, vf, None)
    dno.insert_llfc(sess, "521", "Export (HV)", voltage_level, False, False, vf, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    sess.commit()

    data = {
        "source_id": str(source.id),
        "name": "Bob",
        "start_date_year": "2000",
        "start_date_month": "01",
        "start_date_day": "01",
        "start_date_hour": "00",
        "start_date_minute": "00",
        "insert_electricity": "Insert Electricity",
        "mop_contract_id": str(mop_contract.id),
        "dc_contract_id": str(dc_contract.id),
        "pc_id": str(pc.id),
        "cop_id": str(cop.id),
        "imp_supplier_contract_id": str(imp_supplier_contract.id),
        "energisation_status_id": str(energisation_status.id),
        "gsp_group_id": str(gsp_group.id),
    }
    response = client.post(f"/e/sites/{site.id}/add_e_supply", data=data)

    match(response, 400)


def test_site_hh_data(sess, client):
    site = Site.insert(sess, "CI017", "Water Works")
    sess.commit()

    query_string = {
        "start_year": "2022",
        "start_month": "3",
    }
    response = client.get(f"/e/sites/{site.id}/hh_data", query_string=query_string)

    patterns = [
        r'<input type="hidden" name="start_year" value="2022">',
        r'<input type="hidden" name="start_month" value="3">',
    ]
    match(response, 200, *patterns)


def test_supplier_batches_get(sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_X, "Fusion", vf, None, None)
    contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier",
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
    contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    response = client.get(f"/e/supplier_batches?supplier_contract_id={contract.id}")
    match(response, 200)


def test_supplier_batch_edit_delete(sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    response = client.delete(f"/e/supplier_batches/{batch.id}/edit")
    match(response, 303)


def test_supplier_batch_get(sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, vf, None, {}
    )
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    response = client.get(f"/e/supplier_batches/{batch.id}")
    match(response, 200)


def test_supplier_batch_get_vat(sess, client):
    """When vat is zero, but vat net breakdown non-zero"""
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
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
        "HH COP5",
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
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31),
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    insert_bill_types(sess)
    bill_type_N = BillType.get_by_code(sess, "N")
    batch.insert_bill(
        sess,
        "xx",
        "4432",
        to_utc(ct_datetime(2020, 1, 1)),
        to_utc(ct_datetime(2018, 1, 1)),
        to_utc(ct_datetime(2018, 1, 3)),
        Decimal("482"),
        Decimal("5.67"),
        Decimal("0.00"),
        Decimal("8.55"),
        bill_type_N,
        {"vat": {5: {"vat": Decimal("0"), "net": Decimal("34.66")}}},
        supply,
    )
    sess.commit()

    response = client.get(f"/e/supplier_batches/{batch.id}")
    patterns = [
        r"<thead>\s*",
        r"<th>VAT %</th>\s",
        r"<th>Net GBP</th>\s*",
        r"<th>VAT GBP</th>\s*",
        r"</thead>\s*",
        r"<tbody>\s*" r"<tr>\s*" r"<td>5%</td>\s*",
        r"<td>£34.66</td>\s*",
        r"<td>£0.00</td>\s*",
        r"</tr>\s*",
        r"</tbody>\s*",
    ]
    match(response, 200, *patterns)


def test_supplier_batch_post_import_bills(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        valid_from,
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()
    data = {"import_bills": "Import"}
    response = client.post(f"/e/supplier_batches/{batch.id}", data=data)
    match(response, 200)

    match_repeat(
        client,
        "/e/supplier_bill_imports/0",
        r"All the bills have been successfully loaded and attached to the batch.",
        seconds=5,
    )


def test_supplier_batch_post_delete_import_bills(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        valid_from,
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()
    data = {"delete_import_bills": "Import"}
    response = client.post(f"/e/supplier_batches/{batch.id}", data=data)
    match(response, 200)

    response = client.get("/e/supplier_bill_imports/0")
    match(
        response,
        200,
        r"All the bills have been successfully loaded and attached to the batch\.",
    )


def test_supplier_batch_upload_file_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        valid_from,
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    sess.commit()

    response = client.get(f"/e/supplier_batches/{batch.id}/upload_file")
    match(response, 200)


def test_supplier_batch_file_edit_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        valid_from,
        None,
        {},
    )
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    batch_file = batch.insert_file(sess, "afile.csv", b"", "csv")
    sess.commit()

    response = client.get(f"/e/supplier_batch_files/{batch_file.id}/edit")
    match(response, 200)


def test_supplier_bill_add_post(sess, client):
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
        vf,
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    insert_bill_types(sess)
    bill_type_N = BillType.get_by_code(sess, "N")
    sess.commit()

    data = {
        "mpan_core": "22 7867 6232 781",
        "account": "hrghj88",
        "reference": "74hjkgjk",
        "issue_year": "2020",
        "issue_month": "02",
        "issue_day": "10",
        "issue_hour": "00",
        "issue_minute": "00",
        "start_year": "2020",
        "start_month": "02",
        "start_day": "02",
        "start_hour": "00",
        "start_minute": "00",
        "finish_year": "2020",
        "finish_month": "03",
        "finish_day": "01",
        "finish_hour": "00",
        "finish_minute": "00",
        "kwh": "0",
        "net": "0.0",
        "vat": "0.0",
        "gross": "0.0",
        "bill_type_id": bill_type_N.id,
        "breakdown": "",
    }
    response = client.post(f"/e/supplier_batches/{batch.id}/add_bill", data=data)
    match(
        response,
        400,
        "<li>Problem parsing the field breakdown as Zish: No Zish value found.</li>",
    )


def test_supplier_bill_edit_post_breakdown_malformed(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
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
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31),
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
    batch = imp_supplier_contract.insert_batch(sess, "b1", "batch 1")
    insert_bill_types(sess)
    bill_type_N = BillType.get_by_code(sess, "N")
    bill = batch.insert_bill(
        sess,
        "ytgeklf",
        "s77349",
        utc_datetime(2020, 2, 10),
        utc_datetime(2020, 2, 2),
        utc_datetime(2020, 3, 1),
        Decimal(0),
        Decimal("0.00"),
        Decimal("0.00"),
        Decimal("0.00"),
        bill_type_N,
        {},
        supply,
    )
    sess.commit()

    data = {
        "account": "hrghj88",
        "reference": "74hjkgjk",
        "issue_year": "2020",
        "issue_month": "02",
        "issue_day": "10",
        "issue_hour": "00",
        "issue_minute": "00",
        "start_year": "2020",
        "start_month": "02",
        "start_day": "02",
        "start_hour": "00",
        "start_minute": "00",
        "finish_year": "2020",
        "finish_month": "03",
        "finish_day": "01",
        "finish_hour": "00",
        "finish_minute": "00",
        "kwh": "0",
        "net": "0.0",
        "vat": "0.0",
        "gross": "0.0",
        "bill_type_id": bill_type_N.id,
        "breakdown": "{",
    }
    response = client.post(f"/e/supplier_bills/{bill.id}/edit", data=data)
    match(
        response,
        400,
        "<li>Problem parsing the field breakdown as Zish: Problem at line 1 and "
        "character 2: After this opening &#39;{&#39;, a key or a closing &#39;}&#39; "
        "was expected, but reached the end of the document instead.</li>",
    )


def test_supplier_contracts_add_post(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    sess.commit()

    data = {
        "participant_id": participant.id,
        "name": "Fusion Supplier 2000",
        "charge_script": "",
        "start_year": "2000",
        "start_month": "1",
        "start_day": "1",
        "start_hour": "00",
        "start_minute": "00",
        "properties": "{}",
    }
    response = client.post("/e/supplier_contracts/add", data=data)
    match(response, 303)


def test_supplier_contract_edit_post_missing_properties(sess, client):
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    party = participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    sess.commit()

    data = {
        "party_id": party.id,
        "name": "Fusion Ltd",
        "charge_script": "if",
    }
    response = client.post(f"/e/supplier_contracts/{contract.id}/edit", data=data)
    match(response, 400, "field properties is")


def test_supplier_contract_get(client, sess):
    sess.execute(
        text("INSERT INTO market_role (code, description) VALUES ('X', 'Supplier')")
    )
    sess.execute(text("INSERT INTO participant (code, name) VALUES ('FUSE', 'Fusion')"))
    sess.execute(
        text(
            "INSERT INTO party (market_role_id, participant_id, name, "
            "valid_from, valid_to, dno_code) "
            "VALUES (2, 2, 'Fusion Energy', '2000-01-01', null, null)"
        )
    )
    sess.execute(
        text(
            "INSERT INTO contract (name, charge_script, properties, "
            "state, market_role_id, party_id, start_rate_script_id, "
            "finish_rate_script_id) VALUES ('2020 Fusion', '{}', '{}', '{}', "
            "2, 2, null, null)"
        )
    )
    sess.execute(
        text(
            "INSERT INTO rate_script (contract_id, start_date, finish_date, "
            "script) VALUES (2, '2000-01-03', null, '{}')"
        )
    )
    sess.execute(
        text(
            "UPDATE contract set start_rate_script_id = 2, "
            "finish_rate_script_id = 2 where id = 2;"
        )
    )
    sess.commit()

    response = client.get("/e/supplier_contracts/2")

    patterns = [
        r"<tr>\s*"
        r"<th>Start Date</th>\s*"
        r"<td>2000-01-03 00:00</td>\s*"
        r"</tr>\s*"
        r"<tr>\s*"
        r"<th>Finish Date</th>\s*"
        r"<td>Ongoing</td>\s*"
        r"</tr>\s*"
    ]
    match(response, 200, *patterns)


def test_supplier_contract_add_rate_script(client, sess):
    sess.execute(
        text("INSERT INTO market_role (code, description) " "VALUES ('X', 'Supplier')")
    )
    sess.execute(
        text("INSERT INTO participant (code, name) " "VALUES ('FUSE', 'Fusion')")
    )
    sess.execute(
        text(
            "INSERT INTO party (market_role_id, participant_id, name, "
            "valid_from, valid_to, dno_code) "
            "VALUES (2, 2, 'Fusion Energy', '2000-01-01', null, null)"
        )
    )
    sess.execute(
        text(
            "INSERT INTO contract (name, charge_script, properties, "
            "state, market_role_id, party_id, start_rate_script_id, "
            "finish_rate_script_id) VALUES ('2020 Fusion', '{}', '{}', '{}', "
            "2, 2, null, null)"
        )
    )
    sess.execute(
        text(
            "INSERT INTO rate_script (contract_id, start_date, finish_date, "
            "script) VALUES (2, '2000-01-03', null, '{}')"
        )
    )
    sess.execute(
        text(
            "UPDATE contract set start_rate_script_id = 2, "
            "finish_rate_script_id = 2 where id = 2;"
        )
    )
    sess.commit()

    data = {
        "start_year": "2020",
        "start_month": "02",
        "start_day": "06",
        "start_hour": "01",
        "start_minute": "00",
        "script": "{}",
    }
    response = client.post("/e/supplier_contracts/2/add_rate_script", data=data)

    match(response, 303, r"/supplier_rate_scripts/3")

    contract = Contract.get_supplier_by_id(sess, 2)

    start_rate_script = contract.start_rate_script
    finish_rate_script = contract.finish_rate_script

    assert start_rate_script.start_date == utc_datetime(2000, 1, 3)
    assert finish_rate_script.finish_date is None


def test_supplier_rate_script_edit_get(client, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "hhak", "AK Industries")
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        valid_from,
        None,
        {},
    )
    rate_script = supplier_contract.rate_scripts[0]
    sess.commit()

    response = client.get(f"/e/supplier_rate_scripts/{rate_script.id}/edit")
    match(response, 200)


def test_supply_edit_post(client, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
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
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2020, 1, 1),
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
        "22 0470 7514 535",
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
    sess.commit()

    rolled_back = False

    @event.listens_for(Session, "after_soft_rollback")
    def do_something(session, previous_transaction):
        nonlocal rolled_back
        rolled_back = True

    data = {"supply_edit_post": ""}
    response = client.post(f"/e/supplies/{supply.id}/edit", data=data)

    match(response, 400)

    assert rolled_back


def test_supply_get(client, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
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
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
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
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    supply = site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2020, 1, 1),
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
        "22 0470 7514 535",
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
    sess.commit()
    response = client.get(f"/e/supplies/{supply.id}")

    match(response, 200)


def test_supply_months_get(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    participant.insert_party(
        sess, market_role_C, "Fusion DC", utc_datetime(2000, 1, 1), None, None
    )
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
    sess.commit()

    query_string = {
        "is_import": "true",
        "year": "2021",
        "years": "1",
    }
    response = client.get(f"/e/supplies/{supply.id}/months", query_string=query_string)
    match(response, 200)


def test_supply_hh_data(sess, client):
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
        vf,
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
        vf,
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
        vf,
        None,
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
    sess.commit()
    query_string = {
        "is_import": "true",
        "finish_year": "2021",
        "finish_month": "1",
        "months": "1",
    }
    response = client.get(f"/e/supplies/{supply.id}/hh_data", query_string=query_string)
    match(response, 200)


def test_supply_notes(sess, client):
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
        vf,
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
        vf,
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
        vf,
        None,
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
    supply.note = dumps(
        {
            "notes": [
                {"timestamp": to_utc(ct_datetime(2023, 1, 1)), "body": "note 1"},
                {"timestamp": to_utc(ct_datetime(2023, 1, 2)), "body": "note 2"},
            ]
        }
    )
    sess.commit()
    response = client.get(f"/e/supplies/{supply.id}/notes")
    match(
        response,
        200,
        r'<tbody>\s*<tr>\s*<td>\s*\[<a href="/e/supplies/1/notes/1/edit">edit</a>\]',
    )


def test_supply_virtual_bill_get(sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(sess, market_role_M, "Fusion Mop Ltd", vf, None, None)
    participant.insert_party(sess, market_role_X, "Fusion Ltc", vf, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)

    mop_charge_script = """
from chellow.utils import reduce_bill_hhs

def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]

        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))

    ds.mop_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    mop_contract = Contract.insert_mop(
        sess,
        "Fusion Mop Contract",
        participant,
        mop_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )

    dc_charge_script = """
from chellow.utils import reduce_bill_hhs

def virtual_bill_titles():
    return ['net-gbp', 'problem']

def virtual_bill(ds):
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]

        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))

    ds.dc_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""

    dc_contract = Contract.insert_dc(
        sess,
        "Fusion DC 2000",
        participant,
        dc_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    pc = Pc.insert(sess, "00", "hh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")

    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill_titles():
    return [
        'ccl-kwh', 'ccl-rate', 'ccl-gbp', 'net-gbp', 'vat-gbp', 'gross-gbp',
        'sum-msp-kwh', 'sum-msp-gbp', 'problem']

def virtual_bill(ds):
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]
        bill_hh['sum-msp-kwh'] = hh['msp-kwh']
        bill_hh['sum-msp-gbp'] = hh['msp-kwh'] * 0.1
        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat-gbp'] = 0
        bill_hh['gross-gbp'] = bill_hh['net-gbp'] + bill_hh['vat-gbp']

    ds.supplier_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    imp_supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        supplier_charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
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

    sess.commit()
    query_string = {
        "start_year": "2020",
        "start_month": "01",
        "start_day": "01",
        "start_hour": "00",
        "start_minute": "00",
        "finish_year": "2020",
        "finish_month": "01",
        "finish_day": "01",
        "finish_hour": "00",
        "finish_minute": "00",
    }
    response = client.get(
        f"/e/supplies/{supply.id}/virtual_bill", query_string=query_string
    )
    match(response, 200)
