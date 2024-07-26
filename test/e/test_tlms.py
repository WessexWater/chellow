from decimal import Decimal

from chellow.e.computer import SupplySource
from chellow.e.tlms import elexon_import, hh
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
    VoltageLevel,
    insert_comms,
    insert_cops,
    insert_dtc_meter_types,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_hh(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")
    participant = Participant.insert(sess, "CALB", "Calb")
    market_role = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role, "None core", vf, None, None)
    ss_start = to_utc(ct_datetime(2020, 1, 1))
    tlm_II = Decimal("2.5")
    tlm_SF = Decimal("1.5")
    Contract.insert_non_core(
        sess,
        "tlms",
        "",
        {},
        to_utc(ct_datetime(2000, 4, 1)),
        None,
        {
            "tlms": {
                "01 00:00": {
                    "_L": {"SF": {"off_taking": tlm_SF}, "II": {"off_taking": tlm_II}}
                }
            }
        },
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
    Contract.insert_dno(
        sess,
        dno.dno_code,
        participant,
        "",
        {},
        vf,
        None,
        {},
    )
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
    caches = {}
    ss = SupplySource(
        sess,
        ss_start,
        ss_start,
        to_utc(ct_datetime(2021, 1, 1)),
        supply.eras[0],
        True,
        caches,
    )
    hh_datum = ss.hh_data[0]
    hh_datum["gsp-kwh"] = 1
    hh(ss)
    assert hh_datum["tlm"] == 1.5


def test_elexon_import(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    participant = Participant.insert(sess, "CALB", "Calb")
    market_role = MarketRole.insert(sess, "Z", "Non-core")
    participant.insert_party(sess, market_role, "None core", vf, None, None)
    Contract.insert_non_core(
        sess, "tlms", "", {"enabled": True, "url": "https://example.com"}, vf, None, {}
    )
    Contract.insert_non_core(
        sess,
        "configuration",
        "",
        {"elexonportal_scripting_key": "xxk"},
        vf,
        None,
        {},
    )
    sess.commit()

    def log(msg):
        pass

    def set_progress(msg):
        pass

    s = mocker.Mock()
    mock_response = mocker.Mock()
    lines = [b"", b""]
    mock_response.iter_lines = mocker.Mock(return_value=lines)
    s.get = mocker.Mock(return_value=mock_response)
    scripting_key = mocker.Mock()

    elexon_import(sess, log, set_progress, s, scripting_key)
