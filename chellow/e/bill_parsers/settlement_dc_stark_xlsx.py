from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta

from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.models import Session
from chellow.utils import parse_mpan_core, to_ct, to_utc


def get_ct_date(sheet, col, row):
    cell = get_cell(sheet, col, row)
    val = cell.value
    if not isinstance(val, Datetime):
        raise BadRequest(f"Problem reading {val} as a timestamp at {cell.coordinate}.")
    return to_ct(val)


def get_start_date(sheet, col, row):
    dt = get_ct_date(sheet, col, row)
    return None if dt is None else to_utc(dt)


def get_cell(sheet, col, row):
    try:
        coordinates = f"{col}{row}"
        return sheet[coordinates]
    except IndexError:
        raise BadRequest(f"Can't find the cell {coordinates} on sheet {sheet}.")


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


def _process_row(sess, sheet, row, issue_date):
    mpan_core = parse_mpan_core(str(get_int(sheet, "B", row)))
    start_date_ct = get_ct_date(sheet, "D", row)
    start_date = to_utc(get_ct_date(sheet, "D", row))
    finish_date_ct = get_ct_date(sheet, "E", row) + relativedelta(hours=23, minutes=30)
    finish_date = to_utc(finish_date_ct)

    elements = []

    for (col_meters, col_rate, col_net), cop in (
        ("GHI", "unmetered"),
        ("JKL", "2"),
        ("MNO", "3"),
        ("PQR", "5"),
        ("STU", "10"),
    ):
        meters = get_int(sheet, col_meters, row)
        rate = get_dec(sheet, col_rate, row)
        net = get_dec(sheet, col_net, row)
        if net != 0:
            elements.append(
                {
                    "name": "mpan",
                    "start_date": start_date,
                    "finish_date": finish_date,
                    "net": net,
                    "breakdown": {
                        "rate": {rate},
                        "meters": meters,
                        "cop": {cop},
                    },
                }
            )

    ad_hoc_visits = get_dec(sheet, "AE", row)
    ad_hoc_rate = get_dec(sheet, "AF", row)
    ad_hoc_gbp = get_dec(sheet, "AG", row)
    if ad_hoc_gbp != 0:
        elements.append(
            {
                "name": "ad-hoc",
                "start_date": start_date,
                "finish_date": finish_date,
                "net": ad_hoc_gbp,
                "breakdown": {
                    "rate": {ad_hoc_rate},
                    "activity-name": {"ad_hoc_visit"},
                    "visits": ad_hoc_visits,
                },
            }
        )

    annual_visits_count = get_int(sheet, "AK", row)
    annual_visits_rate = get_dec(sheet, "AL", row)
    annual_visits_gbp = get_dec(sheet, "AM", row)
    if annual_visits_gbp != 0:
        elements.append(
            {
                "name": "annual_visits",
                "start_date": start_date,
                "finish_date": finish_date,
                "net": annual_visits_gbp,
                "breakdown": {
                    "rate": {annual_visits_rate},
                    "count": annual_visits_count,
                },
            }
        )

    breakdown = {
        "raw_lines": [],
        "settlement-status": ["settlement"],
    }

    return {
        "bill_type_code": "N",
        "kwh": Decimal(0),
        "net": Decimal("0.00") + round(get_dec(sheet, "AO", row), 2),
        "vat": Decimal("0.00") + round(get_dec(sheet, "AP", row), 2),
        "gross": Decimal("0.00") + round(get_dec(sheet, "AQ", row), 2),
        "reads": [],
        "breakdown": breakdown,
        "account": mpan_core,
        "issue_date": issue_date,
        "start_date": start_date,
        "finish_date": finish_date,
        "mpan_core": mpan_core,
        "reference": "_".join(
            (
                start_date_ct.strftime("%Y%m%d"),
                finish_date_ct.strftime("%Y%m%d"),
                to_ct(issue_date).strftime("%Y%m%d"),
                mpan_core,
            )
        ),
        "elements": elements,
    }


class Parser:
    def __init__(self, f):
        self.book = load_workbook(f, data_only=True)
        self.sheet = self.book.worksheets[0]

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
        try:
            with Session() as sess:
                bills = []
                issue_date_str = get_str(self.sheet, "A", 7)
                issue_date = to_utc(
                    to_ct(Datetime.strptime(issue_date_str[6:-3], "%d/%m/%Y %H:%M"))
                )
                for row in range(12, len(self.sheet["A"]) + 1):
                    val = get_cell(self.sheet, "A", row).value
                    if val is None or val == "":
                        continue

                    self._set_last_line(row, val)
                    bill = _process_row(sess, self.sheet, row, issue_date)
                    bills.append(bill)
                    sess.rollback()

        except BadRequest as e:
            raise BadRequest(f"Row number: {row} {e.description}")

        return bills
