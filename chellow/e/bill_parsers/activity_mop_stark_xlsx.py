from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.utils import parse_mpan_core, to_utc


class Parser:
    def __init__(self, f):
        self.book = load_workbook(f, data_only=True)
        self.sheet = self.book.worksheets[1]

        self.last_line = None
        self._line_number = None
        self._title_line = None

    def get_cell(self, col, row):
        try:
            coordinates = f"{col}{row}"
            return self.sheet[coordinates]
        except IndexError:
            raise BadRequest(
                f"Can't find the cell {coordinates} on sheet {self.sheet}."
            )

    def get_int(self, col, row):
        return int(self.get_cell(col, row).value)

    def get_dec(self, col, row):
        cell = self.get_cell(col, row)
        try:
            return Decimal(str(cell.value))
        except InvalidOperation as e:
            raise BadRequest(f"Problem parsing the number at {cell.coordinate}. {e}")

    def get_str(self, col, row):
        return self.get_cell(col, row).value.strip()

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
        try:
            bills = []
            issue_date = self.get_start_date("C", 6)

            for row in range(12, len(self.sheet["A"]) + 1):
                val = self.get_cell("B", row).value
                if val is None or val == "":
                    break

                self._set_last_line(row, val)
                mpan_core = parse_mpan_core(str(self.get_int("B", row)))

                start_date = finish_date = self.get_start_date("F", row)
                activity_name_raw = self.get_str("G", row)
                activity_name = activity_name_raw.lower().replace(" ", "_")

                net_dec = self.get_dec("I", row)
                net = round(net_dec, 2)

                vat_dec = self.get_dec("J", row)
                vat = round(vat_dec, 2)

                gross_dec = self.get_dec("K", row)
                gross = round(gross_dec, 2)

                breakdown = {
                    "raw-lines": [],
                    "activity-name": [activity_name],
                    "activity-gbp": net,
                }

                bills.append(
                    {
                        "bill_type_code": "N",
                        "kwh": Decimal(0),
                        "vat": vat,
                        "net": net,
                        "gross": gross,
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
        except BadRequest as e:
            raise BadRequest(f"Row number: {row} {e.description}")

        return bills
