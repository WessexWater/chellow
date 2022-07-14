from decimal import Decimal

import xlrd.sheet

from chellow.e.bill_parsers.sww_xls import _parse_row
from chellow.utils import utc_datetime


def test_parse_row(mocker):
    row = []
    for val in [
        "2019-04-01",
        "2019-04-30",
        "22 7673 2894 214",
        54,
        7.8,
        74,
        5998,
        6.22,
        52,
        877,
        8.001,
        82.98,
        377,
        0.3,
        52,
        823,
        0.782,
        305,
        672,
        4.62,
        8483,
        6843,
        6.328,
        6984,
        7034,
        6734,
        574,
        956,
        678,
        4567,
        485,
        57,
        76,
        39647,
        6587,
        768,
        34687,
        67,
        5478,
        879654,
        654897,
        54789,
        None,
        None,
        None,
        43895,
        48,
        498,
        3498,
        9384,
        23,
    ]:
        cell = mocker.Mock(spec=xlrd.sheet.Cell)
        cell.value = val
        row.append(cell)

    row_index = 2
    datemode = 0
    titles = [
        "BILL START DATE",
        "BILL END DATE",
        "MPAN",
        "DUOS-AVAIL-AV USE KVADAY",
        "DUOS-AVAIL-AV RATE P/KVADAY",
        "DUOS-AVAIL-AV COST GBP",
        "DUOS-STND-SITE USE DAY",
        "DUOS-STND-SITE RATE P/DAY",
        "DUOS-STND-SITE COST GBP",
        "DUOS-UNIT-AMBER USE KWH",
        "DUOS-UNIT-AMBER RATE P/KWH",
        "DUOS-UNIT-AMBER COST GBP",
        "DUOS-UNIT-GREEN USE KWH",
        "DUOS-UNIT-GREEN RATE P/KWH",
        "DUOS-UNIT-GREEN COST GBP",
        "DUOS-UNIT-RED USE KWH",
        "DUOS-UNIT-RED RATE P/KWH",
        "DUOS-UNIT-RED COST GBP",
        "LVY-AAHEDC-ALL USE KWH",
        "LVY-AAHEDC-ALL RATE P/KWH",
        "LVY-AAHEDC-ALL COST GBP",
        "LVY-BSUOS-ALL USE KWH",
        "LVY-BSUOS-ALL RATE P/KWH",
        "LVY-BSUOS-ALL COST GBP",
        "LVY-CCL-ALL USE KWH",
        "LVY-CCL-ALL RATE P/KWH",
        "LVY-CCL-ALL COST GBP",
        "LVY-CFDOB-ALL USE KWH",
        "LVY-CFDOB-ALL RATE P/KWH",
        "LVY-CFDOB-ALL COST GBP",
        "LVY-CFDOP-ALL USE KWH",
        "LVY-CFDOP-ALL RATE P/KWH",
        "LVY-CFDOP-ALL COST GBP",
        "LVY-FIT-ALL USE KWH",
        "LVY-FIT-ALL RATE P/KWH",
        "LVY-FIT-ALL COST GBP",
        "LVY-RO-ALL USE KWH",
        "LVY-RO-ALL RATE P/KWH",
        "LVY-RO-ALL COST GBP",
        "NRG-UNIT-SUMMER USE KWH",
        "NRG-UNIT-SUMMER RATE P/KWH",
        "NRG-UNIT-SUMMER COST GBP",
        "NRG-UNIT-WINTER USE KWH",
        "NRG-UNIT-WINTER RATE P/KWH",
        "NRG-UNIT-WINTER COST GBP",
        "SYS-ADMIN-ALL USE MO",
        "SYS-ADMIN-ALL RATE GBP/MO",
        "SYS-ADMIN-ALL COST GBP",
        "TUOS-TRIAD-SITE USE DAY",
        "TUOS-TRIAD-SITE RATE GBP/DAY",
        "TUOS-TRIAD-SITE COST GBP",
    ]
    title_row = []
    for title in titles:
        cell = mocker.Mock(spec=xlrd.sheet.Cell)
        cell.value = title
        title_row.append(cell)

    bill = _parse_row(row, row_index, datemode, title_row)

    bill_start_date = utc_datetime(2019, 4, 1)
    assert bill["start_date"] == bill_start_date

    bill_finish_date = utc_datetime(2019, 4, 30, 23, 30)
    assert bill["finish_date"] == bill_finish_date

    assert bill["net"] == Decimal("82805.98")
    assert bill["breakdown"]["aahedc-gbp"] == Decimal("8483")
    assert bill["mpan_core"] == "22 0003 0354 632"
