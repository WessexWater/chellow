from decimal import Decimal

from openpyxl import Workbook

from chellow.e.hh_parser_vital_xlsx import find_hhs

from chellow.utils import utc_datetime


def test_find_hhs():
    wb = Workbook()
    sheet = wb.worksheets[0]

    for row, (ts, imp, exp) in enumerate(
        (
            ("15/09/2024 21:30:00", 508, 22),
            ("15/09/2024 21:15:00", 500, 20),
            ("15/09/2024 21:00:00", 497, 20),
            ("15/09/2024 20:45:00", 490, 17),
            ("15/09/2024 20:30:01", 481, 15),
            ("15/09/2024 20:30:00", 475, 10),
        ),
        start=2,
    ):
        sheet[f"A{row}"] = ts
        sheet[f"H{row}"] = Decimal(imp)
        sheet[f"I{row}"] = Decimal(exp)

    hhs = list(find_hhs(sheet, "99 0000 0000 000", "99 0000 0000 010"))
    expected_hhs = [
        {
            "channel_type": "ACTIVE",
            "mpan_core": "99 0000 0000 000",
            "start_date": utc_datetime(2024, 9, 15, 20, 0),
            "status": "A",
            "value": Decimal("11"),
        },
        {
            "channel_type": "ACTIVE",
            "mpan_core": "99 0000 0000 010",
            "start_date": utc_datetime(2024, 9, 15, 20, 0),
            "status": "A",
            "value": Decimal("2"),
        },
        {
            "channel_type": "ACTIVE",
            "mpan_core": "99 0000 0000 000",
            "start_date": utc_datetime(2024, 9, 15, 19, 30),
            "status": "A",
            "value": Decimal("16"),
        },
        {
            "channel_type": "ACTIVE",
            "mpan_core": "99 0000 0000 010",
            "start_date": utc_datetime(2024, 9, 15, 19, 30),
            "status": "A",
            "value": Decimal("5"),
        },
    ]

    assert hhs == expected_hhs
