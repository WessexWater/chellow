from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.utils import parse_mpan_core, to_ct, to_utc


def get_cell(sheet, col, row):
    try:
        coordinates = f"{col}{row}"
        return sheet[coordinates]
    except IndexError:
        raise BadRequest(f"Can't find the cell {coordinates} on sheet {sheet}.")


def get_int(sheet, col, row):
    return int(get_cell(sheet, col, row).value)


def get_dec(sheet, col, row):
    cell = get_cell(sheet, col, row)
    try:
        return Decimal(str(cell.value))
    except InvalidOperation as e:
        raise BadRequest(f"Problem parsing the number at {cell.coordinate}. {e}")


def get_str(sheet, col, row):
    return get_cell(sheet, col, row).value.strip()


def get_ct_date(sheet, col, row):
    cell = get_cell(sheet, col, row)
    val = cell.value
    if isinstance(val, Datetime):
        dt = val
    elif isinstance(val, str):
        dt = Datetime.strptime(val, "dd/mm/yyyy")
    else:
        raise BadRequest(
            f"The value {val} at {cell.coordinate} is of type {type(val)}, but "
            f"expected a timestamp or string."
        )
    return to_ct(dt)


def _process_row(issue_date, sheet, row):
    mpan_core = parse_mpan_core(str(get_int(sheet, "B", row)))

    start_date = finish_date = to_utc(get_ct_date(sheet, "F", row))
    activity_name_raw = get_str(sheet, "G", row)
    activity_name = activity_name_raw.lower().replace(" ", "_")

    net_dec = get_dec(sheet, "I", row)
    net = round(net_dec, 2)

    vat_dec = get_dec(sheet, "J", row)
    vat = round(vat_dec, 2)

    gross_dec = get_dec(sheet, "K", row)
    gross = round(gross_dec, 2)

    breakdown = {
        "raw-lines": [],
        "vat": {20: {"vat": vat, "net": net}},
    }

    return {
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
        "elements": [
            {
                "name": "activity",
                "start_date": start_date,
                "finish_date": finish_date,
                "net": net,
                "breakdown": {"name": {activity_name}},
            }
        ],
    }


class Parser:
    def __init__(self, f):
        self.book = load_workbook(f, data_only=True)
        self.sheet = self.book.worksheets[1]

        self.last_line = None
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
        try:
            bills = []
            issue_date = to_utc(get_ct_date(self.sheet, "C", 6))
            for row in range(12, len(self.sheet["A"]) + 1):
                val = get_cell(self.sheet, "B", row).value
                if val is None or val == "":
                    break
                self._set_last_line(row, val)

                bill = _process_row(issue_date, self.sheet, row)
                bills.append(bill)

        except BadRequest as e:
            raise BadRequest(f"Row number: {row} {e.description}")

        return bills
