from datetime import datetime as Datetime

from pytz import utc

from chellow.utils import (
    PropDict,
    c_months_u,
    ct_datetime,
    hh_format,
    make_val,
    parse_hh_start,
    to_utc,
    u_months_u,
    utc_datetime,
)


def test_make_val():
    v = {0, "hello"}
    make_val(v)


def test_PropDict_create():
    location = "loc"
    props = {0: [{0: 1}]}
    PropDict(location, props)


def test_PropDict_get():
    assert PropDict("cont " + str(Datetime(2017, 1, 1)), {}, []).get("akey") is None


def test_PropDict():
    assert PropDict("", {"*": 5})[1] == 5


def test_PropDict_nested():
    assert PropDict("", {1: {"*": 5}})[1][1] == 5


def test_to_utc():
    dt_utc = to_utc(ct_datetime(2014, 9, 6, 1))
    assert dt_utc == Datetime(2014, 9, 6, 0, 0, tzinfo=utc)


def test_c_months_u():
    finish_year, finish_month = 2009, 3
    start, _ = next(
        c_months_u(finish_year=finish_year, finish_month=finish_month, months=1)
    )
    assert start == to_utc(ct_datetime(finish_year, finish_month))


def test_c_months_u_start_finish():
    start_year, start_month, finish_year, finish_month = 2009, 3, 2009, 4
    month_list = list(
        c_months_u(
            start_year=start_year,
            start_month=start_month,
            finish_year=finish_year,
            finish_month=finish_month,
        )
    )
    print(month_list)
    assert month_list == [
        (to_utc(ct_datetime(2009, 3)), to_utc(ct_datetime(2009, 3, 31, 23, 30))),
        (to_utc(ct_datetime(2009, 4)), to_utc(ct_datetime(2009, 4, 30, 23, 30))),
    ]


def test_u_months_u_start_none():
    start_year, start_month = 2009, 3
    month_1 = next(
        u_months_u(start_year=start_year, start_month=start_month, months=None)
    )
    assert month_1 == (utc_datetime(2009, 3), utc_datetime(2009, 3, 31, 23, 30))


def test_hh_format_ct():
    dt = utc_datetime(2019, 6, 30)
    actual = hh_format(dt)
    assert actual == ("2019-06-30 01:00")


def test_hh_format_hh():
    dt = utc_datetime(2019, 6, 30)
    actual = hh_format(dt, with_hh=True)
    assert actual == ("2019-06-30 01:00", 3)


def test_hh_format_hh_46():
    dt = to_utc(ct_datetime(2019, 3, 31, 23, 30))
    actual = hh_format(dt, with_hh=True)
    assert actual == ("2019-03-31 23:30", 46)


def test_hh_format_hh_50():
    dt = to_utc(ct_datetime(2019, 10, 27, 23, 30))
    actual = hh_format(dt, with_hh=True)
    assert actual == ("2019-10-27 23:30", 50)


def test_hh_format_none():
    dt = None
    actual = hh_format(dt)
    assert actual == "ongoing"


def test_parse_hh_start():
    actual = parse_hh_start("2019-01-01 00:00Z")
    assert actual == utc_datetime(2019, 1, 1)
