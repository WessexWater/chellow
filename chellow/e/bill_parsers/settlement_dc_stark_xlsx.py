from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta

from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.models import Session
from chellow.utils import parse_mpan_core, to_utc


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
                issue_date = Datetime.strptime(issue_date_str[6:], "%d/%m/%Y %H:%M:%S")
                for row in range(12, len(self.sheet["A"]) + 1):
                    val = self.get_cell("A", row).value
                    if val is None or val == "":
                        break

                    self._set_last_line(row_index, val)
                    mpan_core = parse_mpan_core(str(self.get_int("B", row)))
                    start_date = self.get_start_date("D", row)
                    finish_date = self.get_start_date("E", row) + relativedelta(
                        hours=23, minutes=30
                    )

                    net = round(self.get_dec("W", row), 2)

                    cop_3_meters = self.get_int("G", row)
                    cop_3_rate = self.get_dec("H", row)
                    cop_3_gbp = self.get_dec("I", row)

                    # Cop 5 meters
                    self.get_int("J", row)
                    cop_5_rate = self.get_dec("K", row)
                    cop_5_gbp = self.get_dec("L", row)

                    ad_hoc_visits = self.get_dec("P", row)
                    ad_hoc_rate = self.get_dec("Q", row)
                    ad_hoc_gbp = self.get_dec("R", row)
                    activity_names = set()
                    activity_gbp = Decimal("0")
                    if ad_hoc_gbp != 0:
                        activity_names.add("ad_hoc_visit")
                        activity_gbp += ad_hoc_gbp

                    annual_visits = self.get_int("S", row)
                    annual_rate = self.get_dec("T", row)
                    annual_gbp = self.get_dec("U", row)
                    if annual_gbp != 0:
                        activity_names.add("annual_visit")
                        activity_gbp += annual_gbp

                    if cop_3_meters > 0:
                        cop = "3"
                        mpan_rate = cop_3_rate
                        mpan_gbp = cop_3_gbp
                    else:
                        cop = "5"
                        mpan_rate = cop_5_rate
                        mpan_gbp = cop_5_gbp

                    breakdown = {
                        "raw_lines": [],
                        "cop": [cop],
                        "settlement-status": ["settlement"],
                        "mpan-rate": [mpan_rate],
                        "mpan-gbp": mpan_gbp,
                        "ad-hoc-visits": ad_hoc_visits,
                        "ad-hoc-rate": [ad_hoc_rate],
                        "ad-hoc-gbp-info": ad_hoc_gbp,
                        "annual-visits-count": annual_visits,
                        "annual-visits-rate": [annual_rate],
                        "annual-visits-gbp-info": annual_gbp,
                    }
                    if len(activity_names) > 0:
                        breakdown["activity-name"] = sorted(activity_names)

                    if activity_gbp != 0:
                        breakdown["activity-gbp"] = activity_gbp

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
                        }
                    )
                    sess.rollback()

        except BadRequest as e:
            raise BadRequest(f"Row number: {row} {e.description}")

        return bills
