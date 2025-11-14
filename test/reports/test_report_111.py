import csv
from decimal import Decimal
from io import StringIO

from utils import match

from chellow.e.computer import contract_func
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
    ReportRun,
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
    insert_sources,
    insert_voltage_levels,
)
from chellow.reports.report_111 import (
    _process_period,
    _process_supply,
    content,
    find_gaps,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_find_gaps():
    gaps = {
        to_utc(ct_datetime(2025, 1, 1)): "start",
        to_utc(ct_datetime(2025, 1, 1, 0, 30)): "start_finish",
        to_utc(ct_datetime(2025, 1, 1, 1, 0)): "finish",
    }
    assert list(find_gaps(gaps)) == [
        (
            to_utc(ct_datetime(2025, 1, 1, 0, 0)),
            to_utc(ct_datetime(2025, 1, 1, 0, 0)),
        ),
        (
            to_utc(ct_datetime(2025, 1, 1, 0, 30)),
            to_utc(ct_datetime(2025, 1, 1, 0, 30)),
        ),
    ]


# End to end tests


def test_ete_error_message_for_invalid_bill_id(client, sess):
    query_string = {
        "bill_id": "0",
    }
    response = client.get("/reports/111", query_string=query_string)

    match(response, 404)


# HTTP level tests


def test_http_supplier_batch_with_mpan_cores(mocker, client, sess):
    market_role_X = MarketRole.insert(sess, "X", "Supplier")
    participant = Participant.insert(sess, "hhak", "AK Industries")
    participant.insert_party(
        sess, market_role_X, "Fusion Ltc", utc_datetime(2000, 1, 1), None, None
    )
    supplier_contract = Contract.insert_supplier(
        sess,
        "Fusion Supplier 2000",
        participant,
        "",
        {},
        utc_datetime(2000, 1, 1),
        None,
        {},
    )
    batch = supplier_contract.insert_batch(sess, "005", "batch 5")
    sess.commit()
    user = User.get_by_email_address(sess, "admin@example.com")
    MockThread = mocker.patch("chellow.reports.report_111.threading.Thread")

    query_string = {
        "batch_id": str(batch.id),
        "mpan_cores": "22 1065 3921 534",
    }
    response = client.get("/reports/111", query_string=query_string)

    match(response, 303)

    expected_args = (
        batch.id,
        None,
        None,
        None,
        None,
        user.id,
        ["22 1065 3921 534"],
        "_batch_005",
        1,
    )

    MockThread.assert_called_with(target=content, args=expected_args)


# Worker level tests


def test_process_period(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
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
    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill(ds):
    rate = 0.1
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]
        bill_hh['nrg-kwh'] = hh['msp-kwh']
        bill_hh['nrg-rate'] = {rate}
        bill_hh['off-rate'] = {0.1}
        bill_hh['nrg-gbp'] = hh['msp-kwh'] * rate + 1
        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat-gbp'] = 0
        bill_hh['gross-gbp'] = bill_hh['net-gbp'] + bill_hh['vat-gbp']
        bill_hh['problem'] = 'hello '

    ds.supplier_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    supplier_contract = Contract.insert_supplier(
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
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
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
        supplier_contract,
        "7748",
        361,
        None,
        None,
        None,
        None,
        None,
    )
    batch = supplier_contract.insert_batch(sess, "a b", "")
    insert_bill_types(sess)
    bill_type = BillType.get_by_code(sess, "N")
    bill = batch.insert_bill(
        sess,
        "dd",
        "hjk",
        to_utc(ct_datetime(2009, 7, 10)),
        to_utc(ct_datetime(2009, 7, 10)),
        to_utc(ct_datetime(2009, 7, 10)),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        bill_type,
        {"vat": {Decimal("20"): {"net": Decimal("10.00"), "vat": Decimal("10.00")}}},
        supply,
    )
    bill.insert_element(
        sess,
        "nrg",
        to_utc(ct_datetime(2009, 7, 10)),
        to_utc(ct_datetime(2009, 7, 10)),
        Decimal("10.00"),
        {"rate": {Decimal("0.1")}},
    )
    sess.commit()

    report_context = {}
    bill_ids = {bill.id: bill}
    forecast_date = utc_datetime(2020, 7, 10)
    vbf = contract_func(report_context, supplier_contract, "virtual_bill")
    period_start = to_utc(ct_datetime(2009, 7, 10, 0, 0))
    period_finish = to_utc(ct_datetime(2009, 7, 10, 0, 0))

    data = _process_period(
        sess,
        report_context,
        supply,
        supplier_contract,
        bill_ids,
        forecast_date,
        vbf,
        period_start,
        period_finish,
    )
    expected = {
        "actual_bills": [
            {
                "batch_id": 1,
                "batch_reference": "a b",
                "breakdown": "{\n"
                '  "vat": {\n'
                "    20: {\n"
                '      "net": 10.00,\n'
                '      "vat": 10.00,\n'
                "    },\n"
                "  },\n"
                "}",
                "gross": Decimal("10.00"),
                "id": 1,
                "kwh": Decimal("10.00"),
                "net": Decimal("10.00"),
                "problem": "The Gross GBP (10.00) of the bill isn't equal "
                "to the Net GBP "
                "(10.00) + VAT GBP (10.00) of the bill.",
                "start_date": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
                "finish_date": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
                "vat": Decimal("10.00"),
            },
        ],
        "actual_net_gbp": 10.0,
        "difference_net_gbp": 9.0,
        "contract_id": 4,
        "contract_name": "Fusion Supplier 2000",
        "market_role_code": "X",
        "elements": {
            "nrg": {
                "parts": {
                    "gbp": {
                        "actual": Decimal("10.00"),
                        "difference": 9.0,
                        "virtual": 1.0,
                        "passed": "❌",
                    },
                    "kwh": {
                        "difference": None,
                        "virtual": 0,
                        "passed": "❔",
                    },
                    "rate": {
                        "actual": {
                            Decimal("0.1"),
                        },
                        "difference": 0.0,
                        "virtual": {
                            0.1,
                        },
                        "passed": "✅",
                    },
                },
                "actual_elements": [
                    {
                        "bill": {
                            "batch": {
                                "id": 1,
                                "reference": "a b",
                            },
                            "id": 1,
                        },
                        "breakdown": "{\n" '  "rate": [\n' "    0.1,\n" "  ],\n" "}",
                        "finish_date": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
                        "id": 1,
                        "net": Decimal("10.00"),
                        "start_date": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
                    },
                ],
            },
        },
        "exp_mpan_core": None,
        "imp_mpan_core": "22 7867 6232 781",
        "period_start": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
        "period_finish": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
        "site_id": 1,
        "site_code": "CI017",
        "site_name": "Water Works",
        "supply_id": 1,
        "virtual_net_gbp": 1.0,
        "problem": "Bills have problems. hello ",
    }

    assert data == expected


def test_process_period_no_era(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
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
    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill(ds):
    rate = 0.1
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]
        bill_hh['nrg-kwh'] = hh['msp-kwh']
        bill_hh['nrg-rate'] = {rate}
        bill_hh['off-rate'] = {0.1}
        bill_hh['nrg-gbp'] = hh['msp-kwh'] * rate + 1
        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat-gbp'] = 0
        bill_hh['gross-gbp'] = bill_hh['net-gbp'] + bill_hh['vat-gbp']
        bill_hh['problem'] = 'hello '

    ds.supplier_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    supplier_contract = Contract.insert_supplier(
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
        to_utc(ct_datetime(2001, 1, 1)),
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
        supplier_contract,
        "7748",
        361,
        None,
        None,
        None,
        None,
        None,
    )
    batch = supplier_contract.insert_batch(sess, "a b", "")
    insert_bill_types(sess)
    bill_type = BillType.get_by_code(sess, "N")
    bill = batch.insert_bill(
        sess,
        "dd",
        "hjk",
        to_utc(ct_datetime(2009, 7, 10)),
        to_utc(ct_datetime(2009, 7, 10)),
        to_utc(ct_datetime(2009, 7, 10)),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        bill_type,
        {"vat": {Decimal("20"): {"net": Decimal("10.00"), "vat": Decimal("10.00")}}},
        supply,
    )
    bill.insert_element(
        sess,
        "nrg",
        to_utc(ct_datetime(2009, 7, 10)),
        to_utc(ct_datetime(2009, 7, 10)),
        Decimal("10.00"),
        {"rate": {Decimal("0.1")}},
    )
    sess.commit()

    report_context = {}
    bill_ids = {bill.id: bill}
    forecast_date = utc_datetime(2020, 7, 10)
    vbf = contract_func(report_context, supplier_contract, "virtual_bill")
    period_start = to_utc(ct_datetime(2009, 7, 10, 0, 0))
    period_finish = to_utc(ct_datetime(2009, 7, 10, 0, 0))

    data = _process_period(
        sess,
        report_context,
        supply,
        supplier_contract,
        bill_ids,
        forecast_date,
        vbf,
        period_start,
        period_finish,
    )
    expected = {
        "actual_bills": [
            {
                "batch_id": 1,
                "batch_reference": "a b",
                "breakdown": "{\n"
                '  "vat": {\n'
                "    20: {\n"
                '      "net": 10.00,\n'
                '      "vat": 10.00,\n'
                "    },\n"
                "  },\n"
                "}",
                "gross": Decimal("10.00"),
                "id": 1,
                "kwh": Decimal("10.00"),
                "net": Decimal("10.00"),
                "problem": "The Gross GBP (10.00) of the bill isn't equal "
                "to the Net GBP (10.00) + VAT GBP (10.00) of the bill.",
                "start_date": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
                "finish_date": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
                "vat": Decimal("10.00"),
            },
        ],
        "actual_net_gbp": 10.0,
        "difference_net_gbp": 10.0,
        "contract_id": 4,
        "contract_name": "Fusion Supplier 2000",
        "market_role_code": "X",
        "elements": {
            "nrg": {
                "parts": {
                    "gbp": {
                        "actual": Decimal("10.00"),
                        "difference": 10.0,
                        "passed": "❌",
                    },
                    "rate": {
                        "actual": {
                            Decimal("0.1"),
                        },
                        "difference": None,
                        "passed": "❔",
                    },
                },
                "actual_elements": [
                    {
                        "bill": {
                            "batch": {
                                "id": 1,
                                "reference": "a b",
                            },
                            "id": 1,
                        },
                        "breakdown": "{\n" '  "rate": [\n' "    0.1,\n" "  ],\n" "}",
                        "finish_date": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
                        "id": 1,
                        "net": Decimal("10.00"),
                        "start_date": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
                    },
                ],
            },
        },
        "exp_mpan_core": None,
        "imp_mpan_core": "22 7867 6232 781",
        "period_start": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
        "period_finish": to_utc(ct_datetime(2009, 7, 10, 0, 0)),
        "site_id": 1,
        "site_code": "CI017",
        "site_name": "Water Works",
        "supply_id": 1,
        "virtual_net_gbp": 0,
        "problem": "Bills have problems. No eras for this period of the supply. ",
    }

    assert data == expected


def test_process_supply(sess):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
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
    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill(ds):
    rate = 0.1
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]
        bill_hh['nrg-kwh'] = hh['msp-kwh']
        bill_hh['nrg-rate'] = {rate}
        bill_hh['off-rate'] = {0.1}
        bill_hh['nrg-gbp'] = hh['msp-kwh'] * rate + 1
        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat-gbp'] = 0
        bill_hh['gross-gbp'] = bill_hh['net-gbp'] + bill_hh['vat-gbp']
        bill_hh['problem'] = 'hello '

    ds.supplier_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    supplier_contract = Contract.insert_supplier(
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
    meter_type = MeterType.insert(sess, "C5", "COP 1-5", utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, "CR", "Credit", utc_datetime(1996, 1, 1), None
    )
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
        supplier_contract,
        "7748",
        361,
        None,
        None,
        None,
        None,
        None,
    )
    batch = supplier_contract.insert_batch(sess, "a b", "")
    insert_bill_types(sess)
    bill_type = BillType.get_by_code(sess, "N")
    bill = batch.insert_bill(
        sess,
        "dd",
        "hjk",
        utc_datetime(2009, 7, 10),
        utc_datetime(2009, 7, 10),
        utc_datetime(2009, 7, 10),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        bill_type,
        {},
        supply,
    )
    bill.insert_element(
        sess,
        "nrg",
        utc_datetime(2009, 7, 10),
        utc_datetime(2009, 7, 10),
        Decimal("10.00"),
        {"rate": {Decimal("0.1")}},
    )
    sess.commit()

    report_context = {}
    supply_id = supply.id
    bill_ids = {bill.id}
    forecast_date = utc_datetime(2020, 7, 10)
    vbf = contract_func(report_context, supplier_contract, "virtual_bill")

    vals = list(
        _process_supply(
            sess,
            report_context,
            supply_id,
            bill_ids,
            forecast_date,
            supplier_contract,
            vbf,
        )
    )
    expected = [
        {
            "actual_bills": [
                {
                    "batch_id": 1,
                    "batch_reference": "a b",
                    "breakdown": "{}",
                    "gross": Decimal("10.00"),
                    "id": 1,
                    "kwh": Decimal("10.00"),
                    "net": Decimal("10.00"),
                    "problem": "The Gross GBP (10.00) of the bill isn't equal "
                    "to the Net GBP "
                    "(10.00) + VAT GBP (10.00) of the bill.The total 'net' 0.00 in "
                    "the VAT breakdown doesn't match the 'net' 10.00 of the "
                    "bill.The total VAT 0.00 in the VAT breakdown doesn't match the "
                    "VAT 10.00 of the bill.",
                    "vat": Decimal("10.00"),
                    "start_date": utc_datetime(2009, 7, 10, 0, 0),
                    "finish_date": utc_datetime(2009, 7, 10, 0, 0),
                },
            ],
            "actual_net_gbp": 10.0,
            "difference_net_gbp": 9.0,
            "contract_id": 4,
            "contract_name": "Fusion Supplier 2000",
            "market_role_code": "X",
            "elements": {
                "nrg": {
                    "parts": {
                        "gbp": {
                            "actual": Decimal("10.00"),
                            "difference": 9.0,
                            "virtual": 1.0,
                            "passed": "❌",
                        },
                        "kwh": {
                            "difference": None,
                            "virtual": 0,
                            "passed": "❔",
                        },
                        "rate": {
                            "actual": {
                                Decimal("0.1"),
                            },
                            "difference": 0.0,
                            "virtual": {
                                0.1,
                            },
                            "passed": "✅",
                        },
                    },
                    "actual_elements": [
                        {
                            "bill": {
                                "batch": {
                                    "id": 1,
                                    "reference": "a b",
                                },
                                "id": 1,
                            },
                            "breakdown": "{\n"
                            '  "rate": [\n'
                            "    0.1,\n"
                            "  ],\n"
                            "}",
                            "finish_date": utc_datetime(2009, 7, 10, 0, 0),
                            "id": 1,
                            "net": Decimal("10.00"),
                            "start_date": utc_datetime(2009, 7, 10, 0, 0),
                        },
                    ],
                },
            },
            "exp_mpan_core": None,
            "imp_mpan_core": "22 7867 6232 781",
            "period_start": utc_datetime(2009, 7, 10, 0, 0),
            "period_finish": utc_datetime(2009, 7, 10, 0, 0),
            "site_id": 1,
            "site_code": "CI017",
            "site_name": "Water Works",
            "supply_id": 1,
            "virtual_net_gbp": 1.0,
            "problem": "Bills have problems. hello ",
        },
    ]

    assert vals == expected


def test_content(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
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
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill(ds):
    rate = 0.1
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]
        bill_hh['sum-msp-kwh'] = hh['msp-kwh']
        bill_hh['rate'] = {rate}
        bill_hh['off-rate'] = {0.1}
        bill_hh['sum-msp-gbp'] = hh['msp-kwh'] * rate
        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat-gbp'] = 0
        bill_hh['gross-gbp'] = bill_hh['net-gbp'] + bill_hh['vat-gbp']

    ds.supplier_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    supplier_contract = Contract.insert_supplier(
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
        supplier_contract,
        "7748",
        361,
        None,
        None,
        None,
        None,
        None,
    )
    batch = supplier_contract.insert_batch(sess, "a b", "")
    insert_bill_types(sess)
    bill_type = BillType.get_by_code(sess, "N")
    bill = batch.insert_bill(
        sess,
        "dd",
        "hjk",
        utc_datetime(2009, 7, 10),
        utc_datetime(2009, 7, 10),
        utc_datetime(2009, 7, 10),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        bill_type,
        {"rate": [Decimal("0.1")]},
        supply,
    )
    user_role = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "admin", user_role, None)
    user_id = user.id
    report_run = ReportRun.insert(sess, "", user, "", {})
    report_run_id = report_run.id
    batch_id = batch.id
    bill_id = bill.id
    supplier_contract_id = supplier_contract.id
    sess.commit()

    virtual_bill_titles = [
        "ccl-kwh",
        "ccl-rate",
        "ccl-gbp",
        "net-gbp",
        "vat-gbp",
        "gross-gbp",
        "sum-msp-kwh",
        "rate",
        "sum-msp-gbp",
        "problem",
    ]
    titles = [
        "batch",
        "bill-reference",
        "bill-type",
        "bill-kwh",
        "bill-net-gbp",
        "bill-vat-gbp",
        "bill-start-date",
        "bill-finish-date",
        "imp-mpan-core",
        "exp-mpan-core",
        "site-code",
        "site-name",
        "covered-from",
        "covered-to",
        "covered-bills",
        "metered-kwh",
    ]
    for t in virtual_bill_titles:
        titles.append("covered-" + t)
        titles.append("virtual-" + t)
        if t.endswith("-gbp"):
            titles.append("difference-" + t)

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_111.open_file", return_value=mock_file)

    content(
        batch_id,
        bill_id,
        supplier_contract_id,
        vf,
        vf,
        user_id,
        [],
        "",
        report_run_id,
    )


def test_content_with_mpans(sess, mocker):
    vf = to_utc(ct_datetime(1996, 1, 1))
    site = Site.insert(sess, "CI017", "Water Works")

    market_role_Z = MarketRole.insert(sess, "Z", "Non-core")
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
    pc = Pc.insert(sess, "00", "hh", vf, None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, "5")
    insert_comms(sess)
    comm = Comm.get_by_code(sess, "GSM")
    supplier_charge_script = """
import chellow.e.ccl
from chellow.utils import HH, reduce_bill_hhs, utc_datetime

def virtual_bill_titles():
    return []

def virtual_bill(ds):
    rate = 0.1
    for hh in ds.hh_data:
        hh_start = hh['start-date']
        bill_hh = ds.supplier_bill_hhs[hh_start]
        bill_hh['sum-msp-kwh'] = hh['msp-kwh']
        bill_hh['rate'] = {rate}
        bill_hh['off-rate'] = {0.1}
        bill_hh['sum-msp-gbp'] = hh['msp-kwh'] * rate
        bill_hh['net-gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat-gbp'] = 0
        bill_hh['gross-gbp'] = bill_hh['net-gbp'] + bill_hh['vat-gbp']

    ds.supplier_bill = reduce_bill_hhs(ds.supplier_bill_hhs)
"""
    supplier_contract = Contract.insert_supplier(
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
        supplier_contract,
        "7748",
        361,
        None,
        None,
        None,
        None,
        None,
    )
    batch = supplier_contract.insert_batch(sess, "a b", "")
    insert_bill_types(sess)
    bill_type = BillType.get_by_code(sess, "N")
    bill = batch.insert_bill(
        sess,
        "dd",
        "hjk",
        utc_datetime(2009, 7, 10),
        utc_datetime(2009, 7, 10),
        utc_datetime(2009, 7, 10),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        Decimal("10.00"),
        bill_type,
        {"rate": [Decimal("0.1")]},
        supply,
    )
    user_role = UserRole.insert(sess, "editor")
    user = User.insert(sess, "admin@example.com", "admin", user_role, None)
    user_id = user.id
    report_run = ReportRun.insert(sess, "", user, "", {})
    report_run_id = report_run.id
    batch_id = batch.id
    bill_id = bill.id
    supplier_contract_id = supplier_contract.id
    sess.commit()

    virtual_bill_titles = [
        "ccl-kwh",
        "ccl-rate",
        "ccl-gbp",
        "net-gbp",
        "vat-gbp",
        "gross-gbp",
        "sum-msp-kwh",
        "rate",
        "sum-msp-gbp",
        "problem",
    ]
    titles = [
        "batch",
        "bill-reference",
        "bill-type",
        "bill-kwh",
        "bill-net-gbp",
        "bill-vat-gbp",
        "bill-start-date",
        "bill-finish-date",
        "imp-mpan-core",
        "exp-mpan-core",
        "site-code",
        "site-name",
        "covered-from",
        "covered-to",
        "covered-bills",
        "metered-kwh",
    ]
    for t in virtual_bill_titles:
        titles.append("covered-" + t)
        titles.append("virtual-" + t)
        if t.endswith("-gbp"):
            titles.append("difference-" + t)

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_111.open_file", return_value=mock_file)

    content(
        batch_id,
        bill_id,
        supplier_contract_id,
        vf,
        vf,
        user_id,
        [
            "22 7867 6232 781",
        ],
        "",
        report_run_id,
    )
    mock_file.seek(0)
    actual_rows = [row for row in csv.reader(mock_file)]
    assert actual_rows == [
        [
            "imp_mpan_core",
            "exp_mpan_core",
            "site_code",
            "site_name",
            "period_start",
            "period_finish",
            "actual_net_gbp",
            "virtual_net_gbp",
            "difference_net_gbp",
        ],
        [
            "22 7867 6232 781",
            "",
            "CI017",
            "Water Works",
            "2009-07-10 01:00",
            "2009-07-10 01:00",
            "0",
            "0.0",
            "0.0",
        ],
    ]
