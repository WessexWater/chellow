import decimal
from datetime import datetime as Datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.models import Session
from chellow.utils import hh_format, parse_mpan_core, to_utc


def get_ct_date(row, idx):
    cell = get_cell(row, idx)
    val = cell.value
    if not isinstance(val, Datetime):
        raise BadRequest(f"Problem reading {val} as a timestamp at {cell.coordinate}.")
    return val


def get_start_date(row, idx):
    dt = get_ct_date(row, idx)
    return None if dt is None else to_utc(dt)


def get_cell(row, idx):
    try:
        return row[idx]
    except IndexError:
        raise BadRequest(
            f"For the row {row}, the index is {idx} which is beyond the end of the row."
        )


def get_str(row, idx):
    return get_cell(row, idx).value.strip()


def get_dec(row, idx):
    cell = get_cell(row, idx)
    try:
        return Decimal(str(cell.value))
    except decimal.InvalidOperation as e:
        raise BadRequest(f"Problem parsing the number at {cell.coordinate}. {e}")


def get_int(row, idx):
    return int(get_cell(row, idx).value)


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
        row_index = None
        sess = None
        try:
            sess = Session()
            bills = []
            issue_date_str = get_str(self.sheet[7], 0)
            issue_date = Datetime.strptime(issue_date_str[6:], "%d/%m/%Y %H:%M:%S")
            for row_index in range(12, len(self.sheet["A"]) + 1):
                row = self.sheet[row_index]
                val = get_cell(row, 1).value
                if val is None or val == "":
                    break

                self._set_last_line(row_index, val)
                mpan_core = parse_mpan_core(str(get_int(row, 1)))
                start_date = get_start_date(row, 3)
                finish_date = get_start_date(row, 4) + relativedelta(
                    hours=23, minutes=30
                )

                net = round(get_dec(row, 31), 2)

                cop_3_meters = get_int(row, 6)
                cop_3_rate = get_dec(row, 7)
                cop_3_gbp = get_dec(row, 8)

                # Cop 5 meters
                get_int(row, 9)
                cop_5_rate = get_dec(row, 10)
                cop_5_gbp = get_dec(row, 11)

                ad_hoc_visits = get_dec(row, 21)
                ad_hoc_rate = get_dec(row, 22)
                ad_hoc_gbp = get_dec(row, 23)

                annual_visits = get_int(row, 27)
                annual_rate = get_dec(row, 28)
                annual_gbp = get_dec(row, 29)

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
                    "ad-hoc-gbp": ad_hoc_gbp,
                    "annual-visits-count": annual_visits,
                    "annual-visits-rate": [annual_rate],
                    "annual-visits-gbp": annual_gbp,
                }
                annual_date_cell = get_cell(row, 30)
                annual_date_value = annual_date_cell.value
                if annual_date_value is not None:
                    if isinstance(annual_date_value, Datetime):
                        annual_date = hh_format(annual_date_value)
                    else:
                        annual_date = annual_date_value
                    breakdown["annual-visits-date"] = [annual_date]

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
            raise BadRequest(f"Row number: {row_index} {e.description}")
        finally:
            if sess is not None:
                sess.close()

        return bills
