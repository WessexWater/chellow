from decimal import Decimal

import xlrd.sheet

from chellow.e.bill_parsers.engie_xls import _make_raw_bills, _parse_row
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_parse_row(mocker):
    row = []
    for val in [
        "Power Comany Ltd.",
        "Bill Paja",
        "556",
        "BILL PAJA",
        "883",
        "1 True Way",
        "672770",
        43555.00,
        43555.00,
        "",
        "2019-03-01 - 2019-03-31",
        "",
        "",
        "",
        "Draft",
        "",
        "Product",
        "Hand Held Read -",
        43555.00,
        43555.00,
        "",
        "2299999999929",
        "",
        "",
        "",
        "785",
        "GBP",
        "INV",
        "",
        "",
    ]:
        cell = mocker.Mock(spec=xlrd.sheet.Cell)
        cell.value = val
        row.append(cell)

    row_index = 2
    datemode = 0
    title_row = ["To Date"]

    bills = {}

    _parse_row(bills, row, row_index, datemode, title_row)
    assert bills == {
        "22 9999 9999 929": {
            "2019-03-01 - 2019-03-31": {
                "account": "22 9999 9999 929",
                "bill_type_code": "N",
                "breakdown": {
                    "raw_lines": [
                        "['To Date']",
                    ],
                },
                "elements": [
                    {
                        "breakdown": {},
                        "finish_date": to_utc(ct_datetime(2019, 3, 31, 23, 30)),
                        "name": "meter-rental",
                        "net": Decimal("785.00"),
                        "start_date": to_utc(ct_datetime(2019, 3, 31)),
                    },
                ],
                "finish_date": to_utc(ct_datetime(2019, 3, 31, 23, 30)),
                "gross": Decimal("785.00"),
                "issue_date": to_utc(ct_datetime(2019, 3, 31, 0, 0)),
                "kwh": Decimal("0"),
                "mpan_core": "22 9999 9999 929",
                "net": Decimal("785.00"),
                "reads": [],
                "reference": "672770_3",
                "start_date": to_utc(ct_datetime(2019, 3, 1)),
                "vat": Decimal("0.00"),
            },
        },
    }


def test_parse_row_usage_units_zero(mocker):
    row = []
    for val in [
        "Power Comany Ltd.",
        "Bill Paja",
        "556",
        "BILL PAJA",
        "883",
        "1 True Way",
        "672770",
        43555.00,
        43555.00,
        "",
        "2019-03-01 - 2019-03-31",
        "",
        "",
        "",
        "Draft",
        "",
        "Product",
        "Hand Held Read -",
        43555.00,
        43555.00,
        "",
        "2299999999929",
        "877",
        0.0,
        "",
        "785",
        "GBP",
        "INV",
        "",
        "",
    ]:
        cell = mocker.Mock(spec=xlrd.sheet.Cell)
        cell.value = val
        row.append(cell)

    row_index = 2
    datemode = 0
    title_row = ["To Date"]

    bills = {}

    _parse_row(bills, row, row_index, datemode, title_row)
    assert bills == {
        "22 9999 9999 929": {
            "2019-03-01 - 2019-03-31": {
                "account": "22 9999 9999 929",
                "bill_type_code": "N",
                "breakdown": {
                    "raw_lines": [
                        "['To Date']",
                    ],
                },
                "elements": [
                    {
                        "breakdown": {"kwh": Decimal("877")},
                        "finish_date": to_utc(ct_datetime(2019, 3, 31, 23, 30)),
                        "name": "meter-rental",
                        "net": Decimal("785.00"),
                        "start_date": to_utc(ct_datetime(2019, 3, 31)),
                    },
                ],
                "finish_date": to_utc(ct_datetime(2019, 3, 31, 23, 30)),
                "gross": Decimal("785.00"),
                "issue_date": to_utc(ct_datetime(2019, 3, 31, 0, 0)),
                "kwh": Decimal("0"),
                "mpan_core": "22 9999 9999 929",
                "net": Decimal("785.00"),
                "reads": [],
                "reference": "672770_3",
                "start_date": to_utc(ct_datetime(2019, 3, 1)),
                "vat": Decimal("0.00"),
            },
        },
    }


def test_bill_parser_engie_xls_billed_kwh(mocker):
    """
    Blank units should still give billed kWh
    """
    row_vals = [
        "Mistral Wind Power Ltd.",
        "Bill Paja",
        "886572998",
        "Bill Paja",
        "869987122",
        "BA1 5TT",
        "99708221",
        42627,
        42694,
        42629,
        "2016-08-01 - 2016-08-31",
        "458699",
        "Standard Deluxe",
        "Beautiful Breeze",
        "Accepted",
        "Pass Thru - UK Electricity Cost Component",
        "Product",
        "Renewables Obligation (RO)",
        42583,
        42613,
        "Commercial UK Energy VAT",
        "2298132107763",
        27997.33,
        "",
        0.0971123676,
        "9224",
        "GBP",
        "INV",
        "Renewables Obligation (RO)",
        "",
    ]
    row = []
    for row_val in row_vals:
        v = mocker.Mock()
        v.value = row_val
        row.append(v)

    datemode = mocker.Mock()
    bills = {}
    _parse_row(bills, row, 1, datemode, [])
    # assert bill["kwh"] == Decimal("27997.33")
    assert bills == {
        "22 9813 2107 763": {
            "2016-08-01 - 2016-08-31": {
                "account": "22 9813 2107 763",
                "bill_type_code": "N",
                "breakdown": {
                    "raw_lines": [
                        "[]",
                    ],
                    "vat": {
                        20: {
                            "net": Decimal("9224.00"),
                            "vat": Decimal("0.00"),
                        },
                    },
                },
                "elements": [
                    {
                        "breakdown": {
                            "kwh": Decimal("27997.33"),
                            "rate": Decimal("0.0971123676"),
                        },
                        "finish_date": to_utc(ct_datetime(2016, 8, 31, 23, 30)),
                        "name": "meter-rental",
                        "net": Decimal("9224.00"),
                        "start_date": to_utc(ct_datetime(2016, 8, 1)),
                    },
                ],
                "finish_date": to_utc(ct_datetime(2016, 8, 31, 23, 30)),
                "gross": Decimal("9224.00"),
                "issue_date": None,
                "kwh": Decimal("27997.33"),
                "mpan_core": "22 9813 2107 763",
                "net": Decimal("9224.00"),
                "reads": [],
                "reference": "99708221_2",
                "start_date": to_utc(ct_datetime(2016, 8, 1)),
                "vat": Decimal("0.00"),
            },
        },
    }


def test_make_raw_bills_vat(mocker):
    row_vals = [
        "Mistral Wind Power Ltd.",
        "Bill Paja",
        "886572998",
        "Bill Paja",
        "869987122",
        "BA1 5TT",
        "99708221",
        42627,
        42694,
        42629,
        "2016-08-01 - 2016-08-31",
        "",
        "",
        "",
        "Accepted",
        "",
        "Sales Tax",
        "Standard VAT@20%",
        "",
        "",
        "",
        "2298132107763",
        "",
        "",
        "",
        "9224",
        "GBP",
        "INV",
        "",
        "",
    ]
    row = []
    for row_val in row_vals:
        v = mocker.Mock()
        v.value = row_val
        row.append(v)

    datemode = mocker.Mock()
    sheet = mocker.Mock()
    sheet.nrows = 2
    sheet.row = mocker.Mock(return_value=row)
    bills = _make_raw_bills(sheet, datemode)
    expected_bills = [
        {
            "bill_type_code": "N",
            "kwh": Decimal("0"),
            "vat": Decimal("9224.00"),
            "net": Decimal("0.00"),
            "reads": [],
            "breakdown": {
                "raw_lines": [str(row)],
                "vat_percentage": Decimal("20"),
                "vat": {
                    Decimal("20"): {
                        "net": Decimal("0.00"),
                        "vat": Decimal("9224.00"),
                    },
                },
                "vat-rate": {
                    Decimal("0.2"),
                },
            },
            "account": "22 9813 2107 763",
            "issue_date": None,
            "start_date": utc_datetime(2016, 7, 31, 23, 0),
            "finish_date": utc_datetime(2016, 8, 31, 22, 30),
            "mpan_core": "22 9813 2107 763",
            "reference": "99708221_2",
            "gross": Decimal("9224.00"),
            "elements": [],
        }
    ]
    assert bills == expected_bills
