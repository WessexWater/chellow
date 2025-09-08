import csv
from decimal import Decimal

from io import BytesIO, TextIOWrapper

from chellow.e.bill_parsers.csv import Parser, _process_row
from chellow.utils import ct_datetime, to_utc


def test_process_row():
    vals = [
        "N",
        "SA342376000",
        "22 1065 3921 534",
        "3423760004",
        "2010-02-02 00:00",
        "2010-01-05 00:00",
        "2010-01-10 23:30",
        "150",
        "98.174",  # Check rounded to two dp
        "15.01",
        "0",
        "",
        "read",
        "I02D89150",
        "22 1065 3921 534",
        "1",
        "kWh",
        "1",
        "2010-01-04 23:30",
        "14281",
        "E",
        "2010-01-06 23:30",
        "15924",
        "N",
        "element",
        "nrg",
        "2010-01-06 00:00",
        "2010-01-11 23:30",
        "5.123",
        "{}",
    ]
    actual = _process_row(vals)
    expected = {
        "account": "SA342376000",
        "bill_type_code": "N",
        "breakdown": {},
        "elements": [
            {
                "breakdown": {},
                "finish_date": to_utc(ct_datetime(2010, 1, 11, 23, 30)),
                "name": "nrg",
                "net": Decimal("5.12"),
                "start_date": to_utc(ct_datetime(2010, 1, 6, 0, 0)),
            },
        ],
        "finish_date": to_utc(ct_datetime(2010, 1, 10, 23, 30)),
        "gross": Decimal("0.00"),
        "issue_date": to_utc(ct_datetime(2010, 2, 2, 0, 0)),
        "kwh": Decimal("150"),
        "mpan_core": "22 1065 3921 534",
        "net": Decimal("98.17"),
        "reads": [
            {
                "coefficient": Decimal("1"),
                "mpan": "22 1065 3921 534",
                "msn": "I02D89150",
                "pres_date": to_utc(ct_datetime(2010, 1, 6, 23, 30)),
                "pres_type_code": "N",
                "pres_value": Decimal("15924"),
                "prev_date": to_utc(ct_datetime(2010, 1, 4, 23, 30)),
                "prev_type_code": "E",
                "prev_value": Decimal("14281"),
                "tpr_code": "00001",
                "units": "kWh",
            },
        ],
        "reference": "3423760004",
        "start_date": to_utc(ct_datetime(2010, 1, 5, 0, 0)),
        "vat": Decimal("15.01"),
    }
    assert actual == expected


def test_bill_parser_csv():
    """
    Check bills have a UTC timezone
    """

    vals = [
        [
            "#InvoiceType",
            "Account Reference",
            "Mpans",
            "Invoice Reference",
            "Issue Date",
            "Start Date",
            "Finish Date",
            "kWh",
            "Net",
            "VAT",
            "Gross",
            "Breakdown",
            "Record Type",
            "R1 Meter Serial Number",
            "R1 MPAN",
            "R1 Coefficient",
            "R1 Units",
            "R1 TPR",
            "R1 Previous Read Date",
            "R1 Previous Read Value",
            "R1 Previous Read Type",
            "R1 Present Read Date",
            "R1 Present Read Value",
            "R1 Present Read Type",
        ],
        [
            "N",
            "SA342376000",
            "22 1065 3921 534",
            "3423760004",
            "2010-02-02 00:00",
            "2010-01-05 00:00",
            "2010-01-10 23:30",
            "150",
            "98.17",
            "15.01",
            "0",
            "",
            "read",
            "I02D89150",
            "22 1065 3921 534",
            "1",
            "kWh",
            "1",
            "2010-01-04 23:30",
            "14281",
            "E",
            "2010-01-06 23:30",
            "15924",
            "N",
        ],
        [
            "N",
            "SA342376000",
            "22 1065 3921 534",
            "3423760005",
            "2011-02-02 00:00",
            "2011-01-05 00:00",
            "2011-01-10 23:30",
            "150",
            "98.17",
            "15.01",
            "0",
            "",
            "read",
            "I02D89150",
            "22 1065 3921 534",
            "1",
            "kWh",
            "1",
            "2011-01-04 23:30",
            "24286",
            "E",
            "2011-01-06 23:30",
            "25927",
            "E",
            "read",
            "I02D89150",
            "22 1065 3921 534",
            "1",
            "kWh",
            "1",
            "2011-02-04 23:30",
            "34285",
            "E",
            "2011-02-06 23:30",
            "46883",
            "E",
            "read",
            "I02D89150",
            "22 1065 3921 534",
            "1",
            "kWh",
            "3",
            "2011-02-04 23:30",
            "8553",
            "E",
            "2011-02-06 23:30",
            "8553",
            "E",
        ],
    ]
    with BytesIO() as f:
        writer = csv.writer(TextIOWrapper(f, write_through=True))
        writer.writerows(vals)
        f.seek(0)
        parser = Parser(f)
        for bill in parser.make_raw_bills():
            for read in bill["reads"]:
                for k in ("prev_date", "pres_date"):
                    assert read[k].tzinfo is not None


def test_make_raw_bills_whitespace_comment():
    """
    Check bills have a UTC timezone
    """

    vals = [
        [
            "\ufeff#InvoiceType",  # Check whitespace is ignored
            "Account Reference",
            "Mpans",
            "Invoice Reference",
            "Issue Date",
            "Start Date",
            "Finish Date",
            "kWh",
            "Net",
            "VAT",
            "Gross",
            "Breakdown",
            "Record Type",
            "R1 Meter Serial Number",
            "R1 MPAN",
            "R1 Coefficient",
            "R1 Units",
            "R1 TPR",
            "R1 Previous Read Date",
            "R1 Previous Read Value",
            "R1 Previous Read Type",
            "R1 Present Read Date",
            "R1 Present Read Value",
            "R1 Present Read Type",
        ],
    ]
    with BytesIO() as f:
        writer = csv.writer(TextIOWrapper(f, write_through=True))
        writer.writerows(vals)
        f.seek(0)
        parser = Parser(f)
        for bill in parser.make_raw_bills():
            pass
