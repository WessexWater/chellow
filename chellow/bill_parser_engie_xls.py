from decimal import Decimal
import decimal
from datetime import datetime as Datetime
import csv
from chellow.utils import parse_mpan_core, HH, to_utc, to_ct
from itertools import count
from xlrd import xldate_as_tuple, open_workbook
from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import BadRequest


ELEM_MAP = {
    ('Assistance for Areas with High Electricity Distribution Costs (AAHEDC)',
        '', 'Usage'): 'aahedc-gsp-kwh',
    ('Assistance for Areas with High Electricity Distribution Costs (AAHEDC)',
        '', 'Price'): 'aahedc-rate',
    ('Assistance for Areas with High Electricity Distribution Costs (AAHEDC)',
        '', 'Amount'): 'aahedc-gbp',
    ('Balancing Services Use of System (BSUoS)', '', 'Usage'): 'buos-nbp-kwh',
    ('Balancing Services Use of System (BSUoS)', '', 'Price'): 'bsuos-rate',
    ('Balancing Services Use of System (BSUoS)', '', 'Amount'): 'bsuos-gbp',
    ('Capacity Market (Actual)', '', 'Usage'): 'capacity-gsp-kwh',
    ('Capacity Market (Actual)', '', 'Price'): 'capacity-rate',
    ('Capacity Market (Actual)', '', 'Amount'): 'capacity-gbp',
    ('Capacity Market (Estimate)', '', 'Usage'): 'capacity-gsp-kwh',
    ('Capacity Market (Estimate)', '', 'Price'): 'capacity-rate',
    ('Capacity Market (Estimate)', '', 'Amount'): 'capacity-gbp',
    ('CfD FiT (Actual)', '', 'Usage'): 'cfd-fit-nbp-kwh',
    ('CfD FiT (Actual)', '', 'Price'): 'cfd-fit-rate',
    ('CfD FiT (Actual)', '', 'Amount'): 'cfd-fit-gbp',
    ('CfD FiT (Estimate)', '', 'Usage'): 'cfd-fit-nbp-kwh',
    ('CfD FiT (Estimate)', '', 'Price'): 'cfd-fit-rate',
    ('CfD FiT (Estimate)', '', 'Amount'): 'cfd-fit-gbp',
    ('CCL', '', 'Usage'): 'ccl-kwh',
    ('CCL', '', 'Price'): 'ccl-rate',
    ('CCL', '', 'Amount'): 'ccl-gbp',
    ('DUoS Unit Charge 3', '', 'Usage'): 'duos-green-kwh',
    ('DUoS Unit Charge 3', '', 'Price'): 'duos-green-rate',
    ('DUoS Unit Charge 3', '', 'Amount'): 'duos-green-gbp',
    ('DUoS Unit Charge 2', '', 'Usage'): 'duos-amber-kwh',
    ('DUoS Unit Charge 2', '', 'Price'): 'duos-amber-rate',
    ('DUoS Unit Charge 2', '', 'Amount'): 'duos-amber-gbp',
    ('DUoS Unit Charge 1', '', 'Usage'): 'duos-red-kwh',
    ('DUoS Unit Charge 1', '', 'Price'): 'duos-red-rate',
    ('DUoS Unit Charge 1', '', 'Amount'): 'duos-red-gbp',
    ('DUoS Standing Charge', '', 'Usage'): 'duos-fixed-days',
    ('DUoS Standing Charge', '', 'Price'): 'duos-fixed-rate',
    ('DUoS Standing Charge', '', 'Amount'): 'duos-fixed-gbp',
    ('DUoS Reactive', '', 'Usage'): 'duos-reactive-kvarh',
    ('DUoS Reactive', '', 'Price'): 'duos-reactive-rate',
    ('DUoS Reactive', '', 'Amount'): 'duos-reactive-gbp',
    ('Flex Adj', '', 'Amount'): 'reconciliation-gbp',
    ('Feed in Tariff (FiT)', '', 'Usage'): 'fit-msp-kwh',
    ('Feed in Tariff (FiT)', '', 'Price'): 'fit-rate',
    ('Feed in Tariff (FiT)', '', 'Amount'): 'fit-gbp',
    ('Feed in Tariff (FiT) Actual', '', 'Usage'): 'fit-msp-kwh',
    ('Feed in Tariff (FiT) Actual', '', 'Price'): 'fit-rate',
    ('Feed in Tariff (FiT) Actual', '', 'Amount'): 'fit-gbp',
    ('Feed in Tariff (FiT) Estimate', '', 'Usage'): 'fit-msp-kwh',
    ('Feed in Tariff (FiT) Estimate', '', 'Price'): 'fit-rate',
    ('Feed in Tariff (FiT) Estimate', '', 'Amount'): 'fit-gbp',
    ('Levy Exempt Energy', '', 'Usage'): 'lec-kwh',
    ('Levy Exempt Energy', '', 'Price'): 'lec-rate',
    ('Levy Exempt Energy', '', 'Amount'): 'lec-gbp',
    ('Meter Rental', '', 'Usage'): 'meter-rental-days',
    ('Meter Rental', '', 'Price'): 'meter-rental-rate',
    ('Meter Rental', '', 'Amount'): 'meter-rental-gbp',
    ('Renewables Obligation (RO)', '', 'Usage'): 'ro-msp-kwh',
    ('Renewables Obligation (RO)', '', 'Price'): 'ro-rate',
    ('Renewables Obligation (RO)', '', 'Amount'): 'ro-gbp',
    ('TNUoS (Estimated)', '', 'Usage'): 'triad-gsp-kw',
    ('TNUoS (Estimated)', '', 'Price'): 'triad-rate',
    ('TNUoS (Estimated)', '', 'Amount'): 'triad-gbp',
    ('TNUoS (Credit)', '', 'Usage'): 'triad-gsp-kw',
    ('TNUoS (Credit)', '', 'Price'): 'triad-rate',
    ('TNUoS (Credit)', '', 'Amount'): 'triad-gbp',
    ('TNUoS (Actual)', '', 'Usage'): 'triad-gsp-kw',
    ('TNUoS (Actual)', '', 'Price'): 'triad-rate',
    ('TNUoS (Actual)', '', 'Amount'): 'triad-gbp',
    ('Unit Rate', 'Summer Weekday', 'Usage'): 'summer-weekday-gsp-kwh',
    ('Unit Rate', 'Summer Weekday', 'Price'): 'summer-weekday-rate',
    ('Unit Rate', 'Summer Weekday', 'Amount'): 'summer-weekday-gbp',
    ('Unit Rate', 'Peak', 'Usage'): 'peak-gsp-kwh',
    ('Unit Rate', 'Peak', 'Price'): 'peak-rate',
    ('Unit Rate', 'Peak', 'Amount'): 'peak-gbp',
    ('Unit Rate', 'Peak Shoulder', 'Usage'): 'peak-shoulder-gsp-kwh',
    ('Unit Rate', 'Peak Shoulder', 'Price'): 'peak-shoulder-rate',
    ('Unit Rate', 'Peak Shoulder', 'Amount'): 'peak-shoulder-gbp',
    ('Unit Rate', 'Summer Night', 'Usage'): 'summer-night-gsp-kwh',
    ('Unit Rate', 'Summer Night', 'Price'): 'summer-night-rate',
    ('Unit Rate', 'Summer Night', 'Amount'): 'summer-night-gbp',
    ('Unit Rate', 'Summer Weekend & Bank Holiday', 'Usage'):
        'summer-weekend-gsp-kwh',
    ('Unit Rate', 'Summer Weekend & Bank Holiday', 'Price'):
        'summer-weekend-rate',
    ('Unit Rate', 'Summer Weekend & Bank Holiday', 'Amount'):
        'summer-weekend-gbp',
    ('Unit Rate', 'Night', 'Usage'): 'night-gsp-kwh',
    ('Unit Rate', 'Night', 'Price'): 'night-rate',
    ('Unit Rate', 'Night', 'Amount'): 'night-gbp',
    ('Unit Rate', 'Winter Weekday', 'Usage'): 'winter-weekday-gsp-kwh',
    ('Unit Rate', 'Winter Weekday', 'Price'): 'winter-weekday-rate',
    ('Unit Rate', 'Winter Weekday', 'Amount'): 'winter-weekday-gbp',
    ('Unit Rate', 'Winter Weekend & Bank Holiday', 'Usage'):
        'winter-weekend-gsp-kwh',
    ('Unit Rate', 'Winter Weekend & Bank Holiday', 'Price'):
        'winter-weekend-rate',
    ('Unit Rate', 'Winter Weekend & Bank Holiday', 'Amount'):
        'winter-weekend-gbp',
    ('Unit Rate', 'Winter Night', 'Usage'): 'winter-night-gsp-kwh',
    ('Unit Rate', 'Winter Night', 'Price'): 'winter-night-rate',
    ('Unit Rate', 'Winter Night', 'Amount'): 'winter-night-gbp',
    ('Reverse BSUoS in Unit Rate', '', 'Usage'): 'bsuos-reverse-nbp-kwh',
    ('Reverse BSUoS in Unit Rate', '', 'Price'): 'bsuos-reverse-rate',
    ('Reverse BSUoS in Unit Rate', '', 'Amount'): 'bsuos-reverse-gbp',
    ('Reverse CfD FiT (Estimate)', '', 'Usage'): 'cfd-fit-nbp-kwh',
    ('Reverse CfD FiT (Estimate)', '', 'Price'): 'cfd-rate',
    ('Reverse CfD FiT (Estimate)', '', 'Amount'): 'cfd-fit-gbp'}


COLUMNS = [
    'Billing Entity',
    'Customer Name',
    'Customer Number',
    'Account Name',
    'Account Number',
    'Billing Address',
    'Bill Number',
    'Bill Date',
    'Due Date',
    'Accepted Date',
    'Bill Period',
    'Agreement Number',
    'Product Bundle',
    'Product Name',
    'Bill Status',
    'Product Item Class',
    'Type',
    'Description',
    'From Date',
    'To Date',
    'Sales Tax Rate',
    'Meter Point',
    'Usage',
    'Usage Unit',
    'Price',
    'Amount',
    'Currency',
    'Indicator',
    'Product Item Name',
    'Rate Name']

COLUMN_MAP = dict(zip(COLUMNS, count()))


def get_date(row, name, datemode):
    val = get_value(row, name)
    if isinstance(val, float):
        return to_utc(to_ct(Datetime(*xldate_as_tuple(val, datemode))))
    else:
        return None


def get_value(row, name):
    idx = COLUMN_MAP[name]
    try:
        val = row[idx].value
    except IndexError:
        raise BadRequest(
            "For the row " + str(row) + " and name '" + name +
            "', the index is " + str(idx) +
            " which is beyond the end of the row. ")
    if isinstance(val, str):
        return val.strip()
    else:
        return val


def get_dec(row, name):
    try:
        return Decimal(str(get_value(row, name)))
    except decimal.InvalidOperation:
        return None


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
        lines = (self._set_last_line(i, l) for i, l in enumerate(f))
        self.reader = csv.reader(lines, skipinitialspace=True)
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
        bills = {}
        title_row = self.sheet.row(0)
        for row_index in range(1, self.sheet.nrows):
            row = self.sheet.row(row_index)
            mpan_core = parse_mpan_core(
                str(int(get_value(row, 'Meter Point'))))
            bill_period = get_value(row, 'Bill Period')
            if '-' in bill_period:
                period_start, period_finish = [
                    to_utc(to_ct(Datetime.strptime(d, '%Y-%m-%d')))
                    for d in bill_period.split(' - ')]
                period_finish += relativedelta(days=1) - HH
            else:
                period_start, period_finish = None, None

            from_date = get_date(row, 'From Date', self.book.datemode)
            if from_date is None:
                if period_start is None:
                    raise BadRequest(
                        "Can't find a bill finish date in row " +
                        str(row_index) + ".")
                else:
                    from_date = period_start

            to_date = get_date(row, 'To Date', self.book.datemode)
            if to_date is None:
                if period_finish is None:
                    raise BadRequest(
                        "Can't find a bill finish date in row " +
                        str(row_index) + " .")
                else:
                    to_date = period_finish

            else:
                to_date += relativedelta(days=1) - HH

            issue_date = get_date(row, 'Bill Date', self.book.datemode)
            key = bill_period, from_date, to_date, mpan_core, issue_date
            try:
                bill = bills[key]
            except KeyError:
                bills[key] = bill = {
                    'bill_type_code': 'N', 'kwh': Decimal(0),
                    'vat': Decimal('0.00'), 'net': Decimal('0.00'),
                    'reads': [],
                    'breakdown': {'raw_lines': [str(title_row)]},
                    'account': mpan_core,
                    'issue_date': issue_date, 'start_date': from_date,
                    'finish_date': to_date, 'mpans': [mpan_core],
                    'reference': '_'.join(
                        (
                            bill_period, from_date.strftime('%Y%m%d'),
                            to_date.strftime('%Y%m%d'),
                            issue_date.strftime('%Y%m%d'),
                            mpan_core))}
            bd = bill['breakdown']

            usage = get_dec(row, 'Usage')
            usage_units = get_value(row, 'Usage Unit')
            price = get_dec(row, 'Price')
            amount = get_dec(row, 'Amount')
            product_item_name = get_value(row, 'Product Item Name')
            rate_name = get_value(row, 'Rate Name')
            if usage_units == 'kWh':
                if product_item_name == 'Renewables Obligation (RO)':
                    bill['kwh'] += round(usage, 2)
                elif product_item_name == "Unit Rate":
                    bd_add(bd, 'sum-gsp-kwh', usage)
            description = get_value(row, 'Description')
            if description in ('Standard VAT@20%', 'Reduced VAT@5%'):
                bill['vat'] += round(amount, 2)
            else:
                bill['net'] += round(amount, 2)

            for q, qname in (
                    (usage, 'Usage'), (price, 'Price'), (amount, 'Amount')):
                try:
                    elem_key = ELEM_MAP[(description, rate_name, qname)]
                    bd_add(bd, elem_key, q)
                except KeyError:
                    pass

            duos_avail_prefix = "DUoS Availability ("
            duos_excess_avail_prefix = "DUoS Excess Availability ("
            if description.startswith("DUoS Availability"):
                if description.startswith(duos_avail_prefix):
                    bd_add(
                        bd, 'duos-availability-kva',
                        int(description[len(duos_avail_prefix):-5]))
                bd_add(bd, 'duos-availability-days', usage)
                bd_add(bd, 'duos-availability-rate', price)
                bd_add(bd, 'duos-availability-gbp', amount)
            elif description.startswith("DUoS Excess Availability"):
                if description.startswith(duos_excess_avail_prefix):
                    bd_add(
                        bd, 'duos-excess-availability-kva',
                        int(description[len(duos_excess_avail_prefix):-5]))
                bd_add(bd, 'duos-excess-availability-days', usage)
                bd_add(bd, 'duos-excess-availability-rate', price)
                bd_add(bd, 'duos-excess-availability-gbp', amount)
            elif description.startswith('BSUoS Black Start '):
                bd_add(bd, 'black-start-gbp', amount)
            elif description.startswith('BSUoS Reconciliation - '):
                if usage is not None:
                    bd_add(bd, 'bsuos-nbp-kwh', usage)
                if price is not None:
                    bd_add(bd, 'bsuos-rate', price)
                bd_add(bd, 'bsuos-gbp', amount)
            elif description.startswith("FiT Rec - "):
                bd_add(bd, 'fit-gbp', amount)
            elif description.startswith("CfD FiT Rec - "):
                bd_add(bd, 'cfd-fit-gbp', amount)
            elif description.startswith("Flex "):
                bd_add(bd, 'reconciliation-gbp', amount)
            elif description.startswith("Legacy TNUoS Reversal "):
                bd_add(bd, 'triad-gbp', amount)

        for bill in bills.values():
            bd = bill['breakdown']
            for k, v in tuple(bd.items()):
                if isinstance(v, set):
                    val = ', '.join(sorted(map(str, v)))
                else:
                    val = v
                bd[k] = val
            bill['gross'] = bill['net'] + bill['vat']

        return [v for k, v in sorted(bills.items())]
