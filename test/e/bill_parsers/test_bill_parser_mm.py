from decimal import Decimal

from chellow.e.bill_parsers.mm import _handle_0461
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
                "units": "kwh",
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
