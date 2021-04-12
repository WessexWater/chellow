from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from werkzeug.exceptions import BadRequest

from xlrd import open_workbook, xldate_as_tuple

from chellow.models import Session
from chellow.utils import ct_datetime, parse_mpan_core, to_utc


def get_date_ct(row, name, datemode):
    val = get_value(row, name)
    if isinstance(val, float):
        return to_utc(Datetime(*xldate_as_tuple(val, datemode)))


def get_start_date(row, name, datemode):
    return to_utc(get_date_ct(row, name, datemode))


def get_finish_date(row, name, datemode):
    d = get_date_ct(row, name, datemode)
    return to_utc(ct_datetime(d.year, d.month, d.day, 23, 30))


def get_value(row, idx):
    try:
        return row[idx].value
    except IndexError:
        raise BadRequest(
            "For the row "
            + str(row)
            + ", the index is "
            + str(idx)
            + " which is beyond the end of the row. "
        )


def get_str(row, idx):
    return get_value(row, idx).strip()


def get_dec(row, idx):
    try:
        return Decimal(str(get_value(row, idx)))
    except InvalidOperation:
        return None


def get_int(row, idx):
    return int(get_value(row, idx))


class Parser:
    def __init__(self, f):
        self.book = open_workbook(file_contents=f.read())
        self.sheet = self.book.sheet_by_index(1)

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
        row_index = sess = None
        try:
            sess = Session()
            bills = []
            title_row = self.sheet.row(10)
            issue_date = get_start_date(self.sheet.row(5), 2, self.book.datemode)
            if issue_date is None:
                raise BadRequest("Expected to find the issue date at cell C6.")

            for row_index in range(11, self.sheet.nrows):
                row = self.sheet.row(row_index)
                val = get_value(row, 1)
                if val is None or val == "":
                    break

                self._set_last_line(row_index, val)
                mpan_core = parse_mpan_core(str(get_int(row, 1)))
                comms = get_str(row, 2)

                settled_str = get_str(row, 3)
                if settled_str == "Settled":
                    settlement_status = "settlement"
                else:
                    settlement_status = "non_settlement"

                start_date = get_start_date(row, 5, self.book.datemode)
                finish_date = get_finish_date(row, 6, self.book.datemode)

                meter_rate = get_dec(row, 7)
                net = round(get_dec(row, 8), 2)
                vat = round(get_dec(row, 9), 2)
                gross = round(get_dec(row, 10), 2)

                breakdown = {
                    "raw-lines": [str(title_row)],
                    "comms": comms,
                    "settlement-status": [settlement_status],
                    "meter-rate": [meter_rate],
                    "meter-gbp": net,
                }

                bills.append(
                    {
                        "bill_type_code": "N",
                        "kwh": Decimal(0),
                        "net": net,
                        "vat": vat,
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
            raise BadRequest("Row number: " + str(row_index) + " " + e.description)
        finally:
            if sess is not None:
                sess.close()

        return bills
