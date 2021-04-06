from chellow.utils import utc_datetime
import chellow.bill_parser_engie_xls
import xlrd.sheet
import pytest
from werkzeug.exceptions import BadRequest
from decimal import Decimal


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

    bill = chellow.bill_parser_engie_xls._parse_row(row, row_index, datemode, title_row)
    assert bill["finish_date"] == utc_datetime(2019, 3, 31, 22, 30)


def test_bd_add():
    el_name = "duos_red"
    bd = {el_name: 0}
    val = None

    with pytest.raises(BadRequest):
        chellow.bill_parser_engie_xls._bd_add(bd, el_name, val)


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
    bill = chellow.bill_parser_engie_xls._parse_row(row, 1, datemode, [])
    assert bill["kwh"] == Decimal("27997.33")
