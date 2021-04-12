import decimal
from datetime import datetime as Datetime
from decimal import Decimal

from werkzeug.exceptions import BadRequest

from xlrd import open_workbook, xldate_as_tuple

from chellow.models import Session
from chellow.utils import parse_mpan_core, to_ct, to_utc


def get_date(row, name, datemode):
    val = get_value(row, name)
    if isinstance(val, float):
        return to_utc(to_ct(Datetime(*xldate_as_tuple(val, datemode))))

    raise BadRequest("Can't find a date.")


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
    except decimal.InvalidOperation:
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
            issue_date = get_date(self.sheet.row(5), 2, self.book.datemode)
            if issue_date is None:
                raise BadRequest("Expected to find the issue date at cell C6.")

            for row_index in range(11, self.sheet.nrows):
                row = self.sheet.row(row_index)
                val = get_value(row, 1)
                if val is None or val == "":
                    break

                self._set_last_line(row_index, val)
                mpan_core = parse_mpan_core(str(get_int(row, 1)))

                start_date = finish_date = get_date(row, 5, self.book.datemode)
                activity_name_raw = get_str(row, 6)
                activity_name = activity_name_raw.lower().replace(" ", "_")

                net_dec = get_dec(row, 8)
                if net_dec is None:
                    raise BadRequest(
                        "Can't find a decimal at column I, expecting the net " "GBP."
                    )
                net = round(net_dec, 2)

                vat_dec = get_dec(row, 9)
                if vat_dec is None:
                    raise BadRequest(
                        "Can't find a decimal at column J, expecting the VAT " "GBP."
                    )

                vat = round(vat_dec, 2)

                gross_dec = get_dec(row, 10)
                if gross_dec is None:
                    raise BadRequest(
                        "Can't find a decimal at column K, expecting the " "gross GBP."
                    )

                gross = round(gross_dec, 2)

                breakdown = {
                    "raw-lines": [str(title_row)],
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
            raise BadRequest("Row number: " + str(row_index) + " " + e.description)
        finally:
            if sess is not None:
                sess.close()

        return bills
