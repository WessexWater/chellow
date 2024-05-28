from collections import defaultdict
from decimal import Decimal

from chellow.e.bill_parsers.mm import _handle_0461, _handle_1455
from chellow.utils import utc_datetime


def test_handle_0461():
    headers = {"kwh": Decimal(0), "reads": []}
    pre_record = ""
    record = "".join(
        (
            "xxxxxxxxxxx",  # msn=11,
            "xx",  # unknown_1=2,
            "000000000539",  # prev_read_value=12,
            "000000000643",  # pres_read_value=12,
            "000001",  # coefficient=6,
            "   KWH",  # units=6,
            "000000000084",  # quantity=12,
            "UNIT  ",  # charge=6,
            "A",  # prev_read_type=1,
            "E",  # pres_read_type=1,
            "2276425654120",  # mpan_core=13,
            "11111111",  # mpan_top=8,
            "SINGLE             ",  # register_code=19,
            "20240401",  # pres_read_date=DATE_LENGTH,
            "20240301",  # prev_read_date=DATE_LENGTH,
        )
    )
    _handle_0461(headers, pre_record, record)
    assert headers == {
        "kwh": Decimal("84"),
        "reads": [
            {
                "msn": "xxxxxxxxxxx",
                "mpan": "11111111 22 7642 5654 120",
                "coefficient": Decimal("1"),
                "units": "kWh",
                "tpr_code": "00001",
                "prev_date": utc_datetime(2024, 3, 1, 0, 0),
                "prev_value": Decimal("539"),
                "prev_type_code": "A",
                "pres_date": utc_datetime(2024, 3, 31, 23, 0),
                "pres_value": Decimal("643"),
                "pres_type_code": "E",
            }
        ],
        "mpan_core": "22 7642 5654 120",
    }


def test_handle_1455():
    headers = {"breakdown": defaultdict(int, {})}
    pre_record = ""
    record = "".join(
        (
            "0000000000034",  # ccl_kwh=13
            "xxxxxxxx",  # unknown_1=8
            "000000000003.00",  # ccl_rate=15
            "0000000000876",  # ccl_gbp=13
        )
    )
    _handle_1455(headers, pre_record, record)
    assert headers == {
        "breakdown": {
            "ccl-kwh": Decimal("34"),
            "ccl-rate": {Decimal("0.03")},
            "ccl-gbp": Decimal("8.76"),
        }
    }
