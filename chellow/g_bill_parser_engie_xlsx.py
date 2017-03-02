from dateutil.relativedelta import relativedelta
import openpyxl
from chellow.utils import HH, to_utc
from collections import OrderedDict
from decimal import Decimal


def to_money(cell):
    return Decimal('0.00') + round(Decimal(cell.value), 2)


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
            volume_kwh = Decimal(row[9].value)
            breakdown = {
                'volume_kwh': volume_kwh,
                'commodity_rate': row[11].value / 100,
                'commodity_gbp': row[12].value,
                'transportation_fixed_rate': row[13].value / 100,
                'transportation_fixed_gbp': row[14].value,
                'transportation_variable_rate': row[15].value / 100,
                'transportation_variable_gbp': row[16].value,
                'metering_rate': row[17].value / 100,
                'metering_gbp': row[18].value,
                'admin_fixed_rate': row[19].value / 100,
                'admin_fixed_gbp': row[20].value,
                'admin_variable_rate': row[21].value / 100,
                'admin_variable_gbp': row[22].value,
                'swing_rate': row[23].value / 100,
                'swing_gbp': row[24].value,
                'ug_gbp': row[25].value,
                'amr_gbp': row[26].value,
                'ad_hoc_gbp': row[27].value,
                'ccl_gbp': row[28].value}

            raw_bill = {
                'breakdown': breakdown,
                'reference': bill_reference,
                'account': row[7].value,
                'issue_date': row[2].value,
                'bill_type_code': 'N',
                'msn': '',
                'mprn': str(row[7].value),
                'start_date': to_utc(row[3].value),
                'finish_date': to_utc(row[4].value) + relativedelta(days=1) -
                HH,
                'net_gbp': to_money(row[31]),
                'vat_gbp': to_money(row[32]),
                'gross_gbp': to_money(row[33]),
                'raw_lines': '',
                'kwh': Decimal(volume_kwh),
                'reads': []}
            raw_bills[bill_reference] = raw_bill

        for self._line_number, row in enumerate(self.consumption_rows[10:]):
            bill_reference_raw = row[1].value
            if bill_reference_raw is None:
                break
            bill_reference = str(bill_reference_raw)
            read = {
                'msn': '',
                'mprn': str(row[5].value),
                'prev_value': row[6].value,
                'prev_date': to_utc(row[7].value),
                'prev_type_code': row[8].value[1],
                'pres_value': row[9].value,
                'pres_date': to_utc(row[10].value),
                'pres_type_code': row[11].value[1],
                'correction_factor': 1,
                'calorific_value': 0,
                'units': 'M3'}
            raw_bill = raw_bills[bill_reference]
            raw_bill['reads'].append(read)
        return raw_bills.values()
