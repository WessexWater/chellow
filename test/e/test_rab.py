from chellow.e.rab import _parse_date
from chellow.utils import ct_datetime, to_utc


def test_parse_date():
    assert _parse_date("01/01/2026") == to_utc(ct_datetime(2026, 1, 1))
