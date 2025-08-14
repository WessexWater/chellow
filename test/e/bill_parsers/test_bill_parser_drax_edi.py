from collections import defaultdict
from decimal import Decimal
from io import BytesIO


from chellow.e.bill_parsers.drax_edi import (
    Parser,
    _process_BCD,
    _process_BTL,
    _process_CCD1,
    _process_CCD3,
    _process_MAN,
    _process_MHD,
    _process_MTR,
    _process_VAT,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_process_BCD(mocker):
    reference = "lkasdhhgw"
    elements = {
        "IVDT": ["200416"],
        "INVN": [reference],
        "BTCD": ["N"],
        "SUMO": ["200301", "200331"],
    }
    headers = {}
    _process_BCD(elements, headers)
    expected_headers = {
        "bill_type_code": "N",
        "finish_date": to_utc(ct_datetime(2020, 3, 31, 23, 30)),
        "issue_date": to_utc(ct_datetime(2020, 4, 16)),
        "start_date": to_utc(ct_datetime(2020, 3, 1)),
        "reference": reference,
        "elements": [],
    }
    assert headers == expected_headers


def test_process_BTL(mocker):
    elements = {"UVLT": ["7482"], "UTVA": ["7659"], "TBTL": ["8572"]}
    issue_date = to_utc(ct_datetime(2020, 4, 1))
    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 31, 23, 30))
    headers = {
        "mpan_core": "20 0000 0000 006",
        "account": "97y4t934",
        "bill_type_code": "N",
        "reference": "974y4uot",
        "issue_date": issue_date,
        "start_date": start_date,
        "finish_date": finish_date,
        "kwh": Decimal("44.5"),
        "net": Decimal("77932.22"),
        "vat": Decimal("870937.88"),
        "gross": Decimal("986733.22"),
        "breakdown": {"raw-lines": []},
        "reads": [],
        "elements": [],
        "lines": [],
    }
    bill = _process_BTL(elements, headers)
    expected_bill = {
        "account": "97y4t934",
        "bill_type_code": "N",
        "breakdown": {"raw-lines": []},
        "finish_date": finish_date,
        "gross": Decimal("85.72"),
        "issue_date": issue_date,
        "kwh": Decimal("44.5"),
        "mpan_core": "20 0000 0000 006",
        "net": Decimal("74.82"),
        "reads": [],
        "reference": "974y4uot",
        "start_date": start_date,
        "vat": Decimal("76.59"),
        "elements": [],
    }
    assert bill == expected_bill


def test_process_BTL_decimal_places(mocker):
    elements = {"UVLT": ["7480"], "UTVA": ["7650"], "TBTL": ["8570"]}
    issue_date = to_utc(ct_datetime(2020, 4, 1))
    start_date = to_utc(ct_datetime(2020, 1, 1))
    finish_date = to_utc(ct_datetime(2020, 1, 31, 23, 30))
    headers = {
        "mpan_core": "20 0000 0000 006",
        "account": "97y4t934",
        "bill_type_code": "N",
        "reference": "974y4uot",
        "issue_date": issue_date,
        "start_date": start_date,
        "finish_date": finish_date,
        "kwh": Decimal("44.5"),
        "breakdown": {"raw-lines": []},
        "reads": [],
        "elements": [],
        "lines": [],
    }
    bill = _process_BTL(elements, headers)
    expected_net = Decimal("74.80")
    expected_vat = Decimal("76.50")
    expected_gross = Decimal("85.70")
    expected_bill = {
        "account": "97y4t934",
        "bill_type_code": "N",
        "breakdown": {"raw-lines": []},
        "finish_date": finish_date,
        "issue_date": issue_date,
        "kwh": Decimal("44.5"),
        "mpan_core": "20 0000 0000 006",
        "net": expected_net,
        "gross": expected_gross,
        "reads": [],
        "reference": "974y4uot",
        "start_date": start_date,
        "vat": expected_vat,
        "elements": [],
    }
    assert bill == expected_bill
    for actual_val, expected_val in (
        (bill["net"], expected_net),
        (bill["vat"], expected_vat),
        (bill["gross"], expected_gross),
    ):
        assert actual_val.as_tuple().exponent == expected_val.as_tuple().exponent


def test_process_CCD3():
    elements = {
        "CCDE": ["3", "", "NRG"],
        "TCOD": ["HH0002", "Night"],
        "TMOD": ["122568"],
        "CONS": ["", "", ""],
        "BPRI": ["10"],
        "CSDT": ["250401"],
        "CEDT": ["250430"],
    }

    lines = []
    headers = {
        "kwh": Decimal("0"),
        "breakdown": defaultdict(int, {}),
        "lines": lines,
        "elements": [],
    }

    _process_CCD3(elements, headers)

    expected_headers = {
        "kwh": Decimal("0"),
        "breakdown": {},
        "elements": [
            {
                "name": "nrg-msp",
                "net": Decimal("0.00"),
                "breakdown": {
                    "rate": {Decimal("0.0001")},
                },
                "start_date": to_utc(ct_datetime(2025, 4, 1)),
                "finish_date": to_utc(ct_datetime(2025, 4, 30, 23, 30)),
            }
        ],
        "lines": lines,
    }
    assert headers == expected_headers


def test_process_CCD3_multiple_elements(mocker):
    elements = {
        "CCDE": ["3", "", "NRG"],
        "TCOD": ["HH0002", "Night"],
        "TMOD": ["122568"],
        "CONS": ["8739", "KWH", ""],
        "BPRI": ["10"],
        "CSDT": ["250401"],
        "CEDT": ["250430"],
        "CTOT": ["75849", ""],
    }

    lines = []
    headers = {
        "kwh": Decimal("1000"),
        "elements": [
            {
                "name": "nrg-msp",
                "net": Decimal("1000.00"),
                "start_date": to_utc(ct_datetime(2025, 4, 1)),
                "finish_date": to_utc(ct_datetime(2025, 4, 30, 23, 30)),
                "breakdown": {
                    "rate": {Decimal("758.33")},
                    "kwh": Decimal("10000"),
                },
            },
        ],
        "breakdown": defaultdict(int, {}),
        "lines": lines,
    }

    _process_CCD3(elements, headers)

    expected_headers = {
        "breakdown": defaultdict(int, {}),
        "kwh": Decimal("1008.739"),
        "elements": [
            {
                "name": "nrg-msp",
                "net": Decimal("1000.00"),
                "start_date": to_utc(ct_datetime(2025, 4, 1)),
                "finish_date": to_utc(ct_datetime(2025, 4, 30, 23, 30)),
                "breakdown": {
                    "rate": {Decimal("758.33")},
                    "kwh": Decimal("10000"),
                },
            },
            {
                "name": "nrg-msp",
                "net": Decimal("758.49"),
                "start_date": to_utc(ct_datetime(2025, 4, 1)),
                "finish_date": to_utc(ct_datetime(2025, 4, 30, 23, 30)),
                "breakdown": {
                    "rate": {Decimal("0.0001")},
                    "kwh": Decimal("8.739"),
                },
            },
        ],
        "lines": lines,
    }
    assert headers == expected_headers


def test_process_MHD(mocker):
    message_type = "UTLBIL"
    elements = {"TYPE": [message_type]}

    customer_number = "xhgurg2"
    lines = ["xxx"]
    headers = {"customer_number": customer_number, "lines": lines}
    _process_MHD(elements, headers)
    expected_headers = {
        "customer_number": customer_number,
        "lines": lines,
        "breakdown": {"vat": {}, "raw-lines": lines},
        "kwh": Decimal(0),
        "reads": [],
    }
    assert headers == expected_headers


def test_process_MTR(mocker):
    elements = {}
    headers = {"message_type": "UTLHDR", "breakdown": {}}
    bill = _process_MTR(elements, headers)
    assert bill is None


def test_process_MAN(mocker):
    elements = {
        "MADN": ["20", "0000000000", "6", "00", "001", "002"],
    }

    headers = {}
    _process_MAN(elements, headers)
    expected_headers = {"mpan_core": "20 0000 0000 006"}
    assert headers == expected_headers


def test_process_CCD_1(mocker):
    msn = "hgkh"

    elements = {
        "CCDE": ["1", "", "NRG"],
        "TCOD": ["NIGHT", "Night"],
        "TMOD": ["453043"],
        "MTNR": [msn],
        "CONS": [[]],
        "BPRI": ["10"],
        "PRDT": ["200301"],
        "PVDT": ["200331"],
        "MLOC": ["2275834732592"],
        "PRRD": ["0", "00", "1", "00"],
        "ADJF": ["", "1"],
    }

    headers = {
        "reads": [],
        "mpan_core": "22 7583 4732 592",
    }

    _process_CCD1(elements, headers)

    expected_headers = {
        "mpan_core": "22 7583 4732 592",
        "reads": [
            {
                "msn": msn,
                "mpan": "   22 7583 4732 592",
                "coefficient": Decimal("0.00001"),
                "units": "kWh",
                "tpr_code": "00210",
                "prev_date": utc_datetime(2020, 3, 31, 22, 30),
                "prev_value": Decimal("1"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2020, 3, 1, 23, 30),
                "pres_value": Decimal("0"),
                "pres_type_code": "N",
            }
        ],
    }
    assert headers == expected_headers


def test_process_VAT(mocker):
    elements = {"UVLA": ["600"], "UVTT": ["150"], "UCSI": ["850"], "VATP": ["20000"]}
    headers = {
        "breakdown": defaultdict(int, {"vat": {}}),
    }

    _process_VAT(elements, headers)
    expected_headers = {
        "breakdown": {
            "vat-rate": {Decimal("0.20")},
            "vat": {Decimal("20"): {"net": Decimal("6.00"), "vat": Decimal("1.50")}},
        }
    }

    assert headers == expected_headers


def test_Parser(mocker, sess):
    file_lines = [
        "CDT=ZAPP+ZAPP Industries'",
        "MHD=2+UTLBIL:3'",
        "MTR=6'",
    ]
    f = BytesIO(b"\n".join(n.encode("utf8") for n in file_lines))
    parser = Parser(f)
    parser.make_raw_bills()
