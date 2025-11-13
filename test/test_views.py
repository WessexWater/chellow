from io import BytesIO

from sqlalchemy import select

from utils import match, match_repeat

from chellow.models import (
    Comm,
    Contract,
    Cop,
    DtcMeterType,
    EnergisationStatus,
    GContract,
    GDn,
    GReadingFrequency,
    GUnit,
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
    Report,
    ReportRun,
    Scenario,
    Site,
    Snag,
    Source,
    Ssc,
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_g_reading_frequencies,
    insert_g_units,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_home(client, sess, mocker):
    vf = to_utc(ct_datetime(2000, 1, 1))

    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "Fusion DC", vf, None, None)
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, vf, None, {}
    )
    sess.commit()

    patched_hh_importer = mocker.patch("chellow.chellow.e.hh_importer")

    class AnObj:
        pass

    tsk = AnObj()
    tsk.is_error = True
    tsk.contract_id = dc_contract.id
    patched_hh_importer.tasks = {"a": tsk}

    response = client.get("/")

    match(response, 200, f"/e/dc_contracts/{dc_contract.id}/auto_importer")


def test_input_date(client, sess, mocker):
    query_string = {
        "prefix": "timestamp",
        "resolution": "day",
        "timestamp_year": "2022",
        "timestamp_month": "11",
        "timestamp_day": "31",
    }
    response = client.get("/input_date", query_string=query_string)

    match(response, 200)


def test_local_report_home(client, sess):
    script = """from flask import render_template_string

def do_get():
    return render_template_string(template)
"""

    template = """{% extends "base.html"%}

{% block content %}
  <p>Marcus Aurelius</p>
{% endblock %}
"""

    report = Report.insert(sess, "Emperor", script, template)
    config = sess.execute(
        select(Contract).where(Contract.name == "configuration")
    ).scalar_one()
    props = config.make_properties()
    props["local_reports_id"] = report.id
    config.properties = props
    sess.commit()

    response = client.get("/local_reports_home")

    match(response, 200)


def test_local_report_post_delete(client, sess):
    report = Report.insert(sess, "Gray", "", "")
    sess.commit()

    data = {
        "delete": "Delete",
    }
    response = client.post(f"/local_reports/{report.id}", data=data)

    match(response, 303)


def test_local_reports_post(client, sess):
    data = {
        "name": "Minority Report",
        "add": "Add",
    }
    response = client.post("/local_reports", data=data)

    match(response, 303)

    report = sess.execute(select(Report)).scalar_one()
    assert report.template == ""


def test_scenario_get(sess, client):
    props = {
        "scenario_start_year": 2010,
        "scenario_start_month": 5,
    }
    scenario = Scenario.insert(sess, "scenario 1", props)
    sess.commit()

    response = client.get(f"/scenarios/{scenario.id}")

    match(response, 200)


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

    response = client.post(f"/scenarios/{scenario.id}/edit", data=data)

    match(response, 303, r"/scenarios/1")


def test_site_get(client, sess):
    valid_from = to_utc(ct_datetime(2000, 1, 1))
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
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "grid")
    insert_energisation_statuses(sess)
    energisation_status = EnergisationStatus.get_by_code(sess, "E")
    gsp_group = GspGroup.insert(sess, "_L", "South Western")
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2020, 1, 1),
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

    response = client.get(f"/sites/{site.id}")

    patterns = []
    match(response, 200, *patterns)


def test_site_get_dumb(client, sess):
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
    pc = Pc.insert(sess, "02", "nhh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    ssc = Ssc.insert(sess, "0001", "All", True, utc_datetime(1996, 1), None)
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
        valid_from,
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
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, valid_from, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, valid_from, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, valid_from, None)
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2020, 1, 1),
        gsp_group,
        mop_contract,
        dc_contract,
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
    sess.commit()

    response = client.get(f"/sites/{site.id}")

    patterns = []
    match(response, 200, *patterns)


def test_supplies_get_e(sess, client):
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
        valid_from,
        None,
        bank_holiday_rate_script,
    )
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", valid_from, None, None
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
    pc = Pc.insert(sess, "02", "nhh", utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    ssc = Ssc.insert(sess, "0001", "All", True, utc_datetime(1996, 1), None)
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
        valid_from,
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
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    mtc_ssc = MtcSsc.insert(sess, mtc_participant, ssc, valid_from, None)
    mtc_llfc_ssc = MtcLlfcSsc.insert(sess, mtc_ssc, llfc, valid_from, None)
    MtcLlfcSscPc.insert(sess, mtc_llfc_ssc, pc, valid_from, None)
    insert_dtc_meter_types(sess)
    dtc_meter_type = DtcMeterType.get_by_code(sess, "H")
    site.insert_e_supply(
        sess,
        source,
        None,
        "Bob",
        utc_datetime(2000, 1, 1),
        utc_datetime(2020, 1, 1),
        gsp_group,
        mop_contract,
        dc_contract,
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
    site.insert_e_supply(
        sess,
        source,
        None,
        "Alice",
        utc_datetime(2000, 1, 1),
        utc_datetime(2020, 1, 1),
        gsp_group,
        mop_contract,
        dc_contract,
        "hgjeyhuw",
        dno,
        pc,
        "845",
        cop,
        comm,
        ssc.code,
        energisation_status,
        dtc_meter_type,
        "22 0471 7514 532",
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
        "search_pattern": "",
    }
    response = client.get("/supplies", query_string=query_string)

    match(response, 200)


def test_supplies_get_g(sess, client):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")

    g_dn = GDn.insert(sess, "EE", "East of England")

    g_ldz = g_dn.insert_g_ldz(sess, "EA")

    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")

    insert_g_units(sess)

    g_unit_M3 = GUnit.get_by_code(sess, "M3")

    g_contract = GContract.insert(sess, False, "Fusion 2020", "", {}, vf, None, {})

    insert_g_reading_frequencies(sess)

    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")

    mprn = "87614362"
    g_supply = site.insert_g_supply(
        sess,
        mprn,
        "main",
        g_exit_zone,
        utc_datetime(2018, 1, 1),
        None,
        "hgeu8rhg",
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    sess.commit()
    query_string = {
        "search_pattern": mprn,
    }
    response = client.get("/supplies", query_string=query_string)

    match(response, 307, rf"/g/supplies/{g_supply.id}")


def test_system(client):
    response = client.get("/system")

    match(response, 200)


def test_general_import_post_full(sess, client):
    """General import of channel snag unignore and check the import that's
    been created.
    """
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
    snag = sess.query(Snag).order_by(Snag.start_date).first()
    snag.set_is_ignored(True)
    sess.commit()

    file_items = [
        "insert",
        "channel_snag_unignore",
        "22 0470 7514 535",
        "FALSE",
        "Active",
        "Missing",
        "2003-08-03 00:00",
        "2004-07-06 23:30",
    ]
    file_name = "gi_channel_snag_ignore.csv"
    file_bytes = ",".join(file_items).encode("utf8")
    f = BytesIO(file_bytes)

    data = {"import_file": (f, file_name)}

    response = client.post("/general_imports", data=data)

    match(response, 303, "/general_imports/0")

    match_repeat(
        client, "/general_imports/0", r"The file has been imported successfully"
    )
    sess.rollback()

    assert not snag.is_ignored


def test_non_core_auto_importer_get(sess, client):
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_non_core(
        sess, "bank_holidays", "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    sess.commit()

    response = client.get(f"/non_core_contracts/{contract.id}/auto_importer")

    match(response, 200)


def test_non_core_auto_importer_get_bmarketidx(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    contract = Contract.insert_non_core(sess, "bmarketidx", "", {}, vf, None, {})
    sess.commit()

    response = client.get(f"/non_core_contracts/{contract.id}/auto_importer")

    match(response, 200)


def test_non_core_auto_importer_post(mocker, sess, client):
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_non_core(
        sess, "bank_holidays", "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    sess.commit()

    mocker.patch("chellow.views.import_module")

    response = client.post(f"/non_core_contracts/{contract.id}/auto_importer")

    match(response, 303)


def test_non_core_contract_edit_post(sess, client):
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_non_core(
        sess, "g_cv", "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    sess.commit()

    data = {
        "name": "g_cv",
        "properties": """{
"enabled": true,
"url": "http://localhost:8080/nationalgrid/cv.csv"}
""",
    }

    response = client.post(f"/non_core_contracts/{contract.id}/edit", data=data)

    match(response, 303)


def test_non_core_rate_script_edit_get(sess, client):
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_non_core(
        sess, "rcrc", "import nonexistent", {}, utc_datetime(2000, 1, 1), None, {}
    )
    rs = contract.start_rate_script
    sess.commit()

    response = client.get(f"/non_core_rate_scripts/{rs.id}/edit")

    match(response, 200)


def test_non_core_rate_script_edit_get_bst(sess, client):
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
    contract = Contract.insert_non_core(
        sess, "rcrc", "", {}, to_utc(ct_datetime(2000, 5, 31, 23, 30)), None, {}
    )
    rs = contract.start_rate_script
    sess.commit()

    response = client.get(f"/non_core_rate_scripts/{rs.id}/edit")

    match(response, 200, r'<input type="hidden" name="start_hour" value="23">')


def test_site_edit_get(sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    GContract.insert_industry(sess, "cv", "", {}, vf, None, {})
    sess.commit()

    response = client.get(f"/sites/{site.id}/edit")
    patterns = [
        r'<select name="g_contract_id">\s*</select>',
    ]
    match(response, 200, *patterns)


def test_rate_server_get(sess, client):
    response = client.get("/rate_server")
    match(response, 200)


def test_report_run_get_bill_check(sess, client):
    report_run = ReportRun.insert(sess, "bill_check", None, "_b_88", {})
    sess.commit()
    query_string = {"element": "net"}
    response = client.get(f"/report_runs/{report_run.id}", query_string=query_string)
    match(response, 200)


def test_report_run_spreadsheet_get(sess, client):
    report_run = ReportRun.insert(sess, "bill_check", None, "_b_88", {})
    report_run.insert_row(sess, "", ["clump"], {}, {})
    sess.commit()

    response = client.get(f"/report_runs/{report_run.id}/spreadsheet")
    match(response, 200)


def test_report_run_row_get_bill_check(sess, client):
    report_run = ReportRun.insert(sess, "bill_check", None, "_b_88", {})
    report_run_row = report_run.insert_row(
        sess,
        "",
        ["clump"],
        {},
        {},
        data={
            "actual_net_gbp": 10,
            "virtual_net_gbp": 20.32,
            "difference_net_gbp": 23.6,
            "elements": {},
        },
    )
    sess.commit()

    response = client.get(f"/report_run_rows/{report_run_row.id}")
    match(response, 200)
