from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta

from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.utils import c_months_u, ct_datetime, parse_mpan_core, to_ct, to_utc


def get_cell(sheet, col, row):
    try:
        coordinates = f"{col}{row}"
        return sheet[coordinates]
    except IndexError:
        raise BadRequest(f"Can't find the cell {coordinates} on sheet {sheet}.")


def get_date(sheet, col, row):
    cell = get_cell(sheet, col, row)
    val = cell.value
    if not isinstance(val, Datetime):
        raise BadRequest(
            f"Problem reading {val} (of type {type(val)}) as a timestamp at "
            f"{cell.coordinate}."
        )
    return val


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
    "Capacity": {
        "name": "duos-availability",
        "gbp": "duos-availability-gbp",
        "units": "duos-availability-kva",
        "rate": "duos-availability-rate",
    },
    "Fixed Charge": {
        "name": "duos-fixed",
        "gbp": "duos-fixed-gbp",
        "units": "duos-fixed-days",
        "rate": "duos-fixed-rate",
    },
    "Unit Rate Zero": None,
    "Excess Reactive Power": {
        "name": "duos-reactive",
        "gbp": "duos-reactive-gbp",
        "units": "duos-reactive-kvarh",
        "rate": "duos-reactive-gbp-per-kvarh",
    },
    "Unit Rate Amber": {
        "name": "duos-amber",
        "gbp": "duos-amber-gbp",
        "units": "duos-amber-kwh",
        "rate": "duos-amber-gbp-per-kwh",
    },
    "Unit Rate Green": {
        "name": "duos-green",
        "gbp": "duos-green-gbp",
        "units": "duos-green-kwh",
        "rate": "duos-green-gbp-per-kwh",
    },
    "Unit Rate Red": {
        "name": "duos-red",
        "gbp": "duos-red-gbp",
        "units": "duos-red-kwh",
        "rate": "duos-red-gbp-per-kwh",
    },
    "Unit Rate Super Red": {
        "name": "duos-super-red",
        "gbp": "duos-super-red-gbp",
        "units": "duos-super-red-kwh",
        "rate": "duos-super-red-gbp-per-kwh",
    },
}


def _parse_gduos_sheet(sheet, mpan_core, issue_date):
    bills = []
    for row in range(2, len(sheet["A"]) + 1):
        val = get_cell(sheet, "A", row).value
        if val is None or val == "":
            break

        start_date_str = get_str(sheet, "B", row)
        start_date_ct = to_ct(Datetime.strptime(start_date_str, "%Y-%m"))
        start_date, finish_date = next(
            c_months_u(
                start_year=start_date_ct.year, start_month=start_date_ct.month, months=1
            )
        )

        element_desc = get_str(sheet, "D", row).strip()
        units = get_dec(sheet, "E", row)
        rate = get_dec(sheet, "F", row)
        net = round(get_dec(sheet, "G", row), 2)

        titles = ELEM_LOOKUP[element_desc]
        if titles is None:
            continue

        breakdown = {
            titles["gbp"]: net,
            titles["units"]: units,
            titles["rate"]: [rate],
        }
        bill = {
            "bill_type_code": "N",
            "kwh": Decimal(0),
            "vat": Decimal("0.00"),
            "net": net,
            "gross": net,
            "reads": [],
            "breakdown": breakdown,
            "account": mpan_core,
            "issue_date": issue_date,
            "start_date": start_date,
            "finish_date": finish_date,
            "mpan_core": mpan_core,
            "reference": "_".join(
                (
                    to_ct(start_date).strftime("%Y%m%d"),
                    to_ct(finish_date).strftime("%Y%m%d"),
                    to_ct(issue_date).strftime("%Y%m%d"),
                    mpan_core,
                    titles["name"],
                )
            ),
        }

        bills.append(bill)
    return bills


def _make_raw_bills(book):
    bills = []
    sheet = book.worksheets[0]
    issue_date_raw = get_date(sheet, "H", 24)
    issue_date = to_utc(
        ct_datetime(issue_date_raw.year, issue_date_raw.month, issue_date_raw.day)
    )

    mpan_core = parse_mpan_core(str(get_int(sheet, "D", 25)))
    start_date_str = get_str(sheet, "D", 22)
    start_date_ct = to_ct(Datetime.strptime(start_date_str, "%d-%b-%Y"))
    start_date = to_utc(start_date_ct)
    finish_date_str = get_str(sheet, "F", 22)
    finish_date_ct = to_ct(Datetime.strptime(finish_date_str, "%d-%b-%Y"))
    finish_date = to_utc(finish_date_ct + relativedelta(hours=23, minutes=30))
    net = round(get_dec(sheet, "H", 33), 2)
    kwh = get_dec(sheet, "D", 33)

    breakdown = {
        "ssp-kwh": kwh,
        "ssp-gbp": net,
    }

    bills.append(
        {
            "bill_type_code": "N",
            "kwh": kwh,
            "vat": Decimal("0.00"),
            "net": net,
            "gross": net,
            "reads": [],
            "breakdown": breakdown,
            "account": mpan_core,
            "issue_date": issue_date,
            "start_date": start_date,
            "finish_date": finish_date,
            "mpan_core": mpan_core,
            "reference": "_".join(
                (
                    to_ct(start_date).strftime("%Y%m%d"),
                    to_ct(finish_date).strftime("%Y%m%d"),
                    to_ct(issue_date).strftime("%Y%m%d"),
                    mpan_core,
                    "ssp",
                )
            ),
        }
    )
    sheet = book.worksheets[3]
    bills.extend(_parse_gduos_sheet(sheet, mpan_core, issue_date))

    return bills


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
