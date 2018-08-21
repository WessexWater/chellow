from decimal import Decimal
import decimal
from datetime import datetime as Datetime, timedelta as Timedelta
from chellow.utils import parse_mpan_core, to_utc, HH
from xlrd import xldate_as_tuple, open_workbook
from werkzeug.exceptions import BadRequest
from sqlalchemy import or_, null
from chellow.models import Session, Era


def get_date(row, name, datemode):
    val = get_value(row, name)
    if isinstance(val, float):
        return to_utc(Datetime(*xldate_as_tuple(val, datemode)))
    else:
        return None


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


METER_RATE = Decimal('60.00')


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
            title_row = self.sheet.row(0)
            for row_index in range(1, self.sheet.nrows):
                row = self.sheet.row(row_index)
                val = get_value(row, 0)
                if val is None or val == '':
                    break

                self._set_last_line(row_index, val)
                msn = str(get_value(row, 4)).strip()
                mpan_core = parse_mpan_core(str(get_int(row, 5)))
                start_date = get_date(row, 6, self.book.datemode)
                issue_date = start_date
                finish_date = get_date(row, 7, self.book.datemode) + \
                    Timedelta(days=1) - HH
                check = get_str(row, 8)
                if check != 'Billed':
                    continue

                era = sess.query(Era).filter(
                    or_(
                        Era.imp_mpan_core == mpan_core,
                        Era.exp_mpan_core == mpan_core),
                    Era.start_date <= finish_date, or_(
                        Era.finish_date == null(),
                        Era.finish_date > start_date)).order_by(
                    Era.start_date).first()

                if era is None:
                    era = sess.query(Era).filter(
                        or_(
                            Era.imp_mpan_core == mpan_core,
                            Era.exp_mpan_core == mpan_core)).order_by(
                        Era.start_date.desc()).first()

                if era is None:
                    account = mpan_core + '/DC'
                else:
                    account = era.dc_account

                net = METER_RATE / 12

                breakdown = {
                    'raw_lines': [str(title_row)], 'cop': ['5'],
                    'settlement-status': ['non_settlement'], 'msn': [msn],
                    'meter-rate': [METER_RATE], 'meter-gbp': net,
                }

                bills.append(
                    {
                        'bill_type_code': 'N', 'kwh': Decimal(0),
                        'vat': Decimal('0.00'), 'net': net, 'gross': net,
                        'reads': [], 'breakdown': breakdown,
                        'account': account, 'issue_date': issue_date,
                        'start_date': start_date, 'finish_date': finish_date,
                        'mpans': [mpan_core], 'reference': '_'.join(
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
