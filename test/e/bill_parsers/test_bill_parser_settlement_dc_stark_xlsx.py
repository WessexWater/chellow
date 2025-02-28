from datetime import datetime as Datetime
from io import BytesIO

from openpyxl import Workbook

from chellow.e.bill_parsers.settlement_dc_stark_xlsx import Parser


def test(sess):

    f = BytesIO()
    wb = Workbook()
    sheet = wb.worksheets[0]
    data = [
        [""],
        [""],
        [""],
        [""],
        [""],
        ["SSIL Billing Backing Data - Wessex"],
        ["Date: 03/05/2024 09:16:58"],
        [""],
        [""],
        [
            "",
            "",
            "",
            "",
            "",
            "",
            "Unmetered",
            "",
            "",
            "Code 2",
            "",
            "",
            "Code 3",
            "",
            "",
            "Code 5",
            "",
            "",
            "Code 10",
            "",
            "",
            "GSM",
            "",
            "",
            "SavenergyOnline",
            "",
            "",
            "Meter Proving Tests",
            "",
            "",
            "Hand Held Visits (Ad hoc)",
            "",
            "",
            "Hand Held Visits (Regular)",
            "",
            "",
            "Annual Site Visits",
            "",
            "",
            "",
            "",
            "",
            "",
        ],
        [
            "Sage",
            "MPAN",
            "Site",
            "Bill From",
            "Bill To",
            "Contract Reference",
            "Unmetered Quant",
            "Unmetered Rate",
            "Quarterly Unmetered Charge",
            "No. COP 2 Meters",
            "Annual COP 2 DC/DA Rate",
            "Quarterly COP 2 Charge",
            "No. COP 3 Meters",
            "Annual COP 3 DC/DA Rate",
            "Quarterly COP 3 Charge",
            "No. COP 5 Meters",
            "Annual COP 5 DC/DA Rate",
            "Quarterly COP 5 Charge",
            "No. COP 10 Meters",
            "Annual COP 10 DC/DA Rate",
            "Quarterly COP 10 Charge",
            "No. GSM Meters",
            "GSM Annual Rate",
            "Quarterly GSM Charge",
            "No. Meters",
            "Annual SEO Rate",
            "Quarterly SEO Charge",
            "No. Meter Proving Test",
            "Meter Proving Test Rate",
            "Meter Proving Test Charge",
            "No. Hand Held Visits (Adhoc)",
            "Hand Held Visit (Adhoc) Rate",
            "Hand Held Visit (Adhoc) Charge",
            "No. Hand Held Visits (Regular)",
            "Hand Held Visit (Regular) Rate",
            "Hand Held Visit (Regular) Charge",
            "No. Annual Site Visits",
            "Annual Site Visit Rate",
            "Annual Site Visit Charge",
            "Hand Held Visit Dates",
            "Grand Total",
            "VAT @ 20% ",
            "Grand Total",
        ],
        [
            "W006",
            "2200013784589",
            "NORTH PETHERTON STW, PARKERS FIELD, NORTH PETHERTON, BRIDGWATER, SOMERSET",
            Datetime(2024, 4, 1),
            Datetime(2024, 6, 30),
            "GF002",
            "0",
            "0.00",
            "0.00",
            "0",
            "0.00",
            "0.00",
            "0",
            "99.50",
            "0.00",
            "1",
            "114.43",
            "28.61",
            "0",
            "0.00",
            "0.00",
            "0",
            "0.00",
            "0.00",
            "1",
            "0.00",
            "0.00",
            "0",
            "25.00",
            "0.00",
            "0",
            "20.00",
            "0.00",
            "0",
            "0.00",
            "0.00",
            "0",
            "20.00",
            "0.00",
            "",
            "28.61",
            "5.72",
            "34.33",
        ],
        [
            "W006",
            "1470001573345",
            "WICKWAR SEWAGE WORKS, OFF STATION ROAD, WICKWAR, WOTTON-UNDER-EDGE, "
            "GLOUCESTERSHIRE",
            Datetime(2024, 6, 12),
            Datetime(2024, 6, 30),
            "GF002",
            "0",
            "0.00",
            "0.00",
            "0",
            "0.00",
            "0.00",
            "0",
            "99.50",
            "0.00",
            "0.6333",
            "114.43",
            "5.96",
            "0",
            "0.00",
            "0.00",
            "0",
            "0.00",
            "0.00",
            "0.6333",
            "0.00",
            "0.00",
            "0",
            "25.00",
            "0.00",
            "0",
            "20.00",
            "0.00",
            "0",
            "0.00",
            "0.00",
            "0",
            "20.00",
            "0.00",
            "",
            "5.96",
            "1.19",
            "7.15",
        ],
    ]
    for row in data:
        sheet.append(row)
    wb.save(f)
    f.seek(0)
    p = Parser(f)
    p.make_raw_bills()
