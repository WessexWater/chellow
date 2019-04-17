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
    'Meter - UK Electricity - AAHEDC Pass-Thru': (
        'aahedc-gsp-kwh', 'aahedc-rate', 'aahedc-gbp'),
    'Meter - UK Electricity - BSUoS Pass-Thru': (
        'bsuos-nbp-kwh', 'bsuos-rate', 'bsuos-gbp'),
    'Meter - UK Electricity - Capacity Market Pass-Thru': (
        'capacity-gsp-kwh', 'capacity-rate', 'capacity-gbp'),
    'Meter - UK Electricity - CfD FiT Pass-Thru':
        ('cfd-fit-nbp-kwh', 'cfd-fit-rate', 'cfd-fit-gbp'),
    'Meter - UK Electricity - CCL': {
        'CCL': ('ccl-kwh', 'ccl-rate', 'ccl-gbp'),
        'Levy Exempt Energy': ('lec-kwh', 'lec-rate', 'lec-gbp')
    },
    'Meter - UK Electricity - DUoS': {
        'DUoS Unit Charge 3':
            ('duos-green-kwh', 'duos-green-rate', 'duos-green-gbp'),
        'DUoS Unit Charge 2':
            ('duos-amber-kwh', 'duos-amber-rate', 'duos-amber-gbp'),
        'DUoS Unit Charge 1':
            ('duos-red-kwh', 'duos-red-rate', 'duos-red-gbp'),
        'DUoS Standing Charge':
            ('duos-fixed-days', 'duos-fixed-rate', 'duos-fixed-gbp'),
        'DUoS Reactive': (
            'duos-reactive-kvarh', 'duos-reactive-rate', 'duos-reactive-gbp')
    },
    'Meter - UK Electricity - FiT Pass-Thru':
        ('fit-msp-kwh', 'fit-rate', 'fit-gbp'),
    'Pass Thru - UK Electricity Cost Component':
        ('meter-rental-days', 'meter-rental-rate', 'meter-rental-gbp'),
    'Meter - UK Electricity - RO Pass-Thru':
        ('ro-msp-kwh', 'ro-rate', 'ro-gbp'),
    'Meter - UK Electricity - TUoS':
        ('triad-gsp-kw', 'triad-rate', 'triad-gbp'),
    'Meter - UK Electricity - Standard': {
        'Unit Rate': {
            'Summer Weekday': (
                'summer-weekday-gsp-kwh', 'summer-weekday-rate',
                'summer-weekday-gbp'),
            'Peak': ('peak-gsp-kwh', 'peak-rate', 'peak-gbp'),
            'Peak Shoulder': (
                'peak-shoulder-gsp-kwh', 'peak-shoulder-rate',
                'peak-shoulder-gbp'),
            'Summer Night': (
                'summer-night-gsp-kwh', 'summer-night-rate',
                'summer-night-gbp'),
            'Summer Weekend & Bank Holiday': (
                'summer-weekend-gsp-kwh', 'summer-weekend-rate',
                'summer-weekend-gbp'),
            'Night': ('night-gsp-kwh', 'night-rate', 'night-gbp'),
            'Winter Weekday': (
                'winter-weekday-gsp-kwh', 'winter-weekday-rate',
                'winter-weekday-gbp'),
            'Winter Weekend & Bank Holiday': (
                'winter-weekend-gsp-kwh', 'winter-weekend-rate',
                'winter-weekend-gbp'),
            'Winter Night': (
                'winter-night-gsp-kwh', 'winter-night-rate',
                'winter-night-gbp'),
            'Day': ('day-gsp-kwh', 'day-rate', 'day-gbp'),
            'Night': ('night-gsp-kwh', 'night-rate', 'night-gbp')
        },
        'Reverse BSUoS in Unit Rate': (
            'bsuos-reverse-nbp-kwh', 'bsuos-reverse-rate',
            'bsuos-reverse-gbp')
    },
    'Meter - UK Gas - CCL': ('ccl-kwh', 'ccl-rate', 'ccl-gbp')
}


def _find_names(tree, path):
    try:
        tr = tree[path[0]]
    except KeyError:
        return None

    if isinstance(tr, tuple):
        return tr
    else:
        return _find_names(tr, path[1:])


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


def _parse_row(row, row_index, datemode, title_row):
    val = get_value(row, 'Meter Point')
    try:
        mpan_core = parse_mpan_core(str(int(val)))
    except ValueError as e:
        raise BadRequest(
            "Can't parse the MPAN core in column 'Meter Point' at row " +
            str(row_index + 1) + " with value '" + str(val) + "' : " + str(e))
    bill_period = get_value(row, 'Bill Period')
    if '-' in bill_period:
        period_start, period_finish = [
            to_utc(to_ct(Datetime.strptime(d, '%Y-%m-%d')))
            for d in bill_period.split(' - ')]
        period_finish += relativedelta(days=1) - HH
    else:
        period_start, period_finish = None, None

    from_date = get_date(row, 'From Date', datemode)
    if from_date is None:
        if period_start is None:
            raise BadRequest(
                "Can't find a bill finish date in row " + str(row_index) + ".")
        else:
            from_date = period_start

    to_date = get_date(row, 'To Date', datemode)
    if to_date is None:
        if period_finish is None:
            raise BadRequest(
                "Can't find a bill finish date in row " +
                str(row_index) + " .")
        else:
            to_date = period_finish

    else:
        to_date += relativedelta(days=1) - HH

    issue_date = get_date(row, 'Bill Date', datemode)
    bill_number = get_value(row, 'Bill Number')
    bill = {
        'bill_type_code': 'N', 'kwh': Decimal(0),
        'vat': Decimal('0.00'), 'net': Decimal('0.00'), 'reads': [],
        'breakdown': {'raw_lines': [str(title_row)]},
        'account': mpan_core, 'issue_date': issue_date,
        'start_date': from_date, 'finish_date': to_date,
        'mpans': [mpan_core],
    }
    bd = bill['breakdown']

    usage = get_dec(row, 'Usage')
    # usage_units = get_value(row, 'Usage Unit')
    price = get_dec(row, 'Price')
    amount = get_dec(row, 'Amount')
    product_item_name = get_value(row, 'Product Item Name')
    rate_name = get_value(row, 'Rate Name')
    if product_item_name == 'Renewables Obligation (RO)':
        bill['kwh'] += round(usage, 2)
    description = get_value(row, 'Description')
    product_class = get_value(row, 'Product Item Class')
    if description in ('Standard VAT@20%', 'Reduced VAT@5%'):
        bill['vat'] += round(amount, 2)
    else:
        bill['net'] += round(amount, 2)

        path = [product_class, description, rate_name]
        names = _find_names(ELEM_MAP, path)

        if names is None:
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
                    kva = int(
                        description[len(duos_excess_avail_prefix):-5])
                    bd_add(bd, 'duos-excess-availability-kva', kva)
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
            elif description.startswith("FiT Reconciliation "):
                bd_add(bd, 'fit-gbp', amount)
            elif description.startswith("CfD FiT Rec - "):
                bd_add(bd, 'cfd-fit-gbp', amount)
            elif description.startswith("Flex "):
                bd_add(bd, 'reconciliation-gbp', amount)
            elif description.startswith("Legacy TNUoS Reversal "):
                bd_add(bd, 'triad-gbp', amount)
            elif description.startswith("Hand Held Read -"):
                bd_add(bd, 'meter-rental-gbp', amount)
            elif description.startswith("RO Mutualisation "):
                bd_add(bd, 'ro-gbp', amount)
            elif description.startswith("OOC MOP - "):
                bd_add(bd, 'meter-rental-gbp', amount)
            elif description.startswith("KVa Adjustment "):
                bd_add(bd, 'duos-availability-gbp', amount)
            else:
                raise BadRequest(
                    "For the path " + str(path) +
                    " the parser can't work out the element.")
        else:
            for elem_k, elem_v in zip(names, (usage, price, amount)):
                if elem_k is not None:
                    bd_add(bd, elem_k, elem_v)

    reference = str(bill_number) + '_' + str(row_index + 1)
    for k, v in tuple(bd.items()):
        if isinstance(v, set):
            bd[k] = list(v)
        elif k.endswith("-gbp"):
            reference += "_" + k[:-4]

    bill['reference'] = reference
    bill['gross'] = bill['net'] + bill['vat']
    return bill


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
        bills = []
        title_row = self.sheet.row(0)
        for row_index in range(1, self.sheet.nrows):
            row = self.sheet.row(row_index)
            datemode = self.book.datemode
            bills.append(_parse_row(row, row_index, datemode, title_row))
        return bills
