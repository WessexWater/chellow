import csv
import decimal
from decimal import Decimal

from werkzeug.exceptions import BadRequest

from xlrd import open_workbook

from chellow.utils import HH, ct_datetime, to_utc, utc_datetime_now


def get_value(row, title_row, name):
    try:
        idx = title_row.index(name)
    except ValueError:
        return None

    try:
        val = row[idx].value
    except IndexError:
        raise BadRequest(
            f"For the name '{name}', the index is {idx} which is beyond the "
            f"end of the row."
        )

    if isinstance(val, str):
        return val.strip()
    else:
        return val


def get_dec(row, title_row, name):
    val = get_value(row, title_row, name)

    try:
        return val if val is None else Decimal(str(val))
    except decimal.InvalidOperation:
        return None


def get_rate(row, title_row, name):
    raw = get_dec(row, title_row, name)
    return None if raw is None else [raw / Decimal("100")]


def get_date_ct(row, title_row, name):
    s = get_value(row, title_row, name)
    nums = list(map(int, s.split("-")))
    return ct_datetime(nums[0], nums[1], nums[2])


ELEMENT_NAME_LOOKUP = {
    "LVY-CMLOB-ALL": "capmechob",
    "LVY-CMLOP-ALL": "capmechop",
    "DUOS-STND-SITE": "duos-fixed",
    "DUOS-AVAIL-AV": "duos-availability",
    "DUOS-UNIT-AMBER": "duos-amber",
    "DUOS-UNIT-GREEN": "duos-green",
    "DUOS-UNIT-RED": "duos-red",
    "LVY-AAHEDC-ALL": "aahedc",
    "LVY-BSUOS-ALL": "bsuos",
    "LVY-CCL-ALL": "ccl",
    "LVY-CFDOB-ALL": "cfdob",
    "LVY-CFDOP-ALL": "cfdop",
    "LVY-FIT-ALL": "fit",
    "LVY-RO-ALL": "ro",
    "NRG-UNIT-SUMMER": "summer",
    "NRG-UNIT-WINTER": "winter",
    "SYS-ADMIN-ALL": "admin",
    "TUOS-TRIAD-SITE": "triad",
}


def _parse_row(issue_date, row, row_index, datemode, title_row):
    titles = [c.value for c in title_row if c.value is not None]
    bill_start_date_ct = get_date_ct(row, titles, "BILL START DATE")
    start_date = to_utc(bill_start_date_ct)
    bill_finish_date_ct = get_date_ct(row, titles, "BILL END DATE") + (HH * 47)
    finish_date = to_utc(bill_finish_date_ct)

    elements = {}

    kwh = 0
    net_gbp = Decimal("0.00")
    vat_gbp = Decimal("0.00")
    for title in titles[3:]:
        val = get_dec(row, titles, title)
        if val is not None:
            parts = title.split()
            if len(parts) != 3:
                continue
            element_code, typ, units = parts
            element_name = ELEMENT_NAME_LOOKUP[element_code]
            try:
                element = elements[element_name]
            except KeyError:
                element = elements[element_name] = {
                    "name": element_name,
                    "breakdown": {},
                    "net": Decimal("0.00"),
                    "start_date": start_date,
                    "finish_date": finish_date,
                }

            bd = element["breakdown"]
            if typ == "COST":
                element["net"] += round(val, 2)
                net_gbp += round(val, 2)
            elif typ == "USE":
                bd[units.lower()] = val
                if element_name == "aahedc":
                    kwh += val
            elif typ == "RATE":
                bd["rate"] = val

    bd = {"raw_lines": [str(title_row), str(row)]}

    reference = f"{issue_date.strftime('%Y%m%dT%H%M')}_{row_index + 1}"

    return {
        "bill_type_code": "N",
        "kwh": kwh,
        "vat": Decimal("0.00"),
        "net": net_gbp,
        "gross": net_gbp + vat_gbp,
        "reads": [],
        "breakdown": {},
        "account": "2007",
        "issue_date": issue_date,
        "start_date": start_date,
        "finish_date": finish_date,
        "mpan_core": "22 0003 0354 632",
        "reference": reference,
        "elements": list(elements.values()),
    }


class Parser:
    def __init__(self, f):
        self.book = open_workbook(file_contents=f.read())
        self.sheet = self.book.sheet_by_index(1)

        self.last_line = None
        lines = (self._set_last_line(i, l) for i, l in enumerate(f))
        self.reader = csv.reader(lines, skipinitialspace=True)
        self._line_number = None
        self._title_line = None

    @property
    def line_number(self):
        return None if self._line_number is None else self._line_number + 1

    def _set_last_line(self, i, line):
        self._line_numer = i
        self.last_line = line
        if i == 0:
            self._title_line = line
        return line

    def make_raw_bills(self):
        bills = []
        title_row = self.sheet.row(0)
        issue_date = utc_datetime_now()
        for row_index in range(1, self.sheet.nrows):
            row = self.sheet.row(row_index)
            datemode = self.book.datemode
            try:
                bills.append(
                    _parse_row(issue_date, row, row_index, datemode, title_row)
                )
            except BadRequest as e:
                raise BadRequest(f"On row {row_index}: {e.description}")
        return bills
