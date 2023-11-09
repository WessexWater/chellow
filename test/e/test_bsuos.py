from decimal import Decimal

import pytest

from chellow.e.bsuos import _process_url, extract_rates


def test_process_url_csv(mocker, sess):
    res = mocker.Mock()
    res.text = "Date"
    res.status_code = 200
    res.reason = "okay"
    logger = mocker.Mock()
    contract = mocker.Mock()
    url = mocker.Mock()
    s = mocker.Mock()
    s.get = mocker.Mock(return_value=res)
    _process_url(logger, sess, url, contract, s)


@pytest.mark.parametrize(
    "line,rates",
    [
        [
            "BSUoS Tariff £/MWh  £13.41   BSUoS Tariff £/MWh  £14.03",
            [Decimal("13.41"), Decimal("14.03")],
        ],
        [
            "BSUoS Tariff £/MWh £7.63 BSUoS Tariff £/MWh £7.60Fixed Tariff 4",
            [Decimal("7.63"), Decimal("7.60")],
        ],
    ],
)
def test_extract_rate(line, rates):
    actual = extract_rates(line)
    assert actual == rates
