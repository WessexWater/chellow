import csv
from decimal import Decimal
from io import StringIO

import chellow.reports.report_g_supplies_snapshot
from chellow.models import (
    BillType,
    Contract,
    GContract,
    GDn,
    GReadType,
    GReadingFrequency,
    GUnit,
    MarketRole,
    Participant,
    Site,
    insert_bill_types,
    insert_g_read_types,
    insert_g_reading_frequencies,
    insert_g_units,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_supply(mocker, sess, client):
    vf = to_utc(ct_datetime(2000, 1, 1))
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.get_by_code(sess, "Z")
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
    ccl_rate_script = {
        "ccl_gbp_per_kwh": Decimal("0.00525288"),
    }
    GContract.insert_industry(sess, "ccl", "", {}, vf, None, ccl_rate_script)
    bank_holiday_rate_script = {"bank_holidays": []}
    Contract.insert_non_core(
        sess, "bank_holidays", "", {}, vf, None, bank_holiday_rate_script
    )
    charge_script = """
import chellow.gas.ccl
from chellow.gas.engine import g_rates
from chellow.utils import reduce_bill_hhs


def virtual_bill_titles():
    return [
        'units_consumed', 'correction_factor', 'unit_code', 'unit_factor',
        'calorific_value', 'kwh', 'gas_rate', 'gas_gbp', 'ccl_rate',
        'standing_rate', 'standing_gbp', 'net_gbp', 'vat_gbp', 'gross_gbp',
        'problem']


def virtual_bill(ds):
    chellow.gas.ccl.vb(ds)
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
            g_rates(ds.sess, ds.caches, db_id, start_date, False)['gas_rate'])
        bill_hh['gas_rate'] = {gas_rate}
        bill_hh['gas_gbp'] = gas_rate * kwh
        bill_hh['ccl_kwh'] = kwh
        ccl_rate = hh['ccl']
        bill_hh['ccl_rate'] = {ccl_rate}
        bill_hh['ccl_kwh'] = kwh
        bill_hh['ccl_gbp'] = kwh * ccl_rate

        bill_hh['aq'] = 4
        bill_hh['soq'] = 5
        if hh['utc_is_month_end']:
            standing_rate = float(
                g_rates(
                    ds.sess, ds.caches, db_id, start_date, False)['standing_rate'])
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
        sess, False, "Fusion 2020", charge_script, {}, vf, None, g_contract_rate_script
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
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    breakdown = {"units_consumed": 771}
    insert_bill_types(sess)
    bill_type_N = BillType.get_by_code(sess, "N")
    insert_g_read_types(sess)
    g_read_type_A = GReadType.get_by_code(sess, "A")
    g_bill = g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_N,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2015, 9, 1),
        utc_datetime(2015, 9, 30, 22, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        breakdown,
    )
    g_bill.insert_g_read(
        sess,
        msn,
        g_unit_M3,
        Decimal("1"),
        Decimal("37"),
        Decimal("90"),
        utc_datetime(2015, 9, 1),
        g_read_type_A,
        Decimal("890"),
        utc_datetime(2015, 9, 25),
        g_read_type_A,
    )
    sess.commit()

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch(
        "chellow.reports.report_g_supplies_snapshot.open_file",
        return_value=mock_file,
    )

    user = mocker.Mock()
    g_supply_id = g_supply.id
    date = utc_datetime(2020, 9, 1)

    chellow.reports.report_g_supplies_snapshot.content(date, g_supply_id, user)

    mock_file.seek(0)
    sheet = csv.reader(mock_file)
    table = list(sheet)

    expected = [
        [
            "Date",
            "Physical Site Id",
            "Physical Site Name",
            "Other Site Ids",
            "Other Site Names",
            "MPRN",
            "Exit Zone",
            "Meter Serial Number",
            "Correction Factor",
            "Unit",
            "Contract",
            "Account",
            "Supply Start",
            "Supply Finish",
            "reading_frequency",
            "aq",
            "soq",
        ],
        [
            "2020-09-01 01:00",
            "22488",
            "Water Works",
            "",
            "",
            "87614362",
            "EA1",
            "hgeu8rhg",
            "1",
            "M3",
            "Fusion 2020",
            "d7gthekrg",
            "2010-01-01 00:00",
            "",
            "M",
            "4",
            "5",
        ],
    ]

    assert expected == table
