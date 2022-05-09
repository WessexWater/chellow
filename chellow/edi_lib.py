from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from werkzeug.exceptions import BadRequest

from chellow.utils import ct_datetime, to_ct, to_utc


class EdiParser:
    def __init__(self, f):
        self.f_iterator = iter(f)
        self.line_number = 0

    def __iter__(self):
        return self

    def __next__(self):
        self.line = next(self.f_iterator).strip()
        self.line_number += 1

        if self.line[-1] != "'":
            raise BadRequest(
                f"The parser expects each line to end with a ', but line number "
                f"{self.line_number} doesn't: {self.line}."
            )
        self.elements = [element.split(":") for element in self.line[4:-1].split("+")]
        return self.line[:3]


def parse_edi(edi_str):
    for line_number, raw_line in enumerate(edi_str.splitlines(), start=1):
        if raw_line[-1] != "'":
            raise BadRequest(
                f"The parser expects each line to end with a ', but line "
                f"number {line_number} doesn't: {raw_line}."
            )

        line = raw_line.strip()
        code = line[:3]

        els = [el.split(":") for el in line[4:-1].split("+")]

        segment_name = code + els[1][0] if code == "CCD" else code

        try:
            elem_data = SEGMENTS[segment_name]
        except KeyError:
            raise BadRequest(
                f"At line number {line_number} the segment name {segment_name} isn't "
                f"recognized."
            )
        elem_codes = [m["code"] for m in elem_data["elements"]]

        elements = dict(zip(elem_codes, els))

        yield line_number, line, segment_name, elements


def to_decimal(components):
    try:
        result = Decimal(components[0])
    except InvalidOperation as e:
        raise BadRequest(f"Problem parsing decimal '{components[0]}' {e}")
    if len(components) > 1 and components[-1] == "R":
        result *= Decimal("-1")
    return result


def to_ct_date(component):
    return to_ct(Datetime.strptime(component, "%y%m%d"))


def to_date(component):
    return to_utc(to_ct_date(component))


def to_finish_date(component):
    d = to_ct_date(component)
    return to_utc(ct_datetime(d.year, d.month, d.day, 23, 30))


def to_int(component):
    return int(component)


SEGMENTS = {
    "ADJ": {
        "description": "ADDITIONAL ADJUSTMENTS",
        "elements": [
            {
                "code": "SEQA",
                "description": "First Level Sequence Number",
                "components": [
                    ("First Level Sequence Number", "X"),
                ],
            },
            {
                "code": "SEQB",
                "description": "Second Level Sequence Number",
                "components": [
                    ("Second Level Sequence Number", "X"),
                ],
            },
            {
                "code": "ADJF",
                "description": "Adjustment Factor",
                "components": [
                    ("Adjustment Factor Code", "X"),
                    ("Adjustment Factor Value", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
        ],
    },
    "BTL": {
        "description": "BILL TRAILER",
        "elements": [
            {
                "code": "PTOT",
                "description": "Total of Payment Details",
                "components": [
                    ("Total of Payment Details", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "UVLT",
                "description": "Total Charge for Premises Before VAT",
                "components": [
                    ("Total Charge Before VAT", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "UTVA",
                "description": "Bill Total VAT Amount Payable",
                "components": [
                    ("Bill Total VAT Amount Payable", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "BABF",
                "description": "Balance Brought Forward",
                "components": [
                    ("Balance Brought Forward", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "TBTL",
                "description": "Total Bill Amount Payable",
                "components": [
                    ("Total Bill Amount Payable", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
        ],
    },
    "DNA": {
        "description": "DATA NARRATIVE",
        "elements": [
            {
                "code": "SEQA",
                "description": "First Level Sequence Number",
                "components": [("First Level Sequence Number", "X")],
            },
            {
                "code": "DNAC",
                "description": "Data Narrative Code",
                "components": [("Code Table Number", "X"), ("Code Value", "X")],
            },
            {
                "code": "RTEX",
                "description": "Registered Text",
                "components": [
                    ("First Line Registered Text Code", "X"),
                    ("Application Text", "X"),
                    ("Second Line Registered Text Code", "X"),
                    ("Application Text", "X"),
                    ("Third Line Registered Text Code", "X"),
                    ("Application Text", "X"),
                    ("Fourth Line Registered Text Code", "X"),
                    ("Application Text", "X"),
                ],
            },
            {
                "code": "GNAR",
                "description": "General Narrative",
                "components": [
                    ("General Narrative Line 1", "X"),
                    ("General Narrative Line 2", "X"),
                    ("General Narrative Line 3", "X"),
                    ("General Narrative Line 4", "X"),
                ],
            },
        ],
    },
    "END": {
        "description": "END OF TRANSMISSION",
        "elements": [
            {
                "code": "NMST",
                "description": "Number of Messages in Transmission",
                "components": [("Number of Messages in Transmission", "X")],
            },
        ],
    },
    "STX": {
        "description": "Start Of Transmission",
        "elements": [
            {
                "code": "STDS",
                "description": "Syntax Rules Identifier",
                "components": [("Identifier", "X"), ("Version", "X")],
            },
            {
                "code": "FROM",
                "description": "Identification of Transmission Sender",
                "components": [("Code", "X"), ("Name", "X")],
            },
            {
                "code": "UNTO",
                "description": "Identification of Transmission Recipient",
                "components": [("Code", "X"), ("Name", "X")],
            },
            {
                "code": "TRDT",
                "description": "Date and Time of Transmission",
                "components": [("Date", "date"), ("Time", "time")],
            },
            {
                "code": "SNRF",
                "description": "Sender's Transmission Reference",
                "components": [("Sender's Transmission Reference", "X")],
            },
            {
                "code": "RCRF",
                "description": "Recipient's Transmission Reference",
                "components": [("Recipient's Transmission Reference", "X")],
            },
            {
                "code": "APRF",
                "description": "Application Reference",
                "components": [("Application Reference", "X")],
            },
            {
                "code": "PRCD",
                "description": "Transmission Priority Code",
                "components": [("Transmission Priority Code", "X")],
            },
        ],
    },
    "MHD": {
        "description": "MESSAGE HEADER",
        "elements": [
            {
                "code": "MSRF",
                "description": "Message Reference",
                "components": [("Message Reference", "X")],
            },
            {
                "code": "TYPE",
                "description": "Type of Message",
                "components": [("Type", "X"), ("Version Number", "X")],
            },
        ],
    },
    "TTL": {
        "description": "UTILITY BILL FILE TOTALS",
        "elements": [
            {
                "code": "FASU",
                "description": "Bill File Total Amount before VAT",
                "components": [
                    ("Bill File Total Amount before VAT", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "UVAT",
                "description": "Bill File Total VAT Amount",
                "components": [
                    ("Bill File Total VAT Amount", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "FTOP",
                "description": "File Total of Payment Details",
                "components": [
                    ("File Total of Payment Details", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "FBAB",
                "description": "File Total Balance Brought Forward",
                "components": [
                    ("File Total Balance Brought Forward", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "FPSU",
                "description": "Bill File Total Payable including VAT",
                "components": [
                    ("Bill File Total Payable including VAT", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "FTNI",
                "description": "File Total Number of Invoices",
                "components": [
                    ("File Total Number of Invoices", "X"),
                ],
            },
        ],
    },
    "TYP": {
        "description": "TRANSACTION TYPE DETAILS",
        "elements": [
            {
                "code": "TCDE",
                "description": "Transaction Code",
                "components": [("Transaction Code", "X")],
            },
            {
                "code": "TTYP",
                "description": "Transaction Type",
                "components": [("Transaction Type", "X")],
            },
        ],
    },
    "SDT": {
        "description": "SUPPLIER DETAILS",
        "elements": [
            {
                "code": "SIDN",
                "description": "Supplier's Identity",
                "components": [
                    ("Supplier's EAN Location Number", "X"),
                    ("Supplier's Identity Allocated by Customer", "X"),
                ],
            },
            {
                "code": "SNAM",
                "description": "Supplier's Name",
                "components": [("Supplier's Name", "X")],
            },
            {
                "code": "SADD",
                "description": "Supplier's Address",
                "components": [
                    ("Supplier's Address Line 1", "X"),
                    ("Supplier's Address Line 2", "X"),
                    ("Supplier's Address Line 3", "X"),
                    ("Supplier's Address Line 4", "X"),
                    ("Supplier's Post Code", "X"),
                ],
            },
            {
                "code": "VATN",
                "description": "Suplier's VAT Registration Number",
                "components": [
                    ("Numeric VAT Registration Number", "X"),
                    ("Alphanumeric VAT Registration Number", "X"),
                ],
            },
        ],
    },
    "CDT": {
        "description": "CUSTOMER DETAILS",
        "elements": [
            {
                "code": "CIDN",
                "description": "Customer's Identity",
                "components": [
                    ("Customer's EAN Location Number", "X"),
                    ("Customer's Identity Allocated by Customer", "X"),
                ],
            },
            {
                "code": "CNAM",
                "description": "Customer's Name",
                "components": [("Customer's Name", "X")],
            },
            {
                "code": "CADD",
                "description": "Customer's Address",
                "components": [
                    ("Customer's Address Line 1", "X"),
                    ("Customer's Address Line 2", "X"),
                    ("Customer's Address Line 3", "X"),
                    ("Customer's Address Line 4", "X"),
                    ("Customer's Post Code", "X"),
                ],
            },
            {
                "code": "VATR",
                "description": "Customer's VAT Registration Number",
                "components": [
                    ("Numeric VAT Registration Number", "X"),
                    ("Alphanumeric VAT Registration Number", "X"),
                ],
            },
        ],
    },
    "CDA": {
        "description": "CONTRACT DATA",
        "elements": [
            {
                "code": "CPSC",
                "description": "Current Price Structure Reference",
                "components": [
                    ("Current Price Structure Reference", "X"),
                ],
            },
            {
                "code": "ORNO",
                "description": "Order Number and Date",
                "components": [
                    ("Customer's Order Number", "X"),
                    ("Supplier's Order Number", "X"),
                    ("Date Order Placed by customer", "date"),
                    ("Date Order Received by Supplier", "date"),
                ],
            },
            {
                "code": "INSD",
                "description": "Installation Date",
                "components": [("Installation Date", "date")],
            },
            {
                "code": "REPE",
                "description": "Rental Period",
                "components": [("Rental Period", "X")],
            },
        ],
    },
    "FIL": {
        "description": "FILE DETAILS",
        "elements": [
            {
                "code": "FLGN",
                "description": "File Generation Number",
                "components": [
                    ("File Generation Number", "X"),
                ],
            },
            {
                "code": "FLVN",
                "description": "File Version Number",
                "components": [("File Version Number", "X")],
            },
            {
                "code": "FLDT",
                "description": "File Creation Date",
                "components": [
                    ("File Creation Date", "X"),
                ],
            },
            {
                "code": "FLID",
                "description": "File (Reel) Identification",
                "components": [
                    ("File (Reel) Identification", "X"),
                ],
            },
        ],
    },
    "FDT": {
        "description": "FILE PERIOD DATES",
        "elements": [
            {
                "code": "IVED",
                "description": "Invoice Period End Date",
                "components": [
                    ("Invoice Period End Date", "X"),
                ],
            },
            {
                "code": "DVED",
                "description": "Delivery Period End Date",
                "components": [("Delivery Period End Date", "X")],
            },
        ],
    },
    "REF": {
        "description": "ACCOUNT REFERENCE NUMBER",
        "elements": [
            {
                "code": "REFF",
                "description": "Account Identifier",
                "components": [
                    ("Supplier's Reference", "X"),
                    ("Customer's Reference", "X"),
                ],
            },
            {
                "code": "SCRF",
                "description": "Specification / Contract References",
                "components": [
                    ("Specification No.", "X"),
                    ("Contract No.", "X"),
                ],
            },
        ],
    },
    "MTR": {
        "description": "MESSAGE TRAILER",
        "elements": [
            {
                "code": "NOSG",
                "description": "Number of Segments in Message",
                "components": [
                    ("Number of Segments in Message", "X"),
                ],
            },
        ],
    },
    "BCD": {
        "description": "BILL CONTROL DATA",
        "elements": [
            {
                "code": "IVDT",
                "description": "Date of Invoice",
                "components": [
                    ("Date of Invoice", "date"),
                ],
            },
            {
                "code": "TXDT",
                "description": "Tax-point Date",
                "components": [
                    ("Tax-point Date", "date"),
                ],
            },
            {
                "code": "INVN",
                "description": "Invoice Number",
                "components": [
                    ("Invoice Number", "X"),
                ],
            },
            {
                "code": "PBID",
                "description": "Previous Bill Date",
                "components": [
                    ("Previous Bill Date", "date"),
                ],
            },
            {
                "code": "BIFR",
                "description": "Bill Frequency Code",
                "components": [
                    ("Bill Frequency Code", "X"),
                ],
            },
            {
                "code": "BTCD",
                "description": "Bill Type Code",
                "components": [
                    ("Bill Type Code", "X"),
                ],
            },
            {
                "code": "VDAA",
                "description": "VAT Declaration for Amended Account",
                "components": [
                    ("VAT Declaration Code", "X"),
                    ("Date of Bil Withdrawn", "date"),
                    ("VAT Total Amount on Bil Withdrawn", "X"),
                    ("Amended Invoice Reference", "X"),
                    ("Premises Reference of Previous Bill", "X"),
                ],
            },
            {
                "code": "SUMO",
                "description": "Supply Period",
                "components": [
                    ("Start Date", "date"),
                    ("End Date", "date"),
                ],
            },
            {
                "code": "CLVM",
                "description": "Calorific Value in Specified Units",
                "components": [
                    ("Calorific Value", "X"),
                    ("Unit of Measure", "X"),
                ],
            },
        ],
    },
    "CCD1": {
        "description": "CONSUMPTION / CHARGE DETAILS: consumption only",
        "elements": [
            {
                "code": "SEQA",
                "description": "First Level Sequence Number",
                "components": [
                    ("First Level Sequence Number", "X"),
                    ("Customer's Own Location Number", "X"),
                    ("Supplier's Identity of Customer's Location", "X"),
                ],
            },
            {
                "code": "CCDE",
                "description": "Charge Type Code",
                "components": [
                    ("Consumption / Charge Indicator", "X"),
                    ("EAN-13 Article Number", "X"),
                    ("Supplier Code", "X"),
                ],
            },
            {
                "code": "TCOD",
                "description": "Tariff Code",
                "components": [
                    ("Tariff Code", "X"),
                    ("Tariff Description", "X"),
                ],
            },
            {
                "code": "TMOD",
                "description": "Tariff Code Modifier",
                "components": [
                    ("Tariff Code Modifier 1", "X"),
                    ("Tariff Code Modifier 2", "X"),
                    ("Tariff Code Modifier 3", "X"),
                    ("Tariff Code Modifier 4", "X"),
                ],
            },
            {
                "code": "MTNR",
                "description": "Meter Number",
                "components": [
                    ("Meter Number", "X"),
                ],
            },
            {
                "code": "MLOC",
                "description": "Meter Location",
                "components": [
                    ("Meter Location", "X"),
                ],
            },
            {
                "code": "PRDT",
                "description": "Present Read Date",
                "components": [
                    ("Present Read Date", "date"),
                ],
            },
            {
                "code": "PVDT",
                "description": "Previous Read Date",
                "components": [
                    ("Present Read Date", "date"),
                ],
            },
            {
                "code": "NDRP",
                "description": "Reading Period",
                "components": [
                    ("Reading Period", "X"),
                ],
            },
            {
                "code": "PRRD",
                "description": "Reading Data",
                "components": [
                    ("Present Reading", "X"),
                    ("Type", "X"),
                    ("Pevious Reading", "X"),
                    ("Type", "X"),
                ],
            },
            {
                "code": "CONS",
                "description": "Consumption (Billing Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CONB",
                "description": "Consumption (Base Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "ADJF",
                "description": "Adjustment Factor",
                "components": [
                    ("Adjustment Factor Code", "X"),
                    ("Adjustment Factor Value", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CONA",
                "description": "Consumption (Adjusted Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "BPRI",
                "description": "Base Price Per Unit",
                "components": [
                    ("Base Price Per Unit", "X"),
                ],
            },
            {
                "code": "NUCT",
                "description": "Number of Units for Charge Type",
                "components": [
                    ("Units Billed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CSDT",
                "description": "Charge Start Date",
                "components": [
                    ("Charge Start Date", "date"),
                ],
            },
            {
                "code": "CEDT",
                "description": "Charge End Date",
                "components": [
                    ("Charge End Date", "date"),
                ],
            },
            {
                "code": "CPPU",
                "description": "Price per Unit",
                "components": [
                    ("Price per Unit", "X"),
                ],
            },
            {
                "code": "CTOT",
                "description": "Total Charge for Charge Type",
                "components": [
                    ("Total Charge for Charge Type", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "TSUP",
                "description": "VAT - Type of Supply",
                "components": [
                    ("VAT - Type of Supply", "X"),
                ],
            },
            {
                "code": "VATC",
                "description": "VAT Rate Category Code",
                "components": [
                    ("VAT Rate Category Code", "X"),
                ],
            },
            {
                "code": "VATP",
                "description": "VAT Rate Percentage",
                "components": [
                    ("VAT Rate Percentage", "X"),
                ],
            },
            {
                "code": "MSAD",
                "description": "Meter Sub-address",
                "components": [
                    ("Sub-address Code", "X"),
                    ("Sub-address Line", "X"),
                ],
            },
        ],
    },
    "CCD2": {
        "description": "CONSUMPTION / CHARGE DETAILS: Consumption and charge only",
        "elements": [
            {
                "code": "SEQA",
                "description": "First Level Sequence Number",
                "components": [
                    ("First Level Sequence Number", "X"),
                    ("Customer's Own Location Number", "X"),
                    ("Supplier's Identity of Customer's Location", "X"),
                ],
            },
            {
                "code": "CCDE",
                "description": "Charge Type Code",
                "components": [
                    ("Consumption / Charge Indicator", "X"),
                    ("EAN-13 Article Number", "X"),
                    ("Supplier Code", "X"),
                ],
            },
            {
                "code": "TCOD",
                "description": "Tariff Code",
                "components": [
                    ("Tariff Code", "X"),
                    ("Tariff Description", "X"),
                ],
            },
            {
                "code": "TMOD",
                "description": "Tariff Code Modifier",
                "components": [
                    ("Tariff Code Modifier 1", "X"),
                    ("Tariff Code Modifier 2", "X"),
                    ("Tariff Code Modifier 3", "X"),
                    ("Tariff Code Modifier 4", "X"),
                ],
            },
            {
                "code": "MTNR",
                "description": "Meter Number",
                "components": [
                    ("Meter Number", "X"),
                ],
            },
            {
                "code": "MLOC",
                "description": "Meter Location",
                "components": [
                    ("Meter Location", "X"),
                ],
            },
            {
                "code": "PRDT",
                "description": "Present Read Date",
                "components": [
                    ("Present Read Date", "date"),
                ],
            },
            {
                "code": "PVDT",
                "description": "Previous Read Date",
                "components": [
                    ("Present Read Date", "date"),
                ],
            },
            {
                "code": "NDRP",
                "description": "Reading Period",
                "components": [
                    ("Reading Period", "X"),
                ],
            },
            {
                "code": "PRRD",
                "description": "Reading Data",
                "components": [
                    ("Present Reading", "X"),
                    ("Type", "X"),
                    ("Pevious Reading", "X"),
                    ("Type", "X"),
                ],
            },
            {
                "code": "CONS",
                "description": "Consumption (Billing Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CONB",
                "description": "Consumption (Base Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "ADJF",
                "description": "Adjustment Factor",
                "components": [
                    ("Adjustment Factor Code", "X"),
                    ("Adjustment Factor Value", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CONA",
                "description": "Consumption (Adjusted Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "BPRI",
                "description": "Base Price Per Unit",
                "components": [
                    ("Base Price Per Unit", "X"),
                ],
            },
            {
                "code": "NUCT",
                "description": "Number of Units for Charge Type",
                "components": [
                    ("Units Billed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CSDT",
                "description": "Charge Start Date",
                "components": [
                    ("Charge Start Date", "date"),
                ],
            },
            {
                "code": "CEDT",
                "description": "Charge End Date",
                "components": [
                    ("Charge End Date", "date"),
                ],
            },
            {
                "code": "CPPU",
                "description": "Price per Unit",
                "components": [
                    ("Price per Unit", "X"),
                ],
            },
            {
                "code": "CTOT",
                "description": "Total Charge for Charge Type",
                "components": [
                    ("Total Charge for Charge Type", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "TSUP",
                "description": "VAT - Type of Supply",
                "components": [
                    ("VAT - Type of Supply", "X"),
                ],
            },
            {
                "code": "VATC",
                "description": "VAT Rate Category Code",
                "components": [
                    ("VAT Rate Category Code", "X"),
                ],
            },
            {
                "code": "VATP",
                "description": "VAT Rate Percentage",
                "components": [
                    ("VAT Rate Percentage", "X"),
                ],
            },
            {
                "code": "MSAD",
                "description": "Meter Sub-address",
                "components": [
                    ("Sub-address Code", "X"),
                    ("Sub-address Line", "X"),
                ],
            },
        ],
    },
    "CCD3": {
        "description": "CONSUMPTION / CHARGE DETAILS: Consumption based charges only",
        "elements": [
            {
                "code": "SEQA",
                "description": "First Level Sequence Number",
                "components": [
                    ("First Level Sequence Number", "X"),
                    ("Customer's Own Location Number", "X"),
                    ("Supplier's Identity of Customer's Location", "X"),
                ],
            },
            {
                "code": "CCDE",
                "description": "Charge Type Code",
                "components": [
                    ("Consumption / Charge Indicator", "X"),
                    ("EAN-13 Article Number", "X"),
                    ("Supplier Code", "X"),
                ],
            },
            {
                "code": "TCOD",
                "description": "Tariff Code",
                "components": [
                    ("Tariff Code", "X"),
                    ("Tariff Description", "X"),
                ],
            },
            {
                "code": "TMOD",
                "description": "Tariff Code Modifier",
                "components": [
                    ("Tariff Code Modifier 1", "X"),
                    ("Tariff Code Modifier 2", "X"),
                    ("Tariff Code Modifier 3", "X"),
                    ("Tariff Code Modifier 4", "X"),
                ],
            },
            {
                "code": "MTNR",
                "description": "Meter Number",
                "components": [
                    ("Meter Number", "X"),
                ],
            },
            {
                "code": "MLOC",
                "description": "Meter Location",
                "components": [
                    ("Meter Location", "X"),
                ],
            },
            {
                "code": "PRDT",
                "description": "Present Read Date",
                "components": [
                    ("Present Read Date", "date"),
                ],
            },
            {
                "code": "PVDT",
                "description": "Previous Read Date",
                "components": [
                    ("Present Read Date", "date"),
                ],
            },
            {
                "code": "NDRP",
                "description": "Reading Period",
                "components": [
                    ("Reading Period", "X"),
                ],
            },
            {
                "code": "PRRD",
                "description": "Reading Data",
                "components": [
                    ("Present Reading", "X"),
                    ("Type", "X"),
                    ("Pevious Reading", "X"),
                    ("Type", "X"),
                ],
            },
            {
                "code": "CONS",
                "description": "Consumption (Billing Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CONB",
                "description": "Consumption (Base Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "ADJF",
                "description": "Adjustment Factor",
                "components": [
                    ("Adjustment Factor Code", "X"),
                    ("Adjustment Factor Value", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CONA",
                "description": "Consumption (Adjusted Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "BPRI",
                "description": "Base Price Per Unit",
                "components": [
                    ("Base Price Per Unit", "X"),
                ],
            },
            {
                "code": "NUCT",
                "description": "Number of Units for Charge Type",
                "components": [
                    ("Units Billed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CSDT",
                "description": "Charge Start Date",
                "components": [
                    ("Charge Start Date", "date"),
                ],
            },
            {
                "code": "CEDT",
                "description": "Charge End Date",
                "components": [
                    ("Charge End Date", "date"),
                ],
            },
            {
                "code": "CPPU",
                "description": "Price per Unit",
                "components": [
                    ("Price per Unit", "X"),
                ],
            },
            {
                "code": "CTOT",
                "description": "Total Charge for Charge Type",
                "components": [
                    ("Total Charge for Charge Type", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "TSUP",
                "description": "VAT - Type of Supply",
                "components": [
                    ("VAT - Type of Supply", "X"),
                ],
            },
            {
                "code": "VATC",
                "description": "VAT Rate Category Code",
                "components": [
                    ("VAT Rate Category Code", "X"),
                ],
            },
            {
                "code": "VATP",
                "description": "VAT Rate Percentage",
                "components": [
                    ("VAT Rate Percentage", "X"),
                ],
            },
            {
                "code": "MSAD",
                "description": "Meter Sub-address",
                "components": [
                    ("Sub-address Code", "X"),
                    ("Sub-address Line", "X"),
                ],
            },
        ],
    },
    "CCD4": {
        "description": "CONSUMPTION / CHARGE DETAILS: Consumption based charges only",
        "elements": [
            {
                "code": "SEQA",
                "description": "First Level Sequence Number",
                "components": [
                    ("First Level Sequence Number", "X"),
                    ("Customer's Own Location Number", "X"),
                    ("Supplier's Identity of Customer's Location", "X"),
                ],
            },
            {
                "code": "CCDE",
                "description": "Charge Type Code",
                "components": [
                    ("Consumption / Charge Indicator", "X"),
                    ("EAN-13 Article Number", "X"),
                    ("Supplier Code", "X"),
                ],
            },
            {
                "code": "TCOD",
                "description": "Tariff Code",
                "components": [
                    ("Tariff Code", "X"),
                    ("Tariff Description", "X"),
                ],
            },
            {
                "code": "TMOD",
                "description": "Tariff Code Modifier",
                "components": [
                    ("Tariff Code Modifier 1", "X"),
                    ("Tariff Code Modifier 2", "X"),
                    ("Tariff Code Modifier 3", "X"),
                    ("Tariff Code Modifier 4", "X"),
                ],
            },
            {
                "code": "MTNR",
                "description": "Meter Number",
                "components": [
                    ("Meter Number", "X"),
                ],
            },
            {
                "code": "MLOC",
                "description": "Meter Location",
                "components": [
                    ("Meter Location", "X"),
                ],
            },
            {
                "code": "PRDT",
                "description": "Present Read Date",
                "components": [
                    ("Present Read Date", "date"),
                ],
            },
            {
                "code": "PVDT",
                "description": "Previous Read Date",
                "components": [
                    ("Present Read Date", "date"),
                ],
            },
            {
                "code": "NDRP",
                "description": "Reading Period",
                "components": [
                    ("Reading Period", "X"),
                ],
            },
            {
                "code": "PRRD",
                "description": "Reading Data",
                "components": [
                    ("Present Reading", "X"),
                    ("Type", "X"),
                    ("Pevious Reading", "X"),
                    ("Type", "X"),
                ],
            },
            {
                "code": "CONS",
                "description": "Consumption (Billing Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CONB",
                "description": "Consumption (Base Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "ADJF",
                "description": "Adjustment Factor",
                "components": [
                    ("Adjustment Factor Code", "X"),
                    ("Adjustment Factor Value", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CONA",
                "description": "Consumption (Adjusted Units)",
                "components": [
                    ("Units Consumed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "BPRI",
                "description": "Base Price Per Unit",
                "components": [
                    ("Base Price Per Unit", "X"),
                ],
            },
            {
                "code": "NUCT",
                "description": "Number of Units for Charge Type",
                "components": [
                    ("Units Billed", "X"),
                    ("Unit of Measure", "X"),
                    ("Negative Indicator", "X"),
                ],
            },
            {
                "code": "CSDT",
                "description": "Charge Start Date",
                "components": [
                    ("Charge Start Date", "date"),
                ],
            },
            {
                "code": "CEDT",
                "description": "Charge End Date",
                "components": [
                    ("Charge End Date", "date"),
                ],
            },
            {
                "code": "CPPU",
                "description": "Price per Unit",
                "components": [
                    ("Price per Unit", "X"),
                ],
            },
            {
                "code": "CTOT",
                "description": "Total Charge for Charge Type",
                "components": [
                    ("Total Charge for Charge Type", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "TSUP",
                "description": "VAT - Type of Supply",
                "components": [
                    ("VAT - Type of Supply", "X"),
                ],
            },
            {
                "code": "VATC",
                "description": "VAT Rate Category Code",
                "components": [
                    ("VAT Rate Category Code", "X"),
                ],
            },
            {
                "code": "VATP",
                "description": "VAT Rate Percentage",
                "components": [
                    ("VAT Rate Percentage", "X"),
                ],
            },
            {
                "code": "MSAD",
                "description": "Meter Sub-address",
                "components": [
                    ("Sub-address Code", "X"),
                    ("Sub-address Line", "X"),
                ],
            },
        ],
    },
    "CLO": {
        "description": "CUSTOMER'S LOCATION",
        "elements": [
            {
                "code": "CLOC",
                "description": "Customer's Location",
                "components": [
                    ("Customer's EAN Location Number", "X"),
                    ("Customer's Own Location Number", "X"),
                    ("Supplier's Identity of Customer's Location", "X"),
                ],
            },
            {
                "code": "CNAM",
                "description": "Customer's Name",
                "components": [
                    ("Customer's Name", "X"),
                ],
            },
            {
                "code": "CADD",
                "description": "Customer's Address",
                "components": [
                    ("Customer's Address Line 1", "X"),
                    ("Customer's Address Line 2", "X"),
                    ("Customer's Address Line 3", "X"),
                    ("Customer's Address Line 4", "X"),
                    ("Customer's Post Code", "X"),
                ],
            },
        ],
    },
    "MAN": {
        "description": "METER ADMINISTRATION NUMBER",
        "elements": [
            {
                "code": "SEQA",
                "description": "First Level Sequence Number",
                "components": [
                    ("First Level Sequence Number", "X"),
                ],
            },
            {
                "code": "SEQB",
                "description": "Second Level Sequence Number",
                "components": [
                    ("Second Level Sequence Number", "X"),
                ],
            },
            {
                "code": "MADN",
                "description": "Distribution Identifier",
                "components": [
                    ("Distribution Identifier", "X"),
                    ("Unique Reference Number", "X"),
                    ("Check Digit", "X"),
                    ("Profile Type (class)", "X"),
                    ("Meter / time switch details", "X"),
                    ("Line Loss factor (LLF)", "X"),
                ],
            },
            {
                "code": "MTNR",
                "description": "Meter Serial Number",
                "components": [
                    ("Meter Serial Number", "X"),
                ],
            },
            {
                "code": "NDIG",
                "description": "Number of Digits",
                "components": [
                    ("Number of Digits", "X"),
                ],
            },
        ],
    },
    "VAT": {
        "description": "VALUE ADDED TAX",
        "elements": [
            {
                "code": "SEQA",
                "description": "First Level Sequence Number",
                "components": [
                    ("First Level Sequence Number", "X"),
                ],
            },
            {
                "code": "NDVT",
                "description": "Number of Days' VAT",
                "components": [
                    ("Number of Days' VAT", "X"),
                ],
            },
            {
                "code": "PNDP",
                "description": "Percentage Qualifying for Lower / Zero VAT Rate",
                "components": [
                    ("Percentage Qualifying for Lower / Zero VAT Rate", "X"),
                ],
            },
            {
                "code": "VATC",
                "description": "VAT Rate Category Code",
                "components": [
                    ("VAT Rate Category Code", "date"),
                ],
            },
            {
                "code": "VATP",
                "description": "VAT Rate Percentage",
                "components": [
                    ("VAT Rate Percentage", "X"),
                ],
            },
            {
                "code": "UVLA",
                "description": "Total Charge for VAT Category Before VAT",
                "components": [
                    ("Total Charge Before VAT", "X"),
                    ("Credit Line Indicator", "X"),
                ],
            },
            {
                "code": "UVTT",
                "description": "VAT Amount Payable",
                "components": [
                    ("Vat Amount Payable", "X"),
                    ("Credit Line Indicator", "X"),
                ],
            },
            {
                "code": "UCSI",
                "description": "Total Charge for VAT Category including VAT",
                "components": [
                    ("Total Charge Including VAT", "X"),
                    ("Credit Line Indicator", "X"),
                ],
            },
            {
                "code": "NRIL",
                "description": "Number of Item Lines",
                "components": [
                    ("Number of Item Lines", "X"),
                ],
            },
            {
                "code": "RFLV",
                "description": "Reason for Lower / Zero VAT Rate",
                "components": [
                    ("Reason for Lower / Zero VAT Rate", "X"),
                ],
            },
        ],
    },
    "VTS": {
        "description": "VAT RATE SUMMARY",
        "elements": [
            {
                "code": "SEQA",
                "description": "First Level Sequence Number",
                "components": [
                    ("First Level Sequence Number", "X"),
                ],
            },
            {
                "code": "VATC",
                "description": "VAT Rate Category Code",
                "components": [
                    ("VAT Rate Category Code", "date"),
                ],
            },
            {
                "code": "VATP",
                "description": "VAT Rate Percentage",
                "components": [
                    ("VAT Rate Percentage", "X"),
                ],
            },
            {
                "code": "USDI",
                "description": "File Total for VAT Category (before VAT)",
                "components": [
                    ("File Total for VAT Category", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "VTVC",
                "description": "File Total VAT for VAT Category",
                "components": [
                    ("File Total VAT for VAT Category", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
            {
                "code": "UPSI",
                "description": "File Total for VAT Category (including VAT)",
                "components": [
                    ("File Total for VAT Category (including VAT)", "X"),
                    ("Credit Indicator", "X"),
                ],
            },
        ],
    },
}
