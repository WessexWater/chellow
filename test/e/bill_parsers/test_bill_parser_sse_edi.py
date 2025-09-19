from collections import defaultdict
from decimal import Decimal
from io import BytesIO

from chellow.e.bill_parsers.sse_edi import (
    Parser,
    _process_BTL,
    _process_CCD2,
    _process_CCD3,
    _process_CCD4,
    _process_MTR,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_missing_mpan_core(mocker, sess):
    file_lines = [
        "MHD=2+UTLBIL:3'",
        "BTL=+18511+8480++80612'",
        "MTR=6'",
    ]
    f = BytesIO(b"\n".join(n.encode("utf8") for n in file_lines))
    parser = Parser(f)
    bills = parser.make_raw_bills()
    expected_bill = {
        "bill_type_code": None,
        "account": None,
        "mpan_core": None,
        "reference": None,
        "issue_date": None,
        "start_date": None,
        "finish_date": None,
        "kwh": Decimal("0"),
        "net": Decimal("185.11"),
        "vat": Decimal("84.80"),
        "gross": Decimal("806.12"),
        "breakdown": defaultdict(
            int,
            {
                "raw-lines": [
                    "MHD=2+UTLBIL:3'",
                    "BTL=+18511+8480++80612'",
                    "MTR=6'",
                ]
            },
        ),
        "elements": [],
        "reads": [],
    }
    assert bills == [expected_bill]


def test_parser_REF(mocker, sess):
    file_lines = [
        "REF='",
    ]
    f = BytesIO(b"\n".join(n.encode("utf8") for n in file_lines))
    parser = Parser(f)
    parser.make_raw_bills()


def test_process_CCD2(mocker, sess):
    headers = {
        "reads": [],
        "breakdown": defaultdict(int),
        "kwh": Decimal(0),
        "elements": [],
    }
    elements = {
        "TMOD": ["0001"],
        "MTNR": ["x"],
        "MLOC": ["228477911812004111222"],
        "PRDT": ["201001"],
        "PVDT": ["200901"],
        "PRRD": ["10", "00", "0", "00"],
        "ADJF": ["", "0"],
        "CONA": ["0", "KWH"],
        "NUCT": ["0"],
        "CSDT": ["200701"],
        "CEDT": ["200901"],
        "CPPU": ["0"],
        "CTOT": ["0"],
    }
    _process_CCD2(elements, headers)
    expected_headers = {
        "reads": [
            {
                "msn": "x",
                "mpan": "04 111 222 22 8477 9118 120",
                "coefficient": Decimal("0"),
                "units": "kWh",
                "tpr_code": "00001",
                "prev_date": utc_datetime(2020, 9, 1, 22, 30),
                "prev_value": Decimal("0"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2020, 10, 1, 22, 30),
                "pres_value": Decimal("10"),
                "pres_type_code": "N",
            }
        ],
        "elements": [
            {
                "name": "00001",
                "net": Decimal("0"),
                "start_date": to_utc(ct_datetime(2020, 7, 1)),
                "finish_date": to_utc(ct_datetime(2020, 9, 1, 23, 30)),
                "breakdown": {
                    "kwh": Decimal("0"),
                    "rate": {Decimal("0")},
                },
            }
        ],
        "kwh": Decimal("0"),
        "breakdown": {},
    }
    assert headers == expected_headers


def test_process_CCD3(mocker, sess):
    headers = {"reads": [], "elements": []}
    elements = {
        "TMOD": ["0001", "CQ1UUP", "", "O"],
        "NUCT": ["8760000", "1"],
        "CPPU": ["086380"],
        "CTOT": ["37150"],
        "CSDT": ["151022"],
        "CEDT": ["171123"],
    }
    _process_CCD3(elements, headers)
    expected_headers = {
        "reads": [],
        "elements": [
            {
                "breakdown": {
                    "kwh": Decimal("8760"),
                    "rate": {
                        Decimal("0.8638"),
                    },
                },
                "finish_date": to_utc(ct_datetime(2017, 11, 23, 23, 30)),
                "name": "00001",
                "net": Decimal("371.50"),
                "start_date": to_utc(ct_datetime(2015, 10, 22)),
            }
        ],
    }
    assert headers == expected_headers
    assert headers["elements"][0]["net"].as_tuple().exponent == -2


def test_process_CCD4(mocker, sess):
    headers = {"reads": [], "elements": []}
    elements = {
        "NDRP": ["241"],
        "TMOD": ["0001", "CQ1UUP", "", "O"],
        "NUCT": ["8760000", "1"],
        "CPPU": ["086380"],
        "CTOT": ["37150"],
        "CSDT": ["151022"],
        "CEDT": ["171123"],
    }
    _process_CCD4(elements, headers)
    expected_headers = {
        "reads": [],
        "elements": [
            {
                "breakdown": {
                    "days": Decimal("241"),
                },
                "finish_date": to_utc(ct_datetime(2017, 11, 23, 23, 30)),
                "name": "standing",
                "net": Decimal("371.50"),
                "start_date": to_utc(ct_datetime(2015, 10, 22)),
            }
        ],
    }
    assert headers == expected_headers
    assert headers["elements"][0]["net"].as_tuple().exponent == -2


def test_process_BTL(mocker, sess):
    issue_date = to_utc(ct_datetime(2020, 10, 1))
    start_date = to_utc(ct_datetime(2020, 9, 1))
    finish_date = to_utc(ct_datetime(2020, 9, 30, 23, 30))
    bill_type_code = "N"
    mpan_core = "22 8477 9118 129"
    account = "AC2"
    reference = "h98ge4kl"
    kwh = Decimal("23")
    net = "45.00"
    vat = "5.20"
    gross = "27.60"
    breakdown = {"raw-lines": []}

    headers = {
        "is_ebatch": True,
        "reads": [{"pres_type_code": "C"}],
        "message_type": "UTLBIL",
        "mpan_core": mpan_core,
        "bill_type_code": bill_type_code,
        "account": account,
        "reference": reference,
        "issue_date": issue_date,
        "start_date": start_date,
        "finish_date": finish_date,
        "breakdown": breakdown,
        "kwh": kwh,
        "elements": [],
    }
    elements = {"UVLT": ["4500"], "UTVA": ["520"], "TBTL": ["2760"]}
    bill = _process_BTL(elements, headers)
    expected_bill = {
        "bill_type_code": bill_type_code,
        "account": account,
        "mpan_core": mpan_core,
        "reference": reference,
        "issue_date": issue_date,
        "start_date": start_date,
        "finish_date": finish_date,
        "kwh": kwh,
        "net": Decimal(net),
        "vat": Decimal(vat),
        "gross": Decimal(gross),
        "breakdown": breakdown,
        "reads": [{"pres_type_code": "E"}],
        "elements": [],
    }
    assert bill == expected_bill
    assert bill["net"].as_tuple().exponent == -2
    assert bill["vat"].as_tuple().exponent == -2
    assert bill["gross"].as_tuple().exponent == -2


def test_process_MTR(mocker, sess):
    headers = {}
    elements = {}
    bill = _process_MTR(elements, headers)
    assert bill is None
