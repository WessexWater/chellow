from collections import defaultdict
from decimal import Decimal

from chellow.gas.bill_parser_total_edi import (
    _process_CCD2,
    _process_MHD,
    _to_finish_date,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_to_finish_date():
    actual = _to_finish_date("211031")
    assert actual == to_utc(ct_datetime(2021, 10, 31, 23, 30))


def test_process_MHD():
    message_type = "UTLBIL"
    headers = {}
    elements = {"TYPE": [message_type, "3"]}
    _process_MHD(elements, headers)

    expected_headers = {
        "message_type": message_type,
        "reads": [],
        "raw_lines": [],
        "breakdown": {"units_consumed": Decimal("0")},
        "kwh": Decimal("0.00"),
        "net": Decimal("0.00"),
        "vat": Decimal("0.00"),
        "gross": Decimal("0.00"),
    }
    assert headers == expected_headers


def test_process_CCD2():
    headers = {}
    headers["reads"] = []
    headers["raw_lines"] = []
    headers["breakdown"] = defaultdict(int, {"units_consumed": Decimal(0)})
    headers["kwh"] = Decimal("0.00")
    headers["net"] = Decimal("0.00")
    headers["vat"] = Decimal("0.00")
    headers["gross"] = Decimal("0.00")
    elements = {
        "CCDE": ["", "", "MET"],
        "NUCT": ["968823", "KWH"],
        "MTNR": [],
        "CONB": [],
        "ADJF": [],
        "PRDT": [],
        "PVDT": [],
        "PRRD": [],
        "MLOC": ["978672"],
        "CSDT": ["240401"],
        "CEDT": ["240430"],
        "CTOT": ["3882"],
        "CPPU": ["9742"],
    }
    _process_CCD2(elements, headers)
    print(headers)
    expected_headers = {
        "reads": [],
        "raw_lines": [],
        "breakdown": {
            "units_consumed": Decimal("0"),
            "commodity_rate": {Decimal("0.09742")},
            "commodity_gbp": Decimal("38.82"),
            "commodity_kwh": Decimal("968.823"),
        },
        "kwh": Decimal("968.823"),
        "net": Decimal("0.00"),
        "vat": Decimal("0.00"),
        "gross": Decimal("0.00"),
        "start_date": utc_datetime(2024, 3, 31, 23, 0),
        "finish_date": utc_datetime(2024, 4, 30, 22, 30),
        "mprn": "978672",
    }

    assert headers == expected_headers
