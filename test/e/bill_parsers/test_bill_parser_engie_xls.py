from decimal import Decimal

import pytest

from werkzeug.exceptions import BadRequest

import xlrd.sheet

from chellow.e.bill_parsers.engie_xls import _bd_add, _make_raw_bills, _parse_row
from chellow.utils import utc_datetime


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

    bill = _parse_row(row, row_index, datemode, title_row)
    assert bill["finish_date"] == utc_datetime(2019, 3, 31, 22, 30)


def test_bd_add():
    el_name = "duos_red"
    bd = {el_name: 0}
    val = None

    with pytest.raises(BadRequest):
        _bd_add(bd, el_name, val)


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
    bill = _parse_row(row, 1, datemode, [])
    assert bill["kwh"] == Decimal("27997.33")


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
            },
            "account": "22 9813 2107 763",
            "issue_date": None,
            "start_date": utc_datetime(2016, 7, 31, 23, 0),
            "finish_date": utc_datetime(2016, 8, 31, 22, 30),
            "mpan_core": "22 9813 2107 763",
            "reference": "99708221_2",
            "gross": Decimal("9224.00"),
        }
    ]
    assert bills == expected_bills
