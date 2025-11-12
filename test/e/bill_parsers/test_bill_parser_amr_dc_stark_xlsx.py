from datetime import datetime as Datetime
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook

from chellow.e.bill_parsers.amr_dc_stark_xlsx import Parser
from chellow.utils import ct_datetime, to_utc


def test_make_bills(mocker, sess):
    f = BytesIO()
    wb = Workbook()
    wb.create_sheet(title="HH", index=1)
    sheet = wb.worksheets[1]
    sheet.insert_rows(0, 12)
    sheet.insert_cols(0, 13)

    sheet["C6"] = Datetime(2025, 10, 30)

    sheet["B11"] = "MPAN"
    sheet["C11"] = "Site Address"
    sheet["D11"] = "Comms"
    sheet["E11"] = "Start Date"
    sheet["F11"] = "Type"
    sheet["G11"] = "Period From"
    sheet["H11"] = "Period To"
    sheet["I11"] = "DC PA"
    sheet["J11"] = "Charge"
    sheet["K11"] = "Est. VAT"
    sheet["L11"] = "Est. Total"

    sheet["B12"] = "2276173918389"
    sheet["C12"] = "Water Works"
    sheet["D12"] = "GPRS"
    sheet["E12"] = ""
    sheet["F12"] = "Settled"
    sheet["G12"] = Datetime(2025, 7, 1)
    sheet["H12"] = Datetime(2025, 9, 30)
    sheet["I12"] = Decimal("16.7")
    sheet["J12"] = Decimal("5.82")
    sheet["K12"] = Decimal("1.57")
    sheet["L12"] = Decimal("8.45")

    wb.save(f)
    f.seek(0)
    p = Parser(f)
    result = p.make_raw_bills()

    expected = [
        {
            "bill_type_code": "N",
            "kwh": Decimal("0"),
            "vat": Decimal("1.57"),
            "net": Decimal("5.82"),
            "gross": Decimal("8.45"),
            "reads": [],
            "breakdown": {
                "raw_lines": [],
                "vat": {
                    20: {
                        "net": Decimal("5.82"),
                        "vat": Decimal("1.57"),
                    },
                },
            },
            "account": "22 7617 3918 389",
            "issue_date": to_utc(ct_datetime(2025, 10, 30)),
            "start_date": to_utc(ct_datetime(2025, 7, 1)),
            "finish_date": to_utc(ct_datetime(2025, 9, 30, 23, 30)),
            "mpan_core": "22 7617 3918 389",
            "reference": "20250701_20250930_20251030_22 7617 3918 389",
            "elements": [
                {
                    "name": "mpan",
                    "start_date": to_utc(ct_datetime(2025, 7, 1)),
                    "finish_date": to_utc(ct_datetime(2025, 9, 30, 23, 30)),
                    "net": Decimal("5.82"),
                    "breakdown": {
                        "rate": {Decimal("16.7")},
                        "days": 92,
                        "settlement-status": {"settlement"},
                        "comm": {"GPRS"},
                    },
                }
            ],
        }
    ]

    assert result == expected
