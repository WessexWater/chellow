import csv
from decimal import Decimal
from io import StringIO

from utils import match, match_tables

import chellow.reports.report_429
from chellow.models import (
    BillType,
    Contract,
    GContract,
    GDn,
    GReadingFrequency,
    GUnit,
    MarketRole,
    Participant,
    ReportRun,
    Site,
    User,
    insert_bill_types,
    insert_g_reading_frequencies,
    insert_g_units,
)
from chellow.utils import utc_datetime


def test_process_g_bill_ids(mocker):
    sess = mocker.Mock()
    forecast_date = utc_datetime(2010, 4, 1)

    query = mocker.Mock()
    sess.query.return_value = query
    m_filter = mocker.Mock()
    query.filter.return_value = m_filter
    g_bill = mocker.Mock()
    m_filter.one.return_value = g_bill
    g_bill.g_reads = []

    m_filter.order_by.return_value = []

    g_bill.g_supply = mocker.Mock()
    g_bill.start_date = forecast_date
    g_bill.finish_date = forecast_date

    MockGBill = mocker.patch("chellow.reports.report_429.GBill", autospec=True)
    MockGBill.g_supply = mocker.Mock()
    MockGBill.start_date = forecast_date
    MockGBill.finish_date = forecast_date

    find_g_era_at = g_bill.g_supply.find_g_era_at

    report_context = {}
    g_bill_ids = [1]
    bill_titles = []
    vbf = mocker.Mock()
    titles = []
    csv_writer = mocker.Mock()
    g_contract = mocker.Mock()
    report_run_id = 1

    chellow.reports.report_429._process_g_bill_ids(
        sess,
        report_context,
        g_contract,
        g_bill_ids,
        forecast_date,
        bill_titles,
        vbf,
        titles,
        csv_writer,
        report_run_id,
    )

    find_g_era_at.assert_not_called()


def test_batch(mocker, sess, client):
    from_date = utc_datetime(2000, 1, 1)
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
    g_cv_rate_script = {
        "cvs": {
            "EA": {
                1: {"applicable_at": utc_datetime(2020, 10, 3), "cv": 39.2000},
            }
        }
    }
    GContract.insert_industry(
        sess, "cv", "", {}, utc_datetime(2000, 1, 1), None, g_cv_rate_script
    )
    ug_rate_script = {
        "ug_gbp_per_kwh": {"EA1": Decimal("40.1")},
    }
    GContract.insert_industry(
        sess, "ug", "", {}, utc_datetime(2000, 1, 1), None, ug_rate_script
    )
    ccl_rate_script = {"ccl_gbp_per_kwh": Decimal("0.00339")}
    GContract.insert_industry(sess, "ccl", "", {}, from_date, None, ccl_rate_script)
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
        sess,
        False,
        "Fusion 2020",
        charge_script,
        {},
        utc_datetime(2000, 1, 1),
        None,
        g_contract_rate_script,
    )
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    g_supply = site.insert_g_supply(
        sess,
        "87614362",
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
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")
    g_batch_id = g_batch.id

    breakdown = {"units_consumed": 771}
    insert_bill_types(sess)
    bill_type_n = BillType.get_by_code(sess, "N")
    g_bill = g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        breakdown,
    )
    g_bill_id = g_bill.id
    user = User.get_by_email_address(sess, "admin@example.com")
    user_id = user.id
    report_run = ReportRun.insert(sess, "g_bill_check", None, "", {})
    report_run_id = report_run.id
    sess.commit()

    mock_file = StringIO()
    mock_file.close = mocker.Mock()
    mocker.patch("chellow.reports.report_429.open_file", return_value=mock_file)

    chellow.reports.report_429.content(
        g_batch_id, g_bill_id, None, None, None, user_id, report_run_id
    )

    mock_file.seek(0)
    actual = list(csv.reader(mock_file))
    expected = [
        [
            "batch",
            "bill_reference",
            "bill_type",
            "bill_start_date",
            "bill_finish_date",
            "mprn",
            "supply_name",
            "site_code",
            "site_name",
            "covered_start",
            "covered_finish",
            "covered_bill_ids",
            "covered_units_consumed",
            "virtual_units_consumed",
            "covered_correction_factor",
            "virtual_correction_factor",
            "" "covered_unit_code",
            "virtual_unit_code",
            "covered_unit_factor",
            "virtual_unit_factor",
            "covered_calorific_value",
            "virtual_calorific_value",
            "covered_kwh",
            "virtual_kwh",
            "covered_gas_rate",
            "virtual_gas_rate",
            "covered_gas_gbp",
            "virtual_gas_gbp",
            "difference_gas_gbp",
            "covered_ccl_rate",
            "virtual_ccl_rate",
            "covered_standing_rate",
            "virtual_standing_rate",
            "covered_standing_gbp",
            "virtual_standing_gbp",
            "difference_standing_gbp",
            "covered_net_gbp",
            "virtual_net_gbp",
            "difference_net_gbp",
            "covered_vat_gbp",
            "virtual_vat_gbp",
            "difference_vat_gbp",
            "covered_gross_gbp",
            "virtual_gross_gbp",
            "difference_gross_gbp",
            "covered_problem",
            "virtual_problem",
        ],
        [
            "b1",
            "55h883",
            "N",
            "2020-01-01 00:00",
            "2020-01-31 23:30",
            "87614362",
            "main",
            "22488",
            "Water Works",
            "2020-01-01 00:00",
            "2020-01-31 23:30",
            "1",
            "771",
            "0",
            "",
            "1.0",
            "",
            "M3",
            "",
            "1.0",
            "",
            "39.2",
            "45",
            "0.0",
            "",
            "0.1",
            "",
            "0.0",
            "0.0",
            "",
            "0.00339",
            "",
            "0.1",
            "",
            "0.1",
            "-0.1",
            "12.40",
            "0.1",
            "12.3",
            "1.20",
            "0",
            "" "1.2",
            "14.52",
            "0.1",
            "14.42",
            "",
            "",
        ],
    ]
    match_tables(expected, actual)


def test_batch_http(mocker, sess, client):
    g_contract = GContract.insert(
        sess, False, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    user = User.get_by_email_address(sess, "admin@example.com")
    sess.commit()

    query_string = {"g_batch_id": g_batch.id}

    mock_Thread = mocker.patch(
        "chellow.reports.report_429.threading.Thread", autospec=True
    )
    response = client.get("/reports/429", query_string=query_string)

    match(response, 303)

    report_run_id = 1

    args = g_batch.id, None, None, None, None, user.id, report_run_id
    mock_Thread.assert_called_with(target=chellow.reports.report_429.content, args=args)


def test_bill_http(mocker, sess, client):
    site = Site.insert(sess, "22488", "Water Works")
    g_dn = GDn.insert(sess, "EE", "East of England")
    g_ldz = g_dn.insert_g_ldz(sess, "EA")
    g_exit_zone = g_ldz.insert_g_exit_zone(sess, "EA1")
    insert_g_units(sess)
    g_unit_M3 = GUnit.get_by_code(sess, "M3")
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_Z = MarketRole.get_by_code(sess, "Z")
    participant.insert_party(
        sess, market_role_Z, "None core", utc_datetime(2000, 1, 1), None, None
    )
    g_contract = GContract.insert_supplier(
        sess, "Fusion 2020", "", {}, utc_datetime(2000, 1, 1), None, {}
    )
    insert_g_reading_frequencies(sess)
    g_reading_frequency_M = GReadingFrequency.get_by_code(sess, "M")
    g_supply = site.insert_g_supply(
        sess,
        "87614362",
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
    g_batch = g_contract.insert_g_batch(sess, "b1", "Jan batch")

    breakdown = {"units_consumed": 771}
    insert_bill_types(sess)
    bill_type_n = BillType.get_by_code(sess, "N")
    g_bill = g_batch.insert_g_bill(
        sess,
        g_supply,
        bill_type_n,
        "55h883",
        "dhgh883",
        utc_datetime(2019, 4, 3),
        utc_datetime(2020, 1, 1),
        utc_datetime(2020, 1, 31, 23, 30),
        Decimal("45"),
        Decimal("12.40"),
        Decimal("1.20"),
        Decimal("14.52"),
        "",
        breakdown,
    )
    user = User.get_by_email_address(sess, "admin@example.com")
    sess.commit()

    query_string = {"g_bill_id": g_bill.id}

    mock_Thread = mocker.patch(
        "chellow.reports.report_429.threading.Thread", autospec=True
    )
    response = client.get("/reports/429", query_string=query_string)

    match(response, 303)

    report_run_id = 1

    args = None, g_bill.id, None, None, None, user.id, report_run_id
    mock_Thread.assert_called_with(target=chellow.reports.report_429.content, args=args)
