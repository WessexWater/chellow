from decimal import Decimal
import decimal
from datetime import datetime as Datetime
from chellow.utils import parse_mpan_core, to_utc, to_ct
from xlrd import xldate_as_tuple, open_workbook
from werkzeug.exceptions import BadRequest
from chellow.models import Session, Era
from sqlalchemy import or_, null


def get_date(row, name, datemode):
    val = get_value(row, name)
    if isinstance(val, float):
        return to_utc(to_ct(Datetime(*xldate_as_tuple(val, datemode))))
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


def bd_add(bd, el_name, val):
    if el_name.split('-')[-1] in ('rate', 'kva'):
        if el_name not in bd:
            bd[el_name] = set()
        bd[el_name].add(val)
    else:
        if el_name not in bd:
            bd[el_name] = 0
        try:
            bd[el_name] += val
        except TypeError as e:
            raise Exception(
                "Problem with element name " + el_name + " and value '" +
                str(val) + "': " + str(e))


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
            for row_index in range(11, self.sheet.nrows):
                row = self.sheet.row(row_index)
                val = get_value(row, 1)
                if val is None or val == '':
                    break

                self._set_last_line(row_index, val)
                mpan_core = parse_mpan_core(str(get_int(row, 1)))
                comms = get_str(row, 2)
                settled_str = get_str(row, 3)
                is_settled = settled_str == 'Settled'
                start_date = get_date(row, 5, self.book.datemode)
                finish_date = get_date(row, 6, self.book.datemode)
                mop_rate = get_dec(row, 7)
                net = round(get_dec(row, 8), 2)

                era = sess.query(Era).filter(
                    or_(
                        Era.imp_mpan_core == mpan_core,
                        Era.exp_mpan_core == mpan_core),
                    Era.start_date <= finish_date, or_(
                        Era.finish_date == null(),
                        Era.finish_date > start_date)).order_by(
                    Era.start_date).first()
                account = era.mop_account

                breakdown = {
                    'raw_lines': [str(title_row)], 'comms': comms,
                    'is_settled': str(is_settled), 'mop_rate': mop_rate
                }

                bills.append(
                    {
                        'bill_type_code': 'N', 'kwh': Decimal(0),
                        'vat': Decimal('0.00'), 'net': net, 'gross': net,
                        'reads': [], 'breakdown': breakdown,
                        'account': account,
                        'issue_date': issue_date, 'start_date': start_date,
                        'finish_date': finish_date, 'mpans': [mpan_core],
                        'reference': '_'.join(
                            (
                                start_date.strftime('%Y%m%d'),
                                finish_date.strftime('%Y%m%d'),
                                issue_date.strftime('%Y%m%d'),
                                mpan_core
                            )
                        )
                    }
                )
        except BadRequest as e:
            raise BadRequest(
                "Row number: " + str(row_index) + " " + e.description)
        finally:
            if sess is not None:
                sess.close()

        return bills
