from collections import defaultdict
from decimal import Decimal
from io import BytesIO


from chellow.e.bill_parsers.haven_edi_tprs import (
    Parser,
    _process_CCD1,
    _process_CCD3,
    _process_MAN,
    _process_MHD,
    _process_MTR,
    _process_VAT,
)
from chellow.utils import utc_datetime


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

    sess = mocker.Mock()
    headers = {"sess": sess}
    _process_MHD(elements, headers)
    expected_headers = {
        "message_type": message_type,
        "reads": [],
        "errors": [],
        "bill_elements": [],
        "breakdown": defaultdict(int, {"raw-lines": []}),
        "sess": sess,
        "kwh": Decimal("0"),
        "account": None,
        "start_date": None,
        "finish_date": None,
        "gross": Decimal("0.00"),
        "vat": Decimal("0.00"),
        "net": Decimal("0.00"),
        "reference": None,
        "mpan_core": None,
        "is_ebatch": False,
        "issue_date": None,
        "bill_type_code": None,
    }
    assert headers == expected_headers
    assert isinstance(headers["breakdown"], type(expected_headers["breakdown"]))


def test_process_CCD3(mocker):
    elements = {
        "CCDE": ["3", "", "NRG"],
        "TCOD": ["NIGHT", "Night"],
        "TMOD": ["453043"],
        "CONS": [[]],
        "BPRI": ["10"],
    }

    headers = {"kwh": Decimal("0"), "breakdown": {}}

    _process_CCD3(elements, headers)

    expected_headers = {
        "kwh": Decimal("0"),
        "breakdown": {},
    }
    assert headers == expected_headers


def test_process_CCD3_ebrs_kwh(mocker):
    elements = {
        "CCDE": ["3", "", "NRG"],
        "TCOD": ["R10001", "Day"],
        "TMOD": ["823408"],
        "NUCT": ["4127137"],
    }

    headers = {"kwh": Decimal("0"), "breakdown": defaultdict(int, {})}

    _process_CCD3(elements, headers)

    expected_headers = {
        "kwh": Decimal("0"),
        "breakdown": {
            "ebrs-kwh": Decimal("4127.137"),
        },
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
                "tpr_code": "453043",
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
        "net": Decimal("0.00"),
        "vat": Decimal("0.00"),
        "gross": Decimal("0.00"),
        "breakdown": defaultdict(int),
    }

    _process_VAT(elements, headers)
    expected_headers = {
        "net": Decimal("6.00"),
        "vat": Decimal("1.50"),
        "gross": Decimal("8.50"),
        "breakdown": {
            "vat": {Decimal("20"): {"vat": Decimal("1.50"), "net": Decimal("6.00")}}
        },
    }
    assert headers == expected_headers


def test_Parser(mocker, sess):
    file_lines = [
        "MHD=2+UTLBIL:3'",
        "MTR=6'",
    ]
    f = BytesIO(b"\n".join(n.encode("utf8") for n in file_lines))
    parser = Parser(f)
    parser.make_raw_bills()
