from chellow.utils import PropDict, make_val, to_utc, ct_datetime, c_months_u


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
