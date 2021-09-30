from decimal import Decimal

from chellow.e_views import get_era_bundles
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
    Participant,
    Pc,
    Site,
    Source,
    VoltageLevel,
    insert_bill_types,
    insert_comms,
    insert_cops,
    insert_energisation_statuses,
    insert_sources,
    insert_voltage_levels,
)
from chellow.utils import utc_datetime


def test_get_era_bundles_bill_after_supply_end(sess, client):
    """Check that a bill starting after the end of a supply still gets
    shown.
    """
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
    Mtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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
    Mtc.insert(
        sess,
        None,
        "845",
        "HH COP5 And Above With Comms",
        False,
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
    dno.insert_llfc(
        sess,
        "510",
        "PC 5-8 & HH HV",
        voltage_level,
        False,
        True,
        utc_datetime(1996, 1, 1),
        None,
    )
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
