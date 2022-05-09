from decimal import Decimal
from io import BytesIO

from chellow.bill_parser_sse_edi import Parser, _process_MTR
from chellow.utils import ct_datetime, to_utc


def test_missing_mpan_core(mocker, sess):
    file_lines = [
        "MHD=2+UTLBIL:3'",
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
        "net": Decimal("0.00"),
        "vat": Decimal("0.00"),
        "gross": Decimal("0.00"),
        "breakdown": {"raw-lines": ["MHD=2+UTLBIL:3'", "MTR=6'"]},
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


def test_process_MTR_ebatch(mocker, sess):
    issue_date = to_utc(ct_datetime(2020, 10, 1))
    start_date = to_utc(ct_datetime(2020, 9, 1))
    finish_date = to_utc(ct_datetime(2020, 9, 30, 23, 30))
    bill_type_code = "N"
    mpan_core = "22 8477 9118 129"
    account = "AC2"
    reference = "h98ge4kl"
    kwh = Decimal(23)
    net = Decimal("45.02")
    vat = Decimal("5.27")
    gross = Decimal("27.64")
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
        "kwh": kwh,
        "net": net,
        "vat": vat,
        "gross": gross,
        "breakdown": breakdown,
    }
    elements = {}
    bill = _process_MTR(elements, headers)
    expected_bill = {
        "bill_type_code": bill_type_code,
        "account": account,
        "mpan_core": mpan_core,
        "reference": reference,
        "issue_date": issue_date,
        "start_date": start_date,
        "finish_date": finish_date,
        "kwh": kwh,
        "net": net,
        "vat": vat,
        "gross": gross,
        "breakdown": breakdown,
        "reads": [{"pres_type_code": "E"}],
    }
    assert bill == expected_bill
