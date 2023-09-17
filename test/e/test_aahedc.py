from decimal import Decimal

from chellow.e.aahedc import hh
from chellow.utils import ct_datetime, to_utc


def test_hh(sess, mocker):
    mock_ss = mocker.Mock()
    mock_ss.caches = {}
    datum = {"gsp-kwh": 1, "start-date": to_utc(ct_datetime(2020, 1, 1))}
    mock_ss.hh_data = [datum]
    rate = Decimal("1.0")
    aahedc_rate_script = {"aahedc_gbp_per_gsp_kwh": rate}
    mock_ss.non_core_rate.return_value = aahedc_rate_script
    hh(mock_ss)

    assert isinstance(datum["aahedc-rate"], float)
