from decimal import Decimal
from io import StringIO

from chellow.e.hh_importer import (
    HhDataImportProcess,
    https_handler,
    solaredge_energy_details_parser,
)
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


def test_https_handler(mocker, sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", valid_from, None, None)
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    market_role_M = MarketRole.insert(sess, "M", "Mop")
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    participant.insert_party(
        sess, market_role_M, "Fusion Mop Ltd", valid_from, None, None
    )
    participant.insert_party(sess, market_role_X, "Fusion Ltc", valid_from, None, None)
    participant.insert_party(sess, market_role_C, "Fusion DC", valid_from, None, None)
    mop_contract = Contract.insert_mop(
        sess, "Fusion", participant, "", {}, valid_from, None, {}
    )
    dc_contract = Contract.insert_dc(
        sess, "Fusion DC 2000", participant, "", {}, valid_from, None, {}
    )
    pc = Pc.insert(sess, "00", "hh", valid_from, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    imp_supplier_contract = Contract.insert_supplier(
        sess, "Fusion Supplier 2000", participant, "", {}, valid_from, None, {}
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
        valid_from,
        None,
    )
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, "HV")
    llfc = dno.insert_llfc(
        sess, "510", "PC 5-8 & HH HV", voltage_level, False, True, valid_from, None
    )
    MtcLlfc.insert(sess, mtc_participant, llfc, valid_from, None)
    insert_sources(sess)
    source = Source.get_by_code(sess, "net")
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
    era = supply.eras[0]
    era.insert_channel(sess, True, "ACTIVE")

    sess.commit()

    mock_requests = mocker.patch("chellow.e.hh_importer.requests")
    mock_s = mocker.Mock()
    mock_requests.Session.return_value = mock_s
    mock_response = mocker.Mock()
    mock_s.get.return_value = mock_response
    mock_response.json.return_value = {
        "Data": [{"Flags": 0, "Time": 636188256000000000, "Value": 21}]
    }

    log = []

    def log_f(msg):
        log.append(msg)

    properties = {
        "enabled": True,
        "protocol": "https",
        "download_days": 8,
        "parser": "meniscus",
        "url_template": "https://example.com/?from="
        "{{chunk_start.strftime('%d/%m/%Y')}}&to="
        "{{chunk_finish.strftime('%d/%m/%Y')}}",
        "url_values": {"22 7907 4116 080": {"api_key": "768234ht"}},
    }

    now = utc_datetime(2020, 12, 22)

    https_handler(sess, log_f, properties, dc_contract, now=now)
    expected_log = [
        "Window start: 2020-12-14 00:00",
        "Window finish: 2020-12-21 23:30",
        "Looking at MPAN core 22 7867 6232 781.",
        "Retrieving data from https://example.com/?from=14/12/2020&to=21/12/2020.",
        "Finished loading.",
    ]
    assert log == expected_log
    mock_s.get.assert_called_once()


def test_HhDataImportProcess(sess):
    valid_from = to_utc(ct_datetime(1996, 1, 1))

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AB Industries")
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
    market_role_C = MarketRole.insert(sess, "C", "HH Dc")
    participant.insert_party(sess, market_role_C, "FDC Ltd.", valid_from, None, None)
    dc_contract = Contract.insert_dc(
        sess,
        "Fusion DC 2000",
        participant,
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    sess.commit()

    process_id = 0
    content = "#F2"
    istream = StringIO(content)
    file_name = "afile.df2"
    file_size = len(content)
    importer = HhDataImportProcess(
        dc_contract.id, process_id, istream, file_name, file_size
    )
    importer.run()

    assert importer.messages == []


def test_solaredge_energy_details_parser():
    def log_f():
        pass

    mpan_core = "22 4781 4783 280"
    res = {
        "energyDetails": {
            "meters": [
                {
                    "type": "Production",
                    "values": [{"date": "2023-10-01 00:00:00", "value": "3772"}],
                }
            ]
        }
    }
    properties = {"generated_mpan_cores": [mpan_core]}
    actual = solaredge_energy_details_parser(log_f, res, properties, mpan_core)
    expected = [
        {
            "mpan_core": "22 4781 4783 280",
            "start_date": utc_datetime(2023, 9, 30, 23, 0),
            "channel_type": "ACTIVE",
            "value": Decimal("3.772"),
            "status": "A",
        }
    ]
    print(actual)
    assert actual == expected
