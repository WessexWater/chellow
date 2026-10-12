from datetime import datetime as Datetime
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook

from chellow.e.bill_parsers.nonsettlement_dc_stark_xlsx import Parser, _process_row
from chellow.utils import ct_datetime, to_utc


def test_process_row(mocker):
    wb = Workbook()
    sheet = wb.worksheets[0]
    sheet.insert_rows(0, 2)
    sheet.insert_cols(0, 9)

    sheet["A1"] = "NAME"
    sheet["B1"] = "NMR"
    sheet["C1"] = "METER TYPE"
    sheet["D1"] = "IDENTIFIER"
    sheet["E1"] = "METER"
    sheet["F1"] = "MPAN REF"
    sheet["G1"] = "START"
    sheet["H1"] = "END"
    sheet["I1"] = "CHECK"
    sheet["J1"] = "RATE"
    sheet["K1"] = "NET TOTAL"
    sheet["L1"] = "VAT @ 20%"
    sheet["M1"] = "GRAND TOTAL"

    sheet["A2"] = "Treglisson"
    sheet["B2"] = "Q997"
    sheet["C2"] = "VIS"
    sheet["D2"] = 101
    sheet["E2"] = "88jiuf ff"
    sheet["F2"] = 1472066139971
    sheet["G2"] = Datetime(2018, 6, 1)
    sheet["H2"] = Datetime(2018, 6, 30)
    sheet["I2"] = "Billed"
    sheet["J2"] = 4.56
    sheet["K2"] = 10.31
    sheet["L2"] = 1.34
    sheet["M2"] = 12.68

    bill = _process_row(sheet[1], sheet[2])
    assert bill == {
        "account": "14 7206 6139 971",
        "bill_type_code": "N",
        "breakdown": {
            "cop": [
                "5",
            ],
            "msn": [
                "88jiuf ff",
            ],
            "raw_lines": [],
            "vat": {
                20: {
                    "net": Decimal("10.31"),
                    "vat": Decimal("1.34"),
                },
            },
        },
        "elements": [
            {
                "breakdown": {
                    "comm": {
                        "IP",
                    },
                    "months": 1,
                    "rate": {
                        Decimal("4.56"),
                    },
                    "settlement-status": {
                        "non_settlement",
                    },
                },
                "finish_date": to_utc(ct_datetime(2018, 6, 30, 23, 30)),
                "name": "meter",
                "net": Decimal("10.31"),
                "start_date": to_utc(ct_datetime(2018, 6, 1, 0, 0)),
            },
        ],
        "finish_date": to_utc(ct_datetime(2018, 6, 30, 23, 30)),
        "gross": Decimal("12.68"),
        "issue_date": to_utc(ct_datetime(2018, 6, 1)),
        "kwh": Decimal("0"),
        "mpan_core": "14 7206 6139 971",
        "net": Decimal("10.31"),
        "reads": [],
        "reference": "20180601_20180630_20180601_14 7206 6139 971",
        "start_date": to_utc(ct_datetime(2018, 6, 1)),
        "vat": Decimal("1.34"),
    }


def test(mocker):
    f = BytesIO()
    wb = Workbook()
    sheet = wb.worksheets[0]
    sheet.insert_rows(0, 2)
    sheet.insert_cols(0, 9)

    sheet["A1"] = "NAME"
    sheet["B1"] = "NMR"
    sheet["C1"] = "METER TYPE"
    sheet["D1"] = "IDENTIFIER"
    sheet["E1"] = "METER"
    sheet["F1"] = "MPAN REF"
    sheet["G1"] = "START"
    sheet["H1"] = "END"
    sheet["I1"] = "CHECK"
    sheet["J1"] = "RATE"
    sheet["K1"] = "NET TOTAL"
    sheet["L1"] = "VAT @ 20%"
    sheet["M1"] = "GRAND TOTAL"

    sheet["A2"] = "Treglisson"
    sheet["B2"] = "Q997"
    sheet["C2"] = "VIS"
    sheet["D2"] = 101
    sheet["E2"] = "88jiuf ff"
    sheet["F2"] = 1472066139971
    sheet["G2"] = Datetime(2018, 6, 1)
    sheet["H2"] = Datetime(2018, 6, 30)
    sheet["I2"] = "Billed"
    sheet["J2"] = 4.56
    sheet["K2"] = 10.31
    sheet["L2"] = 1.34
    sheet["M2"] = 12.68

    wb.save(f)
    f.seek(0)
    parser = Parser(f)
    parser.make_raw_bills()
