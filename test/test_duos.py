from collections import defaultdict

import pytest

import chellow.duos
from chellow.models import MarketRole, Participant, VoltageLevel, insert_voltage_levels
from chellow.utils import BadRequest, ct_datetime, hh_range, to_utc


def test_duos_availability_from_to(mocker, sess):
    caches = {"dno": {"22": {}}}
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", to_utc(ct_datetime(2000, 1, 1)), None, "22"
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
        to_utc(ct_datetime(1996, 1, 1)),
        None,
    )

    month_from = to_utc(ct_datetime(2019, 2, 1))
    month_to = to_utc(ct_datetime(2019, 2, 28, 23, 30))

    for hh in hh_range(caches, month_from, month_to):
        llfc.insert_laf(sess, hh, 1)

    sess.commit()

    ds = mocker.Mock()
    ds.dno_code = "22"
    ds.gsp_group_code = "_L"
    ds.llfc_code = "510"
    ds.is_displaced = False
    ds.sc = 0
    ds.supplier_bill = defaultdict(int)
    ds.supplier_rate_sets = defaultdict(set)
    ds.get_data_sources = mocker.Mock(return_value=[])
    ds.caches = caches
    ds.sess = sess

    hh = {
        "start-date": ct_datetime(2019, 2, 28, 23, 30),
        "ct-decimal-hour": 23.5,
        "ct-is-month-end": True,
        "ct-day-of-week": 3,
        "ct-year": 2019,
        "ct-month": 2,
        "msp-kwh": 0,
        "imp-msp-kvarh": 0,
        "exp-msp-kvarh": 0,
    }
    chellow.duos.datum_2010_04_01(ds, hh)

    ds.get_data_sources.assert_called_with(month_from, month_to)


def test_lafs_hist(mocker, sess):
    caches = {"dno": {"22": {}}}
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", to_utc(ct_datetime(2000, 1, 1)), None, "22"
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
        to_utc(ct_datetime(1996, 1, 1)),
        None,
    )

    hist_laf = 1.5
    start_date = to_utc(ct_datetime(2019, 2, 28, 23, 30))
    hist_date = to_utc(ct_datetime(2018, 2, 28, 23, 30))
    llfc.insert_laf(sess, hist_date, hist_laf)

    sess.commit()

    ds = mocker.Mock()
    ds.start_date = start_date
    ds.finish_date = start_date
    ds.dno_code = "22"
    ds.gsp_group_code = "_L"
    ds.llfc_code = "510"
    ds.is_displaced = False
    ds.sc = 0
    ds.supplier_bill = defaultdict(int)
    ds.supplier_rate_sets = defaultdict(set)
    ds.get_data_sources = mocker.Mock(return_value=iter([ds]))
    ds.caches = caches
    ds.sess = sess
    ds.hh_data = []

    hh = {
        "hist-start": hist_date,
        "start-date": start_date,
        "ct-decimal-hour": 23.5,
        "ct-is-month-end": True,
        "ct-day-of-week": 3,
        "ct-year": 2019,
        "ct-month": 2,
        "msp-kwh": 0,
        "imp-msp-kvarh": 0,
        "exp-msp-kvarh": 0,
    }
    chellow.duos.datum_2012_02_23(ds, hh)

    assert caches["dno"]["22"]["lafs"]["510"][start_date] == hist_laf


def test_lafs_forecast_none(mocker, sess):
    caches = {"dno": {"22": {}}}
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", to_utc(ct_datetime(2000, 1, 1)), None, "22"
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
        to_utc(ct_datetime(1996, 1, 1)),
        None,
    )

    start_date = to_utc(ct_datetime(2019, 2, 28, 23, 30))
    hist_date = to_utc(ct_datetime(2018, 2, 28, 23, 30))

    sess.commit()

    ds = mocker.Mock()
    ds.forecast_date = hist_date
    ds.start_date = start_date
    ds.finish_date = start_date
    ds.dno_code = "22"
    ds.gsp_group_code = "_L"
    ds.llfc_code = "510"
    ds.is_displaced = False
    ds.sc = 0
    ds.supplier_bill = defaultdict(int)
    ds.supplier_rate_sets = defaultdict(set)
    ds.get_data_sources = mocker.Mock(return_value=iter([ds]))
    ds.caches = caches
    ds.sess = sess

    hh = {
        "hist-start": hist_date,
        "start-date": start_date,
        "ct-decimal-hour": 23.5,
        "ct-is-month-end": True,
        "ct-day-of-week": 3,
        "ct-year": 2019,
        "ct-month": 2,
        "msp-kwh": 0,
        "imp-msp-kvarh": 0,
        "exp-msp-kvarh": 0,
    }
    with pytest.raises(
        BadRequest,
        match="Missing LAF for DNO 22 and LLFC 510 and timestamps 2019-02-28 23:30, "
        "2018-02-28 23:30 and 2018-02-28 23:30",
    ):
        chellow.duos.datum_2012_02_23(ds, hh)


def test_lafs_forecast(mocker, sess):
    caches = {"dno": {"22": {}}}
    participant = Participant.insert(sess, "CALB", "AK Industries")
    market_role_R = MarketRole.insert(sess, "R", "Distributor")
    dno = participant.insert_party(
        sess, market_role_R, "WPD", to_utc(ct_datetime(2000, 1, 1)), None, "22"
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
        to_utc(ct_datetime(1996, 1, 1)),
        None,
    )

    forecast_date = to_utc(ct_datetime(2018, 5, 31, 23, 30))
    llfc.insert_laf(sess, forecast_date, 1.4)

    sess.commit()

    hist_date = to_utc(ct_datetime(2018, 2, 28, 23, 30))
    start_date = to_utc(ct_datetime(2019, 2, 28, 23, 30))

    ds = mocker.Mock()
    ds.start_date = start_date
    ds.finish_date = start_date
    ds.forecast_date = forecast_date
    ds.dno_code = "22"
    ds.gsp_group_code = "_L"
    ds.llfc_code = "510"
    ds.is_displaced = False
    ds.sc = 0
    ds.supplier_bill = defaultdict(int)
    ds.supplier_rate_sets = defaultdict(set)
    ds.get_data_sources = mocker.Mock(return_value=iter([ds]))
    ds.caches = caches
    ds.sess = sess
    ds.hh_data = []

    hh = {
        "hist-start": hist_date,
        "start-date": start_date,
        "ct-decimal-hour": 23.5,
        "ct-is-month-end": True,
        "ct-day-of-week": 3,
        "ct-year": 2019,
        "ct-month": 2,
        "msp-kwh": 0,
        "imp-msp-kvarh": 0,
        "exp-msp-kvarh": 0,
    }
    chellow.duos.datum_2012_02_23(ds, hh)
