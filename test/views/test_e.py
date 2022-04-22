from datetime import datetime as Datetime
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook

from sqlalchemy import event
from sqlalchemy.orm import Session

from utils import match

from chellow import hh_importer
from chellow.models import (
    BatchFile,
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
    MtcLlfcSsc,
    MtcLlfcSscPc,
    MtcParticipant,
    MtcSsc,
    Participant,
    Pc,
    Scenario,
    Site,
    Source,
    Ssc,
    VoltageLevel,
    insert_bill_types,
    insert_comms,
    insert_cops,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime
from chellow.views.e import (
    csv_supplies_duration_get,
    get_era_bundles,
    read_add_get,
)


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
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
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
        utc_datetime(2020, 1, 1),
        gsp_group,
        mop_contract,
        "773",
        dc_contract,
        "ghyy3",
        "hgjeyhuw",
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
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


def test_csv_supplies_duration_get(mocker):
    mock_render_template = mocker.patch(
        "chellow.views.e.render_template", autospec=True
    )
    ct_now = ct_datetime(2021, 4, 5)
    csv_supplies_duration_get(ct_now)
    last_month_start = to_utc(ct_datetime(2021, 3, 1))
    last_month_finish = to_utc(ct_datetime(2021, 3, 31, 23, 30))
    mock_render_template.assert_called_with(
        "csv_supplies_duration.html",
        last_month_start=last_month_start,
        last_month_finish=last_month_finish,
    )


def test_csv_sites_duration_get(client):
    response = client.get("/e/csv_sites_duration")

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

    mocker.patch("chellow.views.e.chellow.hh_importer")

    response = client.post(f"/e/dc_contracts/{contract.id}/auto_importer")

    match(response, 303)


def test_dc_contract_edit_post(sess, client):
    market_role_C = MarketRole.insert(sess, "C", "DC")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    party = participant.insert_party(
        sess, market_role_C, "DC Ltd.", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_dc(
        sess, "DC 2000", participant, "", {}, utc_datetime(2000, 1, 1), None, {}
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
        "properties": """{
  "enabled": true,
  "protocol": "https",
  "download_days": 8,
  "url_template":
  "http://localhost:8080/hh_api?from={{chunk_start.strftime('%d/%m/%Y')}}&to={{chunk_finish.strftime('%d/%m/%Y')}}",
  "url_values": {
    "22 7907 4116 080": {
      "api_key": "768234ht"
    }
  }
}
""",
    }

    response = client.post(f"/e/dc_contracts/{contract.id}/edit", data=data)

    match(response, 303)


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


def test_dtc_meter_types(client):
    response = client.get("/e/dtc_meter_types")

    match(response, 200)


def test_era_edit_get(client, sess):
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
        utc_datetime(2020, 1, 1),
        gsp_group,
        mop_contract,
        "773",
        dc_contract,
        "ghyy3",
        "hgjeyhuw",
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
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

    patterns = [
        r'<select name="energisation_status_id">\s*'
        r'<option value="2">De-Energised</option>\s*'
        r'<option value="1" selected>Energised</option>\s*'
        r"</select>",
        r'<select name="comm_id">',
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
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    sess.commit()

    file_name = "rates.xlsx"
    f = BytesIO()
    wb = Workbook()
    wb.save(f)
    f.seek(0)

    data = {
        "dno_file": (f, file_name),
        "import": "Import",
        "gsp_group_id": gsp_group.id,
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
        utc_datetime(2020, 1, 1),
        gsp_group,
        mop_contract,
        "773",
        dc_contract,
        "ghyy3",
        "hgjeyhuw",
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
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
        "mtc_code": "845",
        "cop_id": str(cop.id),
        "comm_id": str(comm.id),
        "ssc_code": "",
        "energisation_status_id": str(energisation_status.id),
        "properties": "{}",
        "imp_mpan_core": "22 0470 7514 535",
        "imp_llfc_code": "510",
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
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    ssc = Ssc.insert(sess, "0001", "All", True, utc_datetime(1996, 1), None)
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, valid_from, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, valid_from, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, valid_from, None)
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
        pc,
        "845",
        cop,
        comm,
        ssc,
        energisation_status,
        {},
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
        "mtc_code": "845",
        "cop_id": str(cop.id),
        "comm_id": str(comm.id),
        "ssc_code": ssc.code,
        "energisation_status_id": str(energisation_status.id),
        "properties": "{}",
        "imp_mpan_core": "22 0470 7514 535",
        "imp_llfc_code": "510",
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
        utc_datetime(2020, 1, 1),
        gsp_group,
        mop_contract,
        "773",
        dc_contract,
        "ghyy3",
        "hgjeyhuw",
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
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

    patterns = [
        r'<select name="energisation_status_id">\s*'
        r'<option value="2">De-Energised</option>\s*'
        r'<option value="1" selected>Energised</option>\s*'
        r"</select>",
        r'<select name="comm_id">\s*'
        r'<option value="3">GPRS General Packet Radio Service</option>',
    ]
    match(response, 400, *patterns)


def test_get_era_bundles_bill_after_supply_end(sess, client):
    """Check that a bill starting after the end of a supply still gets
    shown.
    """
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
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
    source = Source.get_by_code(sess, "net")
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

    bundles = get_era_bundles(sess, supply)

    assert len(bundles[0]["imp_bills"]["bill_dicts"]) == 0
    assert len(bundles[1]["imp_bills"]["bill_dicts"]) == 1


def test_laf_imports_post(mocker, app, client):
    file_lines = ("",)

    file_name = "lafs.ptf"
    file_bytes = "\n".join(file_lines).encode("utf8")
    f = BytesIO(file_bytes)

    data = {"import_file": (f, file_name)}

    response = client.post("/e/laf_imports", data=data)

    match(response, 400)


def test_mdd_imports_get(sess, client):
    response = client.get("/e/mdd_imports")
    match(response, 200)


def test_mop_batch_import_bills_full(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
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


def test_mop_batch_upload_file_post(sess, client):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
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


def test_read_add_get(mocker, app):
    bill_id = 1

    class MockDatetime(Datetime):
        def __new__(cls, y, m, d):
            return Datetime.__new__(cls, y, m, d)

    dt = MockDatetime(2019, 1, 1)
    dt.desc = mocker.Mock()

    with app.app_context():
        g = mocker.patch("chellow.views.e.g", autospec=True)
        g.sess = Sess(None, None)

        MockBill = mocker.patch("chellow.views.e.Bill", autospec=True)
        MockBill.supply = mocker.Mock()
        MockBill.start_date = dt

        mock_bill = mocker.Mock()
        MockBill.get_by_id.return_value = mock_bill
        mock_bill.supply.find_era_at.return_value = None
        mock_bill.finish_date = dt

        MockRegisterRead = mocker.patch("chellow.views.e.RegisterRead", autospec=True)
        MockRegisterRead.bill = mocker.Mock()
        MockRegisterRead.present_date = dt

        mocker.patch("chellow.views.e.render_template", autospec=True)

        read_add_get(bill_id)


def test_scenario_edit_post(sess, client):
    props = {
        "scenario_start_year": 2010,
        "scenario_start_month": 5,
        "scenario_duration": 2,
    }
    scenario = Scenario.insert(sess, "scenario 1", props)
    sess.commit()

    data = {
        "name": "scenario_bau",
        "properties": """
{
  "local_rates": [],
  "scenario_start_year": 2015,
  "scenario_start_month": 6,
  "scenario_duration": 1
}""",
    }

    response = client.post(f"/e/scenarios/{scenario.id}/edit", data=data)

    match(response, 303, r"/scenarios/1")


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
    sess.execute("INSERT INTO market_role (code, description) VALUES ('X', 'Supplier')")
    sess.execute("INSERT INTO participant (code, name) VALUES ('FUSE', 'Fusion')")
    sess.execute(
        "INSERT INTO party (market_role_id, participant_id, name, "
        "valid_from, valid_to, dno_code) "
        "VALUES (2, 2, 'Fusion Energy', '2000-01-01', null, null)"
    )
    sess.execute(
        "INSERT INTO contract (name, charge_script, properties, "
        "state, market_role_id, party_id, start_rate_script_id, "
        "finish_rate_script_id) VALUES ('2020 Fusion', '{}', '{}', '{}', "
        "2, 2, null, null)"
    )
    sess.execute(
        "INSERT INTO rate_script (contract_id, start_date, finish_date, "
        "script) VALUES (2, '2000-01-03', null, '{}')"
    )
    sess.execute(
        "UPDATE contract set start_rate_script_id = 2, "
        "finish_rate_script_id = 2 where id = 2;"
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
        "INSERT INTO market_role (code, description) " "VALUES ('X', 'Supplier')"
    )
    sess.execute("INSERT INTO participant (code, name) " "VALUES ('FUSE', 'Fusion')")
    sess.execute(
        "INSERT INTO party (market_role_id, participant_id, name, "
        "valid_from, valid_to, dno_code) "
        "VALUES (2, 2, 'Fusion Energy', '2000-01-01', null, null)"
    )
    sess.execute(
        "INSERT INTO contract (name, charge_script, properties, "
        "state, market_role_id, party_id, start_rate_script_id, "
        "finish_rate_script_id) VALUES ('2020 Fusion', '{}', '{}', '{}', "
        "2, 2, null, null)"
    )
    sess.execute(
        "INSERT INTO rate_script (contract_id, start_date, finish_date, "
        "script) VALUES (2, '2000-01-03', null, '{}')"
    )
    sess.execute(
        "UPDATE contract set start_rate_script_id = 2, "
        "finish_rate_script_id = 2 where id = 2;"
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
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
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
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
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
    source = Source.get_by_code(sess, "net")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
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
        pc,
        "845",
        cop,
        comm,
        None,
        energisation_status,
        {},
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
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
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
    sess.commit()

    query_string = {
        "is_import": "true",
        "year": "2021",
        "years": "1",
    }
    response = client.get(f"/e/supplies/{supply.id}/months", query_string=query_string)
    match(response, 200)


def test_supply_hh_data(sess, client):
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
    source = Source.get_by_code(sess, "net")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
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
    sess.commit()
    query_string = {
        "is_import": "true",
        "finish_year": "2021",
        "finish_month": "1",
        "months": "1",
    }
    response = client.get(f"/e/supplies/{supply.id}/hh_data", query_string=query_string)
    match(response, 200)
