from decimal import Decimal
import decimal
from datetime import datetime as Datetime
from chellow.utils import parse_mpan_core, to_utc, hh_format, to_ct
from xlrd import xldate_as_tuple, open_workbook
from werkzeug.exceptions import BadRequest
from chellow.models import Session
from dateutil.relativedelta import relativedelta


def get_ct_date(row, name, datemode):
    val = get_value(row, name)
    if isinstance(val, float):
        return to_ct(Datetime(*xldate_as_tuple(val, datemode)))


def get_start_date(row, name, datemode):
    dt = get_ct_date(row, name, datemode)
    return None if dt is None else to_utc(dt)


def get_value(row, idx):
    try:
        return row[idx].value
    except IndexError:
        raise BadRequest(
            "For the row " + str(row) + ", the index is " + str(idx) +
            " which is beyond the end of the row. ")


def get_str(row, idx):
    return get_value(row, idx).strip()


def get_dec(row, idx):
    try:
        return Decimal(str(get_value(row, idx)))
    except decimal.InvalidOperation:
        return None


def get_int(row, idx):
    return int(get_value(row, idx))


class Parser():
    def __init__(self, f):
        self.book = open_workbook(file_contents=f.read())
        self.sheet = self.book.sheet_by_index(0)

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
            title_row = self.sheet.row(10)
            issue_date_str = get_str(self.sheet.row(6), 0)
            issue_date = Datetime.strptime(
                issue_date_str[6:], "%d/%m/%Y %H:%M:%S")
            for row_index in range(11, self.sheet.nrows):
                row = self.sheet.row(row_index)
                val = get_value(row, 1)
                if val is None or val == '':
                    break

                self._set_last_line(row_index, val)
                mpan_core = parse_mpan_core(str(get_int(row, 1)))
                start_date = get_start_date(row, 3, self.book.datemode)
                finish_date = get_start_date(
                    row, 4, self.book.datemode) + relativedelta(
                    hours=23, minutes=30)

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
                annual_date = hh_format(
                    get_start_date(row, 30, self.book.datemode))

                if cop_3_meters > 0:
                    cop = '3'
                    mpan_rate = cop_3_rate
                    mpan_gbp = cop_3_gbp
                else:
                    cop = '5'
                    mpan_rate = cop_5_rate
                    mpan_gbp = cop_5_gbp

                breakdown = {
                    'raw_lines': [str(title_row)], 'cop': [cop],
                    'settlement-status': ['settlement'],
                    'mpan-rate': [mpan_rate], 'mpan-gbp': mpan_gbp,
                    'ad-hoc-visits': ad_hoc_visits,
                    'ad-hoc-rate': [ad_hoc_rate],
                    'ad-hoc-gbp': ad_hoc_gbp,
                    'annual-visits-count': annual_visits,
                    'annual-visits-rate': [annual_rate],
                    'annual-visits-gbp': annual_gbp,
                    'annual-visits-date': [annual_date]
                }

                bills.append(
                    {
                        'bill_type_code': 'N', 'kwh': Decimal(0),
                        'vat': Decimal('0.00'), 'net': net, 'gross': net,
                        'reads': [], 'breakdown': breakdown,
                        'account': mpan_core, 'issue_date': issue_date,
                        'start_date': start_date, 'finish_date': finish_date,
                        'mpan_core': mpan_core, 'reference': '_'.join(
                            (
                                start_date.strftime('%Y%m%d'),
                                finish_date.strftime('%Y%m%d'),
                                issue_date.strftime('%Y%m%d'),
                                mpan_core
                            )
                        )
                    }
                )
                sess.rollback()
        except BadRequest as e:
            raise BadRequest(
                "Row number: " + str(row_index) + " " + e.description)
        finally:
            if sess is not None:
                sess.close()

        return bills
