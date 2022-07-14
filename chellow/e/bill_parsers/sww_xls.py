import csv
import decimal
from decimal import Decimal

from werkzeug.exceptions import BadRequest

from xlrd import open_workbook

from chellow.utils import HH, utc_datetime, utc_datetime_now


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
    return utc_datetime(nums[0], nums[1], nums[2])


def _parse_row(row, row_index, datemode, title_row):
    titles = [c.value for c in title_row]
    bill_start_date = get_date_ct(row, titles, "BILL START DATE")
    bill_finish_date = get_date_ct(row, titles, "BILL END DATE") + (HH * 47)
    issue_date = utc_datetime_now()

    aahedc_kwh = get_dec(row, titles, "LVY-AAHEDC-ALL USE KWH")

    vals = [
        ("capmechob-kwh", get_dec(row, titles, "LVY-CMLOB-ALL USE KWH")),
        ("capmechob-rate", get_dec(row, titles, "LVY-CMLOB-ALL RATE P/KWH")),
        ("capmechob-gbp", get_dec(row, titles, "LVY-CMLOB-ALL COST GBP")),
        ("capmechop-kwh", get_dec(row, titles, "LVY-CMLOP-ALL USE KWH")),
        ("capmechop-rate", get_dec(row, titles, "LVY-CMLOP-ALL RATE P/KWH")),
        ("capmechop-gbp", get_dec(row, titles, "LVY-CMLOP-ALL COST GBP")),
        ("duos-fixed-days", get_dec(row, titles, "DUOS-STND-SITE USE DAY")),
        (
            "duos-availability-kva-days",
            [get_dec(row, titles, "DUOS-AVAIL-AV USE KVADAY")],
        ),
        (
            "duos-availability-rate",
            get_rate(row, titles, "DUOS-AVAIL-AV RATE P/KVADAY"),
        ),
        ("duos-availability-gbp", get_dec(row, titles, "DUOS-AVAIL-AV COST GBP")),
        ("duos-fixed-rate", get_rate(row, titles, "DUOS-STND-SITE RATE P/DAY")),
        ("duos-fixed-gbp", get_dec(row, titles, "DUOS-STND-SITE COST GBP")),
        ("duos-amber-kwh", get_dec(row, titles, "DUOS-UNIT-AMBER USE KWH")),
        ("duos-amber-rate", get_rate(row, titles, "DUOS-UNIT-AMBER RATE P/KWH")),
        ("duos-amber-gbp", get_dec(row, titles, "DUOS-UNIT-AMBER COST GBP")),
        ("duos-green-kwh", get_dec(row, titles, "DUOS-UNIT-GREEN USE KWH")),
        ("duos-green-rate", get_rate(row, titles, "DUOS-UNIT-GREEN RATE P/KWH")),
        ("duos-green-gbp", get_dec(row, titles, "DUOS-UNIT-GREEN COST GBP")),
        ("duos-red-kwh", get_dec(row, titles, "DUOS-UNIT-RED USE KWH")),
        ("duos-red-rate", get_rate(row, titles, "DUOS-UNIT-RED RATE P/KWH")),
        ("duos-red-gbp", get_dec(row, titles, "DUOS-UNIT-RED COST GBP")),
        ("aahedc-kwh", aahedc_kwh),
        ("aahedc-rate", get_rate(row, titles, "LVY-AAHEDC-ALL RATE P/KWH")),
        ("aahedc-gbp", get_dec(row, titles, "LVY-AAHEDC-ALL COST GBP")),
        ("bsuos-nbp-kwh", get_dec(row, titles, "LVY-BSUOS-ALL USE KWH")),
        ("bsuos-rate", get_rate(row, titles, "LVY-BSUOS-ALL RATE P/KWH")),
        ("bsuos-gbp", get_dec(row, titles, "LVY-BSUOS-ALL COST GBP")),
        ("ccl-kwh", get_dec(row, titles, "LVY-CCL-ALL USE KWH")),
        ("ccl-rate", get_rate(row, titles, "LVY-CCL-ALL RATE P/KWH")),
        ("ccl-gbp", get_dec(row, titles, "LVY-CCL-ALL COST GBP")),
        ("cfdob-kwh", get_dec(row, titles, "LVY-CFDOB-ALL USE KWH")),
        ("cfdob-rate", get_rate(row, titles, "LVY-CFDOB-ALL RATE P/KWH")),
        ("cfdob-gbp", get_dec(row, titles, "LVY-CFDOB-ALL COST GBP")),
        ("cfdop-kwh", get_dec(row, titles, "LVY-CFDOP-ALL USE KWH")),
        ("cfdop-rate", get_rate(row, titles, "LVY-CFDOP-ALL RATE P/KWH")),
        ("cfdop-gbp", get_dec(row, titles, "LVY-CFDOP-ALL COST GBP")),
        ("fit-kwh", get_dec(row, titles, "LVY-FIT-ALL USE KWH")),
        ("fit-rate", get_rate(row, titles, "LVY-FIT-ALL RATE P/KWH")),
        ("fit-gbp", get_dec(row, titles, "LVY-FIT-ALL COST GBP")),
        ("ro-kwh", get_dec(row, titles, "LVY-RO-ALL USE KWH")),
        ("ro-rate", get_rate(row, titles, "LVY-RO-ALL RATE P/KWH")),
        ("ro-gbp", get_dec(row, titles, "LVY-RO-ALL COST GBP")),
        ("summer-kwh", get_dec(row, titles, "NRG-UNIT-SUMMER USE KWH")),
        ("summer-rate", get_rate(row, titles, "NRG-UNIT-SUMMER RATE P/KWH")),
        ("summer-gbp", get_dec(row, titles, "NRG-UNIT-SUMMER COST GBP")),
        ("winter-kwh", get_dec(row, titles, "NRG-UNIT-WINTER USE KWH")),
        ("winter-rate", get_rate(row, titles, "NRG-UNIT-WINTER RATE P/KWH")),
        ("winter-gbp", get_dec(row, titles, "NRG-UNIT-WINTER COST GBP")),
        ("admin-months", get_dec(row, titles, "SYS-ADMIN-ALL USE MO")),
        ("admin-rate", [get_dec(row, titles, "SYS-ADMIN-ALL RATE GBP/MO")]),
        ("admin-gbp", get_dec(row, titles, "SYS-ADMIN-ALL COST GBP")),
        ("triad-days", get_dec(row, titles, "TUOS-TRIAD-SITE USE DAY")),
        ("triad-rate", [get_dec(row, titles, "TUOS-TRIAD-SITE RATE GBP/DAY")]),
        ("triad-gbp", get_dec(row, titles, "TUOS-TRIAD-SITE COST GBP")),
    ]

    bd = {
        "raw_lines": [str(title_row), str(row)],
    }

    for k, v in vals:
        if v is not None and v != [None]:
            bd[k] = v

    kwh = Decimal("0.00") if aahedc_kwh is None else aahedc_kwh
    net_gbp = Decimal("0.00")
    net_gbp += sum(v for k, v in bd.items() if k.endswith("-gbp"))
    vat_gbp = Decimal("0.00")
    reference = issue_date.strftime("%Y%m%dT%H%M") + "_" + str(row_index + 1)

    return {
        "bill_type_code": "N",
        "kwh": kwh,
        "vat": Decimal("0.00"),
        "net": net_gbp,
        "gross": net_gbp + vat_gbp,
        "reads": [],
        "breakdown": bd,
        "account": "2007",
        "issue_date": issue_date,
        "start_date": bill_start_date,
        "finish_date": bill_finish_date,
        "mpan_core": "22 0003 0354 632",
        "reference": reference,
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
        for row_index in range(1, self.sheet.nrows):
            row = self.sheet.row(row_index)
            datemode = self.book.datemode
            try:
                bills.append(_parse_row(row, row_index, datemode, title_row))
            except BadRequest as e:
                raise BadRequest("On row " + str(row_index) + ": " + str(e.description))
        return bills
