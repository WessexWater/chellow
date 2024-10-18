from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta

from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.utils import HH, parse_mpan_core, to_ct, to_utc


def get_cell(sheet, col, row):
    try:
        coordinates = f"{col}{row}"
        return sheet[coordinates]
    except IndexError:
        raise BadRequest(f"Can't find the cell {coordinates} on sheet {sheet}.")


def get_date_ct(sheet, col, row):
    date_str = get_str(sheet, col, row)
    return to_ct(Datetime.strptime(date_str, "%d/%m/%Y"))


def get_str(sheet, col, row):
    return get_cell(sheet, col, row).value.strip()


def get_dec(sheet, col, row):
    cell = get_cell(sheet, col, row)
    try:
        return Decimal(str(cell.value))
    except InvalidOperation as e:
        raise BadRequest(f"Problem parsing the number at {cell.coordinate}. {e}")


def get_int(sheet, col, row):
    return int(get_cell(sheet, col, row).value)


ELEM_LOOKUP = {
    "Admin Fee": {
        "gbp": "admin-gbp",
        "units": None,
        "rate": None,
    },
    "VAT": None,
    "GDUOS Charges": {
        "gbp": "duos-gbp",
        "units": None,
        "rate": None,
    },
    "Power Generation": {
        "gbp": "ssp-gbp",
        "units": "ssp-kwh",
        "rate": "ssp-rate",
    },
}


def _make_raw_bills(book):
    bills = {}
    mpan_lookup = {}
    sheet = book.worksheets[0]
    for row in range(2, len(sheet["A"]) + 1):
        val = get_cell(sheet, "A", row).value
        if val is None or val == "":
            break

        description = get_str(sheet, "T", row)
        desc_parts = [d.strip() for d in description.split("-")]
        if len(desc_parts) > 1:
            start_date_ct = to_ct(Datetime.strptime(desc_parts[1], "%b %y"))
            finish_date_ct = start_date_ct + relativedelta(months=1) - HH
        else:
            start_date_ct = get_date_ct(sheet, "M", row)
            finish_date_ct = get_date_ct(sheet, "N", row) + relativedelta(
                hours=23, minutes=30
            )

        desc_elem = desc_parts[0]
        start_date = to_utc(start_date_ct)
        finish_date = to_utc(finish_date_ct)
        reference = get_str(sheet, "G", row)
        issue_date = to_utc(get_date_ct(sheet, "I", row))

        bill_key = reference, start_date
        try:
            bill = bills[bill_key]
        except KeyError:
            bill = bills[bill_key] = {
                "bill_type_code": "N",
                "kwh": Decimal(0),
                "vat": Decimal("0.00"),
                "net": Decimal("0.00"),
                "gross": Decimal("0.00"),
                "reads": [],
                "breakdown": {},
                "issue_date": issue_date,
                "start_date": start_date,
                "finish_date": finish_date,
                "reference": reference,
            }

        net = round(get_dec(sheet, "V", row), 2)
        vat = round(get_dec(sheet, "W", row), 2)
        gross = round(get_dec(sheet, "X", row), 2)
        bill["net"] += net
        bill["vat"] += vat
        bill["gross"] += gross

        mpan_core_str = get_str(sheet, "E", row)
        if len(mpan_core_str) > 0:
            mpan_lookup[reference] = parse_mpan_core(mpan_core_str)

        mpan_core = mpan_lookup[reference]

        bill["mpan_core"] = mpan_core
        bill["account"] = mpan_core

        titles = ELEM_LOOKUP[desc_elem]
        if titles is None:
            continue

        breakdown = bill["breakdown"]
        breakdown[titles["gbp"]] = net

        units_title = titles["units"]
        rate_title = titles["rate"]
        units = get_dec(sheet, "P", row)
        rate = get_dec(sheet, "U", row) / Decimal(1000)

        if units_title is not None:
            breakdown[units_title] = units
        if rate_title is not None:
            breakdown[rate_title] = [rate]
    return bills.values()


class Parser:
    def __init__(self, f):
        self.book = load_workbook(f, data_only=True)

        self.last_line = None
        self._line_number = None
        self._title_line = None

    @property
    def line_number(self):
        return None if self._line_number is None else self._line_number + 1

    def _set_last_line(self, i, line):
        self._line_number = i
        self.last_line = line
        if i == 0:
            self._title_line = line
        return line

    def make_raw_bills(self):
        row = bills = None
        try:
            bills = _make_raw_bills(self.book)
        except BadRequest as e:
            raise BadRequest(f"Row number: {row} {e.description}")

        return bills
