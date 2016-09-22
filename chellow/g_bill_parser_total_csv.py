from dateutil.relativedelta import relativedelta
import csv
import pytz
from collections import defaultdict
from datetime import datetime as Datetime
from decimal import Decimal
from chellow.utils import HH
from io import StringIO


READ_TYPE_MAP = {'PA': 'A'}


def parse_read_type(rt):
    rt = rt.strip()
    return READ_TYPE_MAP.get(rt, rt)


def parse_date(date_str):
    return Datetime.strptime(date_str, "%d/%m/%y").replace(tzinfo=pytz.utc)


def parse_decimal(dec_str):
    return Decimal(''.join(c for c in dec_str if c in '-0123456789.'))


class Parser():
    def __init__(self, f):
        self.csv_reader = csv.reader(
            StringIO(f.getvalue().decode('utf8', errors='ignore')),
            skipinitialspace=True)
        self.titles = ','.join(next(self.csv_reader))
        self._line_number = None

    @property
    def line_number(self):
        return None if self._line_number is None else self._line_number + 2

    def _set_last_line(self, line):
        self.last_line = line
        return line

    def make_raw_bills(self):
        raw_bills = []
        last_bill_reference = None
        raw_bill = None
        for self._line_number, row in enumerate(self.csv_reader):
            if row[0] == '':
                continue
            bill_reference = row[8]
            if last_bill_reference != bill_reference:
                breakdown = defaultdict(int, {'gas_rate': set()})
                raw_bill = {
                    'reference': bill_reference, 'reads': [], 'kwh': 0,
                    'breakdown': breakdown, 'net_gbp': 0, 'vat_gbp': 0,
                    'gross_gbp': 0, 'raw_lines': self.titles + '\n'}
                raw_bills.append(raw_bill)
                last_bill_reference = bill_reference
            if row[9] == '':
                raw_bill['account'] = row[5]
                raw_bill['issue_date'] = parse_date(row[6])
                if row[7] == '':
                    raw_bill['bill_type_code'] = 'N'
                else:
                    raw_bill['bill_type_code'] = 'W'

                raw_bill['msn'] = row[9]
                raw_bill['mprn'] = row[10]
                raw_bill['start_date'] = parse_date(row[17])
                raw_bill['finish_date'] = parse_date(row[18]) + \
                    relativedelta(days=1) - HH
                breakdown['vat_5pc'] += parse_decimal(row[28])
                breakdown['vat_15pc'] += parse_decimal(row[29])
                breakdown['vat_17_5pc'] += parse_decimal(row[30])
                breakdown['vat_20pc'] += parse_decimal(row[31])
                raw_bill['vat_gbp'] += parse_decimal(row[32])
                raw_bill['breakdown']['standing_gbp'] = parse_decimal(row[33])
                raw_bill['gross_gbp'] += parse_decimal(row[34])
                raw_bill['raw_lines'] += u','.join(row) + u'\n'
                raw_bill['net_gbp'] += raw_bill['gross_gbp'] - \
                    raw_bill['vat_gbp']
            else:
                read = {
                    'msn': row[9],
                    'mprn': row[10],
                    'prev_value': parse_decimal(row[11]),
                    'prev_date': parse_date(row[12]),
                    'prev_type_code': parse_read_type(row[13]),
                    'pres_value': parse_decimal(row[14]),
                    'pres_date': parse_date(row[15]),
                    'pres_type_code': parse_read_type(row[16]),
                    'correction_factor': parse_decimal(row[20]),
                    'calorific_value': parse_decimal(row[21]),
                    'units': row[25]}
                vat_gbp = parse_decimal(row[32])
                gross_gbp = parse_decimal(row[34])
                raw_bill['reads'].append(read)
                raw_bill['kwh'] += parse_decimal(row[22])
                raw_bill['net_gbp'] += gross_gbp - vat_gbp
                raw_bill['vat_gbp'] += vat_gbp
                raw_bill['gross_gbp'] += gross_gbp
                raw_bill['raw_lines'] += ','.join(row) + '\n'
                breakdown['gas_rate'].add(parse_decimal(row[23]))
                breakdown['units_consumed'] += parse_decimal(row[24])
                breakdown['gas_gbp'] += parse_decimal(row[26])
                breakdown['ccl_gbp'] += parse_decimal(row[27])
                breakdown['vat_5pc'] += parse_decimal(row[28])
                breakdown['vat_15pc'] += parse_decimal(row[29])
                breakdown['vat_17_5pc'] += parse_decimal(row[30])
                breakdown['vat_20pc'] += parse_decimal(row[31])
        for raw_bill in raw_bills:
            breakdown = raw_bill['breakdown']
            if len(breakdown['gas_rate']) == 1:
                breakdown['gas_rate'] = breakdown['gas_rate'].pop()
            else:
                breakdown['gas_rate'] = ''
            raw_bill['breakdown'] = dict(breakdown)
        return raw_bills
