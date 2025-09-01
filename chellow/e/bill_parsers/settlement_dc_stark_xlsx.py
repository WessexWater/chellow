from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta

from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.models import Session
from chellow.utils import parse_mpan_core, to_ct, to_utc


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

    def get_ct_date(self, col, row):
        cell = self.get_cell(col, row)
        val = cell.value
        if not isinstance(val, Datetime):
            raise BadRequest(
                f"Problem reading {val} as a timestamp at {cell.coordinate}."
            )
        return val

    def get_start_date(self, col, row):
        dt = self.get_ct_date(col, row)
        return None if dt is None else to_utc(dt)

    def get_cell(self, col, row):
        try:
            coordinates = f"{col}{row}"
            return self.sheet[coordinates]
        except IndexError:
            raise BadRequest(
                f"Can't find the cell {coordinates} on sheet {self.sheet}."
            )

    def get_str(self, col, row):
        return self.get_cell(col, row).value.strip()

    def get_dec(self, col, row):
        cell = self.get_cell(col, row)
        try:
            return Decimal(str(cell.value))
        except InvalidOperation as e:
            raise BadRequest(f"Problem parsing the number at {cell.coordinate}. {e}")

    def get_int(self, col, row):
        return int(self.get_cell(col, row).value)

    def make_raw_bills(self):
        row_index = None
        try:
            with Session() as sess:
                bills = []
                issue_date_str = self.get_str("A", 7)
                issue_date = to_utc(
                    to_ct(Datetime.strptime(issue_date_str[6:-3], "%d/%m/%Y %H:%M"))
                )
                for row in range(12, len(self.sheet["A"]) + 1):
                    val = self.get_cell("A", row).value
                    if val is None or val == "":
                        break

                    self._set_last_line(row_index, val)
                    mpan_core = parse_mpan_core(str(self.get_int("B", row)))
                    start_date = to_utc(to_ct(self.get_start_date("D", row)))
                    finish_date = to_utc(
                        to_ct(self.get_start_date("E", row))
                        + relativedelta(hours=23, minutes=30)
                    )

                    net = round(self.get_dec("AO", row), 2)

                    elements = []

                    for (col_meters, col_rate, col_net), cop in (
                        ("GHI", "unmetered"),
                        ("JKL", "2"),
                        ("MNO", "3"),
                        ("PQR", "5"),
                        ("STU", "10"),
                    ):
                        meters = self.get_int(col_meters, row)
                        rate = self.get_dec(col_rate, row)
                        net = self.get_dec(col_net, row)
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

                    ad_hoc_visits = self.get_dec("AE", row)
                    ad_hoc_rate = self.get_dec("AF", row)
                    ad_hoc_gbp = self.get_dec("AG", row)
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

                    annual_visits_count = self.get_int("AK", row)
                    annual_visits_rate = self.get_dec("AL", row)
                    annual_visits_gbp = self.get_dec("AM", row)
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

                    bills.append(
                        {
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
                                    start_date.strftime("%Y%m%d"),
                                    finish_date.strftime("%Y%m%d"),
                                    issue_date.strftime("%Y%m%d"),
                                    mpan_core,
                                )
                            ),
                            "elements": elements,
                        }
                    )
                    sess.rollback()

        except BadRequest as e:
            raise BadRequest(f"Row number: {row} {e.description}")

        return bills
