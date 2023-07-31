from decimal import Decimal
from io import BytesIO

from werkzeug.exceptions import BadRequest

from chellow.e.bill_parsers.haven_edi import (
    BillElement,
    Parser,
    _process_BTL,
    _process_CCD1,
    _process_CCD3,
    _process_CLO,
    _process_MAN,
    _process_MHD,
    _process_MTR,
    _process_segment,
)
from chellow.utils import utc_datetime


def test_process_BTL_zeroes(mocker):
    elements = {
        "UVLT": ["0"],
        "UTVA": ["0"],
        "TBTL": ["0"],
    }
    headers = {}
    _process_BTL(elements, headers)
    expected_headers = {
        "net": Decimal("0.00"),
        "vat": Decimal("0.00"),
        "gross": Decimal("0.00"),
    }
    assert headers == expected_headers
    assert str(headers["net"]) == "0.00"


def test_process_BTL_non_zeroes(mocker):
    elements = {
        "UVLT": ["11"],
        "UTVA": ["12"],
        "TBTL": ["10"],
    }
    headers = {}
    _process_BTL(elements, headers)
    expected_headers = {
        "net": Decimal("0.11"),
        "vat": Decimal("0.12"),
        "gross": Decimal("0.10"),
    }
    assert headers == expected_headers


def test_process_MTR_UTLHDR(mocker):
    elements = {}
    headers = {"message_type": "UTLHDR", "breakdown": {}}
    bill = _process_MTR(elements, headers)
    assert bill is None


def test_process_MTR_UTLBIL(mocker):
    MockSupply = mocker.patch("chellow.e.bill_parsers.haven_edi.Supply", autospec=True)
    mock_supply = mocker.Mock()
    MockSupply.get_by_mpan_core.return_value = mock_supply
    mock_era = mocker.Mock()
    mock_era.ssc.code = "0244"
    gbp = "10.31"
    cons = "113"
    mock_supply.find_era_at.return_value = mock_era
    elements = {}
    sess = mocker.Mock()
    headers = {
        "sess": sess,
        "message_type": "UTLBIL",
        "breakdown": {},
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            )
        ],
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
                "tpr_code": "Day",
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
        "sess": sess,
        "message_type": "UTLBIL",
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            )
        ],
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
    MockSupply = mocker.patch("chellow.e.bill_parsers.haven_edi.Supply", autospec=True)
    mock_supply = mocker.Mock()
    MockSupply.get_by_mpan_core.return_value = mock_supply
    mock_era = mocker.Mock()
    mock_era.ssc.code = "0244"
    gbp = "10.31"
    cons = "113"
    mock_supply.find_era_at.return_value = mock_era
    elements = {}
    sess = mocker.Mock()
    headers = {
        "sess": sess,
        "message_type": "UTLBIL",
        "breakdown": {},
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            ),
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            ),
        ],
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
                "tpr_code": "Day",
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
        "sess": sess,
        "message_type": "UTLBIL",
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            ),
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Night",
            ),
        ],
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
            "00206-gbp": Decimal(gbp) * 2,
            "00206-rate": {Decimal("0.0001")},
            "00206-kwh": Decimal(cons) * 2,
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


def test_process_MTR_UTLBIL_unmetered(mocker):
    MockSupply = mocker.patch("chellow.e.bill_parsers.haven_edi.Supply", autospec=True)
    mock_supply = mocker.Mock()
    MockSupply.get_by_mpan_core.return_value = mock_supply
    mock_era = mocker.Mock()
    mock_era.ssc.code = "0428"
    mock_mr_00258 = mocker.Mock()
    mock_mr_00258.tpr.code = "00258"
    mock_mr_00259 = mocker.Mock()
    mock_mr_00259.tpr.code = "00259"
    mock_era.ssc.measurement_requirements = [mock_mr_00258, mock_mr_00259]
    gbp = "10.31"
    cons = "113"
    mock_supply.find_era_at.return_value = mock_era
    elements = {}
    sess = mocker.Mock()
    headers = {
        "sess": sess,
        "message_type": "UTLBIL",
        "breakdown": {},
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Energy Charges",
            )
        ],
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
        "sess": sess,
        "message_type": "UTLBIL",
        "bill_elements": [
            BillElement(
                gbp=Decimal(gbp),
                rate=Decimal("0.0001"),
                cons=Decimal(cons),
                titles=None,
                desc="Energy Charges",
            )
        ],
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
            "00258-gbp": Decimal(gbp) / 2,
            "00258-rate": {Decimal("0.0001")},
            "00258-kwh": Decimal(cons) / 2,
            "00259-gbp": Decimal(gbp) / 2,
            "00259-rate": {Decimal("0.0001")},
            "00259-kwh": Decimal(cons) / 2,
        },
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
        "breakdown": {"raw-lines": []},
        "sess": sess,
        "kwh": Decimal("0"),
    }
    assert headers == expected_headers
    assert type(headers["breakdown"]) is type(expected_headers)


def test_process_CCD3(mocker):
    elements = {
        "CCDE": ["3", "", "NRG"],
        "TCOD": ["NIGHT", "Night"],
        "TMOD": ["453043"],
        "CONS": [[]],
        "BPRI": ["10"],
    }

    headers = {
        "bill_elements": [],
        "kwh": Decimal("0"),
    }

    _process_CCD3(elements, headers)

    expected_headers = {
        "kwh": Decimal("0"),
        "bill_elements": [
            BillElement(
                gbp=Decimal("0.00"),
                rate=Decimal("0.0001"),
                cons=Decimal("0"),
                titles=None,
                desc="Night",
            )
        ],
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
        "MLOC": [""],
        "PRRD": ["0", "00", "1", "00"],
        "ADJF": ["", "1"],
    }

    headers = {
        "reads": [],
    }

    _process_CCD1(elements, headers)

    expected_headers = {
        "reads": [
            {
                "msn": msn,
                "mpan": "      ",
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
        ]
    }
    assert headers == expected_headers


def test_process_CLO(mocker):
    account = "accnt"

    elements = {"CLOC": [account, ""]}

    headers = {}

    _process_CLO(elements, headers)

    expected_headers = {
        "account": "",
    }
    assert headers == expected_headers


def test_process_segment_error(mocker):
    mocker.patch(
        "chellow.e.bill_parsers.haven_edi._process_MTR", side_effect=BadRequest()
    )

    code = "MTR"
    elements = []
    line = ""
    account = "a1"
    bill_type_code = "N"
    breakdown = {"raw-lines": []}
    finish_date = utc_datetime(2020, 3, 31, 23, 30)
    gross = 1
    kwh = 1
    issue_date = utc_datetime(2020, 4, 30, 23, 30)
    net = 1
    reads = []
    reference = "20848747847"
    start_date = utc_datetime(2020, 3, 1)
    vat = 1
    headers = {
        "message_type": "UTLBIL",
        "errors": [],
        "type_code": "N",
        "reads": reads,
        "bill_type_code": "N",
        "breakdown": breakdown,
        "gross": gross,
        "vat": vat,
        "net": net,
        "kwh": kwh,
        "issue_date": issue_date,
        "finish_date": finish_date,
        "start_date": start_date,
        "account": account,
        "reference": reference,
    }
    line_number = 13

    bill = _process_segment(code, elements, line, headers, line_number)

    expected_bill = {
        "bill_type_code": bill_type_code,
        "account": account,
        "error": "Can't parse the line number 13 : The browser (or proxy) sent a "
        "request that this server could not understand. The key mpan_core is missing "
        "from the headers at line number 13.",
        "breakdown": breakdown,
        "finish_date": finish_date,
        "issue_date": issue_date,
        "gross": gross,
        "kwh": kwh,
        "net": net,
        "reads": reads,
        "reference": reference,
        "start_date": start_date,
        "vat": vat,
    }

    assert bill == expected_bill


def test_Parser(mocker, sess):
    file_lines = [
        "MHD=2+UTLBIL:3'",
        "MTR=6'",
    ]
    f = BytesIO(b"\n".join(n.encode("utf8") for n in file_lines))
    parser = Parser(f)
    parser.make_raw_bills()
