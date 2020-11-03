from decimal import Decimal

from chellow.e_views import get_era_bundles
from chellow.models import (
    BillType, Contract, Cop, GspGroup, MarketRole, MeterPaymentType, MeterType,
    Mtc, Participant, Pc, Site, Source, VoltageLevel, insert_bill_types,
    insert_cops, insert_sources, insert_voltage_levels
)
from chellow.utils import utc_datetime


def test_get_era_bundles_bill_after_supply_end(sess, client):
    ''' Check that a bill starting after the end of a supply still gets
        shown.
    '''
    site = Site.insert(sess, '22488', 'Water Works')
    insert_sources(sess)
    source = Source.get_by_code(sess, 'net')
    gsp_group = GspGroup.insert(sess, '_L', 'South Western')
    participant = Participant.insert(sess, 'hhak', 'AK Industries')
    market_role_X = MarketRole.insert(sess, 'X', 'Supplier')
    market_role_M = MarketRole.insert(sess, 'M', 'Mop')
    market_role_C = MarketRole.insert(sess, 'C', 'HH Dc')
    market_role_R = MarketRole.insert(sess, 'R', 'Distributor')
    participant.insert_party(
        sess, market_role_M, 'Fusion Mop Ltd', utc_datetime(2000, 1, 1), None,
        None)
    participant.insert_party(
        sess, market_role_X, 'Fusion Ltc', utc_datetime(2000, 1, 1), None,
        None)
    participant.insert_party(
        sess, market_role_C, 'Fusion DC', utc_datetime(2000, 1, 1), None,
        None)
    mop_contract = Contract.insert_mop(
        sess, 'Fusion', participant, '', {}, utc_datetime(2000, 1, 1), None,
        {})
    dc_contract = Contract.insert_hhdc(
        sess, 'Fusion DC 2000', participant, '', {}, utc_datetime(2000, 1, 1),
        None, {})
    pc = Pc.insert(sess, '00', 'hh', utc_datetime(2000, 1, 1), None)
    insert_cops(sess)
    cop = Cop.get_by_code(sess, '5')
    imp_supplier_contract = Contract.insert_supplier(
        sess, 'Fusion Supplier 2000', participant, '', {},
        utc_datetime(2000, 1, 1), None, {})
    dno = participant.insert_party(
        sess, market_role_R, 'WPD', utc_datetime(2000, 1, 1), None, '22')
    meter_type = MeterType.insert(
        sess, 'C5', 'COP 1-5', utc_datetime(2000, 1, 1), None)
    meter_payment_type = MeterPaymentType.insert(
        sess, 'CR', 'Credit', utc_datetime(1996, 1, 1), None)
    Mtc.insert(
        sess, None, '845', 'HH COP5 And Above With Comms', False, False, True,
        meter_type, meter_payment_type, 0, utc_datetime(1996, 1, 1), None)
    insert_voltage_levels(sess)
    voltage_level = VoltageLevel.get_by_code(sess, 'HV')
    dno.insert_llfc(
        sess, '510', 'PC 5-8 & HH HV', voltage_level, False, True,
        utc_datetime(1996, 1, 1), None)
    supply = site.insert_e_supply(
        sess, source, None, "Bob", utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31), gsp_group, mop_contract, '773',
        dc_contract, 'ghyy3', 'hgjeyhuw', pc, '845', cop, None, {},
        '22 7867 6232 781', '510', imp_supplier_contract, '7748', 361,
        None, None, None, None, None)
    batch = imp_supplier_contract.insert_batch(sess, 'b1', 'batch 1')
    insert_bill_types(sess)
    bill_type_N = BillType.get_by_code(sess, 'N')
    batch.insert_bill(
        sess, 'ytgeklf', 's77349', utc_datetime(2020, 2, 10),
        utc_datetime(2020, 2, 2), utc_datetime(2020, 3, 1), Decimal(0),
        Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), bill_type_N, {},
        supply)
    sess.commit()

    bundles = get_era_bundles(sess, supply)
    print(bundles)

    assert len(bundles[0]['imp_bills']['bill_dicts']) == 1
