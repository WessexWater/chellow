from dateutil.relativedelta import relativedelta
import openpyxl
from chellow.utils import HH, to_utc
from collections import OrderedDict
from decimal import Decimal


def to_money(row, idx):
    return to_decimal(row, idx, rounding=2)


def to_decimal(row, idx, rounding=6):
    return round(Decimal(row[idx].value), rounding)


def to_int(row, idx):
    return int(row[idx].value)


def to_rate(row, idx):
    return round(Decimal(row[idx].value) / Decimal('100'), 5)


class Parser():
    def __init__(self, f):
        self.book = openpyxl.load_workbook(filename=f)
        self.invoice_sheet = self.book.worksheets[0]
        self.invoice_rows = tuple(self.invoice_sheet.rows)

        self.titles = ','.join(
            c.value for c in self.invoice_rows[0] if c.value is not None)
        self._line_number = None

        self.consumption_sheet = self.book.worksheets[1]
        self.consumption_rows = tuple(self.consumption_sheet.rows)

    @property
    def line_number(self):
        return None if self._line_number is None else self._line_number + 2

    def _set_last_line(self, line):
        self.last_line = line
        return line

    def make_raw_bills(self):
        raw_bills = OrderedDict()
        raw_bill = None
        for self._line_number, row in enumerate(self.invoice_rows[10:]):
            bill_reference_raw = row[1].value
            if bill_reference_raw is None:
                break
            bill_reference = str(bill_reference_raw)
            mprn = str(row[7].value)
            volume_kwh = to_int(row, 9)
            breakdown = {
                'volume_kwh': volume_kwh,
                'commodity_rate': to_rate(row, 11),
                'commodity_gbp': to_money(row, 12),
                'transportation_fixed_rate': to_rate(row, 13),
                'transportation_fixed_gbp': to_money(row, 14),
                'transportation_variable_rate': to_rate(row, 15),
                'transportation_variable_gbp': to_money(row, 16),
                'metering_rate': to_rate(row, 17),
                'metering_gbp': to_money(row, 18),
                'admin_fixed_rate': to_rate(row, 19),
                'admin_fixed_gbp': to_money(row, 20),
                'admin_variable_rate': to_rate(row, 21),
                'admin_variable_gbp': to_money(row, 22),
                'swing_rate': to_rate(row, 23),
                'swing_gbp': to_money(row, 24),
                'ug_gbp': to_money(row, 25),
                'amr_gbp': to_money(row, 26),
                'ad_hoc_gbp': to_money(row, 27),
                'ccl_gbp': to_money(row, 28)}

            raw_bill = {
                'breakdown': breakdown,
                'reference': bill_reference,
                'account': row[7].value,
                'issue_date': row[2].value,
                'bill_type_code': 'N',
                'msn': '',
                'mprn': mprn,
                'start_date': to_utc(row[3].value),
                'finish_date': to_utc(row[4].value) + relativedelta(days=1) -
                HH,
                'net_gbp': to_money(row, 31),
                'vat_gbp': to_money(row, 32),
                'gross_gbp': to_money(row, 33),
                'raw_lines': '',
                'kwh': volume_kwh,
                'reads': []}
            raw_bills[mprn] = raw_bill

        for self._line_number, row in enumerate(self.consumption_rows[10:]):
            bill_reference_raw = row[1].value
            if bill_reference_raw is None:
                break
            bill_reference = str(bill_reference_raw)
            mprn = str(row[5].value)
            read = {
                'msn': '',
                'mprn': mprn,
                'prev_value': to_int(row, 6),
                'prev_date': to_utc(row[7].value),
                'prev_type_code': row[8].value[1],
                'pres_value': to_int(row, 9),
                'pres_date': to_utc(row[10].value),
                'pres_type_code': row[11].value[1],
                'correction_factor': 1,
                'calorific_value': 0,
                'units': 'M3'}
            raw_bill = raw_bills[mprn]
            raw_bill['reads'].append(read)
        return raw_bills.values()
