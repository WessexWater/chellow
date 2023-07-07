from datetime import datetime as Datetime
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook

from chellow.e.bill_parsers.nonsettlement_dc_stark_xlsx import Parser
from chellow.utils import utc_datetime


def test(sess):
    with open(
        "test/e/bill_parsers/test_bill_parser_nonsettlement_dc_stark_xlsx/"
        "bills.nonsettlement.dc.stark.xlsx",
        mode="rb",
    ) as f:
        parser = Parser(f)
        parser.make_raw_bills()


def test_old(sess):
    with open(
        "test/e/bill_parsers/test_bill_parser_nonsettlement_dc_stark_xlsx/"
        "bills_old.nonsettlement.dc.stark.xlsx",
        mode="rb",
    ) as f:
        parser = Parser(f)
        parser.make_raw_bills()


def test_one_bill(sess):
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

    sheet["A2"] = "Quantum Computer"
    sheet["B2"] = 65837766
    sheet["C2"] = "x600"
    sheet["D2"] = 7493477439
    sheet["E2"] = 7864739737
    sheet["F2"] = 2088757371777
    sheet["G2"] = Datetime(2022, 2, 1)
    sheet["H2"] = Datetime(2022, 2, 28)
    sheet["I2"] = "Billed"

    sheet["C6"].value = Datetime(2022, 3, 1)

    sheet["B12"].value = "2227651294270"
    sheet["C12"].value = "CS"
    sheet["D12"].value = "Settled"
    sheet["E12"].value = "Massive Field, Taunton, Somerset"
    sheet["F12"].value = Datetime(2022, 1, 1)
    sheet["G12"].value = Datetime(2022, 1, 31)
    sheet["H12"].value = "5.00"
    sheet["I12"].value = "0.12"
    sheet["J12"].value = "0.76"
    sheet["K12"].value = "0.99"

    wb.save(f)
    f.seek(0)
    p = Parser(f)
    result = p.make_raw_bills()

    expected = [
        {
            "bill_type_code": "N",
            "kwh": Decimal("0"),
            "vat": Decimal("1.00"),
            "net": Decimal("5.00"),
            "gross": Decimal("6.00"),
            "reads": [],
            "breakdown": {
                "raw_lines": [],
                "cop": ["5"],
                "settlement-status": ["non_settlement"],
                "msn": ["7864739737"],
                "meter-rate": [Decimal("60.00")],
                "meter-gbp": Decimal("5.00"),
            },
            "account": "20 8875 7371 777",
            "issue_date": utc_datetime(2022, 2, 1),
            "start_date": utc_datetime(2022, 2, 1),
            "finish_date": utc_datetime(2022, 2, 28, 23, 30),
            "mpan_core": "20 8875 7371 777",
            "reference": "20220201_20220228_20220201_20 8875 7371 777",
        }
    ]

    assert result == expected
