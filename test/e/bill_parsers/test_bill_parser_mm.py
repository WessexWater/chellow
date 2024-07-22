from collections import defaultdict
from decimal import Decimal

from chellow.e.bill_parsers.mm import (
    _handle_0101,
    _handle_0461,
    _handle_0860,
    _handle_1455,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_handle_0101():
    headers = {}
    pre_record = ""
    record = "".join(
        (
            "20240618",  # start_date=DATE_LENGTH
            "20240618",  # finish_date=DATE_LENGTH)
        )
    )
    _handle_0101(headers, pre_record, record)
    assert headers == {
        "start_date": to_utc(ct_datetime(2024, 6, 18)),
        "finish_date": to_utc(ct_datetime(2024, 6, 18, 23, 30)),
    }


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
            "N",  # prev_read_type=1,
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
                "prev_type_code": "N",
                "pres_date": utc_datetime(2024, 3, 31, 23, 0),
                "pres_value": Decimal("643"),
                "pres_type_code": "E",
            }
        ],
        "mpan_core": "22 7642 5654 120",
    }


def test_handle_0860():
    headers = {"breakdown": defaultdict(int, {})}
    pre_record = ""
    record = "".join(
        (
            "000000000456",  # metering_gbp=12
            "xxxxxxxxxxxx",  # unknown_1=12
            "xxxxxxxxxxxx",  # unknown_2=12
            "20240613",  # metering_date=DATE_LENGTH
            "x" * 80,  # description=80
        )
    )
    _handle_0860(headers, pre_record, record)
    assert headers == {
        "breakdown": {
            "metering-gbp": Decimal("4.56"),
        }
    }


def test_handle_1455():
    headers = {"breakdown": defaultdict(int, {})}
    pre_record = ""
    record = "".join(
        (
            "0000000000034",  # ccl_kwh=13
            "xxxxxxxx",  # unknown_1=8
            "000000000003.00",  # ccl_rate=15
            "000000000876",  # ccl_gbp=12
            "0       ",  # unknown_2=8
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
