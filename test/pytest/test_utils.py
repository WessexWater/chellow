from chellow.utils import (
    PropDict, make_val, to_utc, ct_datetime, c_months_u, utc_datetime,
    hh_format_ct, u_months_u)


def test_make_val():
    v = {0, 'hello'}
    make_val(v)


def test_PropDict():
    location = 'loc'
    props = {
        0: [{0: 1}]
    }
    PropDict(location, props)


def test_c_months_u():
    finish_year, finish_month = 2009, 3
    start, _ = next(
        c_months_u(
            finish_year=finish_year, finish_month=finish_month, months=1))
    assert start == to_utc(ct_datetime(finish_year, finish_month))


def test_c_months_u_start_finish():
    start_year, start_month, finish_year, finish_month = 2009, 3, 2009, 4
    month_list = list(
        c_months_u(
            start_year=start_year, start_month=start_month,
            finish_year=finish_year, finish_month=finish_month))
    print(month_list)
    assert month_list == [
        (
            to_utc(ct_datetime(2009, 3)),
            to_utc(ct_datetime(2009, 3, 31, 23, 30))
        ),
        (
            to_utc(ct_datetime(2009, 4)),
            to_utc(ct_datetime(2009, 4, 30, 23, 30))
        )
    ]


def test_u_months_u_start_none():
    start_year, start_month = 2009, 3
    month_1 = next(
        u_months_u(
            start_year=start_year, start_month=start_month, months=None))
    assert month_1 == (
        utc_datetime(2009, 3), utc_datetime(2009, 3, 31, 23, 30))


def test_hh_format_ct():
    dt = utc_datetime(2019, 6, 30)
    actual = hh_format_ct(dt)
    assert actual == ('2019-06-30 01:00', 3)


def test_hh_format_ct_46():
    dt = to_utc(ct_datetime(2019, 3, 31, 23, 30))
    actual = hh_format_ct(dt)
    assert actual == ('2019-03-31 23:30', 46)


def test_hh_format_ct_50():
    dt = to_utc(ct_datetime(2019, 10, 27, 23, 30))
    actual = hh_format_ct(dt)
    assert actual == ('2019-10-27 23:30', 50)
