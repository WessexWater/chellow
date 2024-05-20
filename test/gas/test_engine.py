from decimal import Decimal

from chellow.gas.engine import GDataSource, _bill_kwh, _find_hhs, find_cv
from chellow.models import (
    Contract,
    GContract,
    GDn,
    GReadingFrequency,
    GUnit,
    MarketRole,
    Participant,
    Site,
    insert_g_reading_frequencies,
    insert_g_units,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_find_cv(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "None core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    g_cv_rate_script = {
        "cvs": {
            "EA": {
                1: {"applicable_at": utc_datetime(2020, 10, 3), "cv": 39.2101},
            }
        }
    }
    GContract.insert_industry(sess, "cv", "", {}, vf, None, g_cv_rate_script)
    sess.commit()

    caches = {}
    dt = to_utc(ct_datetime(2020, 1, 1))
    cv, avg_cv = find_cv(sess, caches, dt, g_ldz.code)

    assert (cv, avg_cv) == (39.2101, 39.2101)


def test_find_hhs_pairs_before_after_chunk_finish(mocker):
    """If there's a meter change, a pair can start after the end of the chunk.
    here we test the case for a pair before and after the chunk finish.
    """
    mocker.patch("chellow.gas.engine.find_cv", return_value=(39, 39))
    sess = mocker.Mock()
    caches = {}
    hist_g_era = mocker.Mock()
    hist_g_era.correction_factor = 1
    hist_g_era.g_unit = mocker.Mock()
    hist_g_era.g_unit.code = "M3"
    hist_g_era.g_unit.factor = 1
    hist_g_era.aq = 1
    hist_g_era.soq = 1

    pairs = [
        {"start-date": utc_datetime(2010, 1, 1), "units": 1},
        {"start-date": utc_datetime(2010, 1, 1, 0, 30), "units": 1},
    ]
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1)
    g_ldz_code = "SW"
    hhs = _find_hhs(
        sess, caches, hist_g_era, pairs, chunk_start, chunk_finish, g_ldz_code
    )
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            "unit_code": "M3",
            "unit_factor": 1.0,
            "units_consumed": 1,
            "aq": 1,
            "soq": 1,
            "correction_factor": 1.0,
            "calorific_value": 39,
            "avg_cv": 39,
        }
    }

    assert pairs == [
        {
            "start-date": utc_datetime(2010, 1, 1),
            "units": 1,
            "finish-date": utc_datetime(2010, 1, 1),
        },
    ]


def test_find_hhs_pair_after_chunk_finish(mocker):
    """If there's a meter change, a pair can start after the end of the chunk.
    Here we test for a single pair after the chunk finish.
    """
    mocker.patch("chellow.gas.engine.find_cv", return_value=(39, 39))
    sess = mocker.Mock()
    caches = {}
    hist_g_era = mocker.Mock()
    hist_g_era.correction_factor = 1
    hist_g_era.aq = 1
    hist_g_era.soq = 1
    hist_g_era.g_unit = mocker.Mock()
    hist_g_era.g_unit.code = "M3"
    hist_g_era.g_unit.factor = 1

    pairs = [{"start-date": utc_datetime(2010, 1, 1, 0, 30), "units": 1}]
    chunk_start = utc_datetime(2010, 1, 1)
    chunk_finish = utc_datetime(2010, 1, 1)
    g_ldz_code = "SW"
    hhs = _find_hhs(
        sess, caches, hist_g_era, pairs, chunk_start, chunk_finish, g_ldz_code
    )
    assert hhs == {
        utc_datetime(2010, 1, 1): {
            "unit_code": "M3",
            "unit_factor": 1.0,
            "units_consumed": 1,
            "aq": 1,
            "soq": 1,
            "correction_factor": 1.0,
            "calorific_value": 39,
            "avg_cv": 39,
        }
    }

    assert pairs == [
        {
            "start-date": utc_datetime(2010, 1, 1),
            "units": 1,
            "finish-date": utc_datetime(2010, 1, 1),
        },
    ]


def test_GDataSource_init(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "None core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    g_cv_rate_script = {
        "cvs": {
            "EA": {
                1: {"applicable_at": utc_datetime(2020, 10, 3), "cv": 39.2000},
            }
        }
    }
    GContract.insert_industry(sess, "cv", "", {}, vf, None, g_cv_rate_script)
    ug_rate_script = {
        "ug_gbp_per_kwh": {"EA1": Decimal("40.1")},
    }
    GContract.insert_industry(sess, "ug", "", {}, vf, None, ug_rate_script)
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
    charge_script = """
from chellow.gas.engine import g_rates
from chellow.utils import reduce_bill_hhs


def virtual_bill_titles():
    return [
        'units_consumed', 'correction_factor', 'unit_code', 'unit_factor',
        'calorific_value', 'kwh', 'gas_rate', 'gas_gbp', 'ccl_rate',
        'standing_rate', 'standing_gbp', 'net_gbp', 'vat_gbp', 'gross_gbp',
        'problem']


def virtual_bill(ds):
    for hh in ds.hh_data:
        start_date = hh['start_date']
        bill_hh = ds.bill_hhs[start_date]
        bill_hh['units_consumed'] = hh['units_consumed']
        bill_hh['correction_factor'] = {hh['correction_factor']}
        bill_hh['unit_code'] = {hh['unit_code']}
        bill_hh['unit_factor'] = {hh['unit_factor']}
        bill_hh['calorific_value'] = {hh['calorific_value']}
        kwh = hh['kwh']
        bill_hh['kwh'] = kwh
        gas_rate = float(
            g_rates(ds.sess, ds.caches, db_id, start_date)['gas_rate'])
        bill_hh['gas_rate'] = {gas_rate}
        bill_hh['gas_gbp'] = gas_rate * kwh

        if hh['utc_is_month_end']:
            standing_rate = float(
                g_rates(
                    ds.sess, ds.caches, db_id, start_date)['standing_rate'])
            bill_hh['standing_rate'] = {standing_rate}
            bill_hh['standing_gbp'] = standing_rate
        if hh['utc_decimal_hour'] == 0:
            pass

        bill_hh['net_gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat_gbp'] = 0
        bill_hh['gross_gbp'] = bill_hh['net_gbp'] + bill_hh['vat_gbp']

    ds.bill = reduce_bill_hhs(ds.bill_hhs)
"""
    g_contract_rate_script = {
        "gas_rate": 0.1,
        "standing_rate": 0.1,
    }
    g_contract = GContract.insert(
        sess,
        False,
        "Fusion 2020",
        charge_script,
        {},
        vf,
        None,
        g_contract_rate_script,
    )
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    msn = "hgeu8rhg"
    g_supply = site.insert_g_supply(
        sess,
        "87614362",
        "main",
        g_exit_zone,
        utc_datetime(2010, 1, 1),
        None,
        msn,
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    sess.commit()

    g_era = g_supply.g_eras[0]
    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 31, 23, 30))
    fdate = to_utc(ct_datetime(2020, 3, 1))
    caches = {}
    g_bill = None
    GDataSource(sess, start_date, finish_date, fdate, g_era, caches, g_bill)


def test_bill_kwh(sess):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.insert(sess, "Z", "None core")
    participant.insert_party(sess, market_role_Z, "None core", vf, None, None)
    g_cv_rate_script = {
        "cvs": {
            "EA": {
                1: {"applicable_at": utc_datetime(2020, 10, 3), "cv": 39.2000},
            }
        }
    }
    GContract.insert_industry(sess, "cv", "", {}, vf, None, g_cv_rate_script)
    ug_rate_script = {
        "ug_gbp_per_kwh": {"EA1": Decimal("40.1")},
    }
    GContract.insert_industry(sess, "ug", "", {}, vf, None, ug_rate_script)
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
    charge_script = """
from chellow.gas.engine import g_rates
from chellow.utils import reduce_bill_hhs


def virtual_bill_titles():
    return [
        'units_consumed', 'correction_factor', 'unit_code', 'unit_factor',
        'calorific_value', 'kwh', 'gas_rate', 'gas_gbp', 'ccl_rate',
        'standing_rate', 'standing_gbp', 'net_gbp', 'vat_gbp', 'gross_gbp',
        'problem']


def virtual_bill(ds):
    for hh in ds.hh_data:
        start_date = hh['start_date']
        bill_hh = ds.bill_hhs[start_date]
        bill_hh['units_consumed'] = hh['units_consumed']
        bill_hh['correction_factor'] = {hh['correction_factor']}
        bill_hh['unit_code'] = {hh['unit_code']}
        bill_hh['unit_factor'] = {hh['unit_factor']}
        bill_hh['calorific_value'] = {hh['calorific_value']}
        kwh = hh['kwh']
        bill_hh['kwh'] = kwh
        gas_rate = float(
            g_rates(ds.sess, ds.caches, db_id, start_date)['gas_rate'])
        bill_hh['gas_rate'] = {gas_rate}
        bill_hh['gas_gbp'] = gas_rate * kwh

        if hh['utc_is_month_end']:
            standing_rate = float(
                g_rates(
                    ds.sess, ds.caches, db_id, start_date)['standing_rate'])
            bill_hh['standing_rate'] = {standing_rate}
            bill_hh['standing_gbp'] = standing_rate
        if hh['utc_decimal_hour'] == 0:
            pass

        bill_hh['net_gbp'] = sum(
            v for k, v in bill_hh.items() if k.endswith('gbp'))
        bill_hh['vat_gbp'] = 0
        bill_hh['gross_gbp'] = bill_hh['net_gbp'] + bill_hh['vat_gbp']

    ds.bill = reduce_bill_hhs(ds.bill_hhs)
"""
    g_contract_rate_script = {
        "gas_rate": 0.1,
        "standing_rate": 0.1,
    }
    g_contract = GContract.insert(
        sess,
        False,
        "Fusion 2020",
        charge_script,
        {},
        vf,
        None,
        g_contract_rate_script,
    )
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    msn = "hgeu8rhg"
    g_supply = site.insert_g_supply(
        sess,
        "87614362",
        "main",
        g_exit_zone,
        utc_datetime(2010, 1, 1),
        None,
        msn,
        1,
        g_unit_M3,
        g_contract,
        "d7gthekrg",
        g_reading_frequency_M,
        1,
        1,
    )
    sess.commit()

    g_era = g_supply.g_eras[0]
    chunk_start = to_utc(ct_datetime(2020, 1, 1))
    chunk_finish = to_utc(ct_datetime(2020, 1, 31, 23, 30))
    caches = {}
    hist_map = {}
    _bill_kwh(
        sess,
        caches,
        g_supply,
        g_era,
        chunk_start,
        chunk_finish,
        hist_map,
        g_ldz.code,
    )
