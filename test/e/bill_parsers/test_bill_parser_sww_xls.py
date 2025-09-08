from decimal import Decimal

import xlrd.sheet

from chellow.e.bill_parsers.sww_xls import _parse_row
from chellow.utils import ct_datetime, to_utc


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

    issue_date = to_utc(ct_datetime(2019, 1, 1))

    bill = _parse_row(issue_date, row, row_index, datemode, title_row)
    assert bill == {
        "account": "2007",
        "bill_type_code": "N",
        "breakdown": {},
        "elements": [
            {
                "name": "duos-availability",
                "breakdown": {
                    "kvaday": Decimal("54"),
                    "rate": Decimal("7.8"),
                },
                "net": Decimal("74.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "duos-fixed",
                "breakdown": {
                    "day": Decimal("5998"),
                    "rate": Decimal("6.22"),
                },
                "net": Decimal("52.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "duos-amber",
                "breakdown": {
                    "kwh": Decimal("877"),
                    "rate": Decimal("8.001"),
                },
                "net": Decimal("82.98"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "duos-green",
                "breakdown": {
                    "kwh": Decimal("377"),
                    "rate": Decimal("0.3"),
                },
                "net": Decimal("52.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "duos-red",
                "breakdown": {
                    "kwh": Decimal("823"),
                    "rate": Decimal("0.782"),
                },
                "net": Decimal("305.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "aahedc",
                "breakdown": {
                    "kwh": Decimal("672"),
                    "rate": Decimal("4.62"),
                },
                "net": Decimal("8483.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "bsuos",
                "breakdown": {
                    "kwh": Decimal("6843"),
                    "rate": Decimal("6.328"),
                },
                "net": Decimal("6984.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "ccl",
                "breakdown": {
                    "kwh": Decimal("7034"),
                    "rate": Decimal("6734"),
                },
                "net": Decimal("574.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "cfdob",
                "breakdown": {
                    "kwh": Decimal("956"),
                    "rate": Decimal("678"),
                },
                "net": Decimal("4567.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "cfdop",
                "breakdown": {
                    "kwh": Decimal("485"),
                    "rate": Decimal("57"),
                },
                "net": Decimal("76.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "fit",
                "breakdown": {
                    "kwh": Decimal("39647"),
                    "rate": Decimal("6587"),
                },
                "net": Decimal("768.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "ro",
                "breakdown": {
                    "kwh": Decimal("34687"),
                    "rate": Decimal("67"),
                },
                "net": Decimal("5478.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "summer",
                "breakdown": {
                    "kwh": Decimal("879654"),
                    "rate": Decimal("654897"),
                },
                "net": Decimal("54789.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "admin",
                "breakdown": {
                    "mo": Decimal("43895"),
                    "rate": Decimal("48"),
                },
                "net": Decimal("498.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
            {
                "name": "triad",
                "breakdown": {
                    "day": Decimal("3498"),
                    "rate": Decimal("9384"),
                },
                "net": Decimal("23.00"),
                "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
                "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
            },
        ],
        "finish_date": to_utc(ct_datetime(2019, 4, 30, 23, 30)),
        "gross": Decimal("82805.98"),
        "issue_date": issue_date,
        "kwh": Decimal("672"),
        "mpan_core": "22 0003 0354 632",
        "net": Decimal("82805.98"),
        "reads": [],
        "reference": "20190101T0000_3",
        "start_date": to_utc(ct_datetime(2019, 4, 1, 0, 0)),
        "vat": Decimal("0.00"),
    }
