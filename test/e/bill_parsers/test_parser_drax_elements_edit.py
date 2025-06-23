from collections import defaultdict
from decimal import Decimal
from io import BytesIO


from chellow.e.bill_parsers.drax_element_edi import (
    Parser,
    _process_CCD1,
    _process_CCD3,
    _process_MAN,
    _process_MHD,
    _process_MTR,
    _process_VAT,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_process_MTR_UTLHDR(mocker):
    elements = {}
    headers = {"message_type": "UTLHDR", "breakdown": {}}
    bill = _process_MTR(elements, headers)
    assert bill is None


def test_process_MTR_UTLBIL(mocker):
    gbp = "10.31"
    cons = "113"
    elements = {}
    headers = {
        "is_ebatch": False,
        "message_type": "UTLBIL",
        "breakdown": {
            "00206-gbp": Decimal("10.31"),
            "00206-kwh": Decimal("113"),
            "00206-rate": {Decimal("0.0001")},
        },
        "mpan_core": ["0850"],
        "kwh": 8,
        "reference": "a",
        "issue_date": "d",
        "account": "acc",
        "start_date": "d",
        "finish_date": "d",
        "net": 0,
        "vat": 0,
        "gross": 0,
        "reads": [
            {
                "msn": "hgkh",
                "mpan": "      ",
                "coefficient": Decimal("0.00001"),
                "units": "kWh",
                "tpr_code": "00040",
                "prev_date": utc_datetime(2020, 3, 31, 22, 30),
                "prev_value": Decimal("1"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2020, 3, 1, 23, 30),
                "pres_value": Decimal("0"),
                "pres_type_code": "N",
            },
        ],
        "bill_type_code": "N",
    }
    expected_headers = {
        "is_ebatch": False,
        "message_type": "UTLBIL",
        "kwh": 8,
        "reference": "a",
        "mpan_core": ["0850"],
        "issue_date": "d",
        "account": "acc",
        "start_date": "d",
        "finish_date": "d",
        "net": 0,
        "vat": 0,
        "gross": 0,
        "breakdown": {
            "00206-gbp": Decimal(gbp),
            "00206-rate": {Decimal("0.0001")},
            "00206-kwh": Decimal(cons),
        },
        "reads": [
            {
                "msn": "hgkh",
                "mpan": "      ",
                "coefficient": Decimal("0.00001"),
                "units": "kWh",
                "tpr_code": "00040",
                "prev_date": utc_datetime(2020, 3, 31, 22, 30),
                "prev_value": Decimal("1"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2020, 3, 1, 23, 30),
                "pres_value": Decimal("0"),
                "pres_type_code": "N",
            }
        ],
        "bill_type_code": "N",
    }
    _process_MTR(elements, headers)
    assert headers == expected_headers


def test_process_MTR_UTLBIL_multiple_charges_one_tpr(mocker):
    elements = {}
    headers = {
        "is_ebatch": False,
        "message_type": "UTLBIL",
        "breakdown": {},
        "mpan_core": ["0850"],
        "kwh": 8,
        "reference": "a",
        "issue_date": "d",
        "account": "acc",
        "start_date": "d",
        "finish_date": "d",
        "net": 0,
        "vat": 0,
        "gross": 0,
        "reads": [
            {
                "msn": "hgkh",
                "mpan": "      ",
                "coefficient": Decimal("0.00001"),
                "units": "kWh",
                "tpr_code": "00040",
                "prev_date": utc_datetime(2020, 3, 31, 22, 30),
                "prev_value": Decimal("1"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2020, 3, 1, 23, 30),
                "pres_value": Decimal("0"),
                "pres_type_code": "N",
            },
        ],
        "bill_type_code": "N",
    }
    expected_headers = {
        "is_ebatch": False,
        "message_type": "UTLBIL",
        "kwh": 8,
        "reference": "a",
        "mpan_core": ["0850"],
        "issue_date": "d",
        "account": "acc",
        "start_date": "d",
        "finish_date": "d",
        "net": 0,
        "vat": 0,
        "gross": 0,
        "breakdown": {},
        "reads": [
            {
                "msn": "hgkh",
                "mpan": "      ",
                "coefficient": Decimal("0.00001"),
                "units": "kWh",
                "tpr_code": "00040",
                "prev_date": utc_datetime(2020, 3, 31, 22, 30),
                "prev_value": Decimal("1"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2020, 3, 1, 23, 30),
                "pres_value": Decimal("0"),
                "pres_type_code": "N",
            }
        ],
        "bill_type_code": "N",
    }
    _process_MTR(elements, headers)
    assert headers == expected_headers


def test_process_MTR_UTLBIL_unmetered(mocker):
    elements = {}
    headers = {
        "is_ebatch": False,
        "message_type": "UTLBIL",
        "breakdown": {},
        "mpan_core": ["0850"],
        "kwh": 8,
        "reference": "a",
        "issue_date": "d",
        "account": "acc",
        "start_date": "d",
        "finish_date": "d",
        "net": 0,
        "vat": 0,
        "gross": 0,
        "reads": [],
        "bill_type_code": "N",
    }
    expected_headers = {
        "is_ebatch": False,
        "message_type": "UTLBIL",
        "kwh": 8,
        "reference": "a",
        "mpan_core": ["0850"],
        "issue_date": "d",
        "account": "acc",
        "start_date": "d",
        "finish_date": "d",
        "net": 0,
        "vat": 0,
        "gross": 0,
        "breakdown": {},
        "reads": [],
        "bill_type_code": "N",
    }
    _process_MTR(elements, headers)
    assert headers == expected_headers


def test_process_MAN(mocker):
    elements = {
        "MADN": ["20", "0000000000", "6", "00", "001", "002"],
    }

    headers = {}
    _process_MAN(elements, headers)
    expected_headers = {"mpan_core": "20 0000 0000 006"}
    assert headers == expected_headers


def test_process_MHD(mocker):
    message_type = "UTLBIL"
    elements = {"TYPE": [message_type]}

    headers = {"customer_number": "xhgurg2"}
    _process_MHD(elements, headers)
    expected_headers = {
        "bills": [],
        "customer_number": "xhgurg2",
    }
    assert headers == expected_headers


def test_process_CCD3(mocker):
    elements = {
        "CCDE": ["3", "", "NRG"],
        "TCOD": ["NIGHT", "Night"],
        "TMOD": ["122568"],
        "CONS": [[]],
        "BPRI": ["10"],
        "CSDT": ["250401"],
        "CEDT": ["250430"],
    }

    headers = {
        "kwh": Decimal("0"),
        "breakdown": {},
        "line": "x",
        "bill_type_code": "N",
        "issue_date": to_utc(ct_datetime(2025, 6, 1)),
        "reference": "kdhgl",
        "bills": [],
    }

    _process_CCD3(elements, headers)

    expected_headers = {
        "bill_finish_date": utc_datetime(2025, 4, 29, 22, 30),
        "bill_start_date": utc_datetime(2025, 3, 31, 23, 0),
        "bill_type_code": "N",
        "bills": [
            {
                "bill_type_code": "N",
                "breakdown": {
                    "nrg-msp-gbp": Decimal("0.00"),
                    "nrg-rate": [Decimal("0.0001")],
                    "raw-lines": ["x"],
                },
                "finish_date": utc_datetime(2025, 4, 29, 22, 30),
                "gross": Decimal("0.00"),
                "issue_date": utc_datetime(2025, 5, 31, 23, 0),
                "kwh": Decimal("0"),
                "net": Decimal("0.00"),
                "reads": [],
                "reference": "kdhgl_nrg-msp",
                "start_date": utc_datetime(2025, 3, 31, 23, 0),
                "vat": Decimal("0.00"),
            }
        ],
        "breakdown": {},
        "element_code": "122568",
        "issue_date": utc_datetime(2025, 5, 31, 23, 0),
        "kwh": Decimal("0"),
        "line": "x",
        "reference": "kdhgl",
    }
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
        "breakdown": defaultdict(int),
        "bill_type_code": "N",
        "mpan_core": "22 7583 4732 592",
        "account": "9476o843",
        "reference": "085673",
        "issue_date": utc_datetime(2025, 5, 31, 23, 0),
        "bill_start_date": utc_datetime(2025, 3, 31, 23, 0),
        "bill_finish_date": utc_datetime(2025, 4, 29, 22, 30),
        "line": "kdshg",
        "bills": [],
    }

    _process_VAT(elements, headers)
    expected_headers = {
        "bill_type_code": "N",
        "reference": "085673",
        "account": "9476o843",
        "mpan_core": "22 7583 4732 592",
        "breakdown": {},
        "bill_start_date": utc_datetime(2025, 3, 31, 23, 0),
        "bill_finish_date": utc_datetime(2025, 4, 29, 22, 30),
        "line": "kdshg",
        "bills": [
            {
                "account": "9476o843",
                "bill_type_code": "N",
                "breakdown": {
                    "raw-lines": ["kdshg"],
                    "vat": {
                        Decimal("20"): {"net": Decimal("6.00"), "vat": Decimal("1.50")}
                    },
                },
                "finish_date": utc_datetime(2025, 4, 29, 22, 30),
                "gross": Decimal("1.50"),
                "issue_date": utc_datetime(2025, 5, 31, 23, 0),
                "kwh": Decimal("0.00"),
                "mpan_core": "22 7583 4732 592",
                "net": Decimal("0.00"),
                "reads": [],
                "reference": "085673_vat",
                "start_date": utc_datetime(2025, 3, 31, 23, 0),
                "vat": Decimal("1.50"),
            }
        ],
        "issue_date": utc_datetime(2025, 5, 31, 23, 0),
        "line": "kdshg",
        "mpan_core": "22 7583 4732 592",
        "reference": "085673",
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
