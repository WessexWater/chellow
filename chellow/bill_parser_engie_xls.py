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
    None: None,
    'Charge - Recurring': {
        None: ('duos-fixed-gbp', 'duos-fixed-rate', 'duos-fixed-days')
    },
    'Meter - UK Electricity - AAHEDC Pass-Thru': {
        None: ['aahedc-gbp', 'aahedc-rate', 'aahedc-gsp-kwh']
    },
    'Meter - UK Electricity - BSUoS Pass-Thru': {
        None: ['bsuos-gbp', 'bsuos-rate', 'bsuos-nbp-kwh']
    },
    'Meter - UK Electricity - Capacity Market Pass-Thru': {
        None: ['capacity-gbp', 'capacity-rate', 'capacity-kwh'],
        'Reverse Capacity Market Estimate': {
            None: ['capacity-gbp']
        }
    },
    'Meter - UK Electricity - CfD FiT Pass-Thru': {
        None: ['cfd-fit-gbp', 'cfd-fit-rate', 'cfd-fit-nbp-kwh']
    },
    'Meter - UK Electricity - CCL': {
        None: ['ccl-gbp', 'ccl-rate', 'ccl-kwh'],
        'CCL': {
            None: ['ccl-gbp', 'ccl-rate', 'ccl-kwh']
        },
        'Levy Exempt Energy': {
            None: ['lec-gbp', 'lec-rate', 'lec-kwh']
        }
    },
    'Meter - UK Electricity - DUoS': {
        None: None,
        'DUoS Unit Charge 3': {
            None: ('duos-green-gbp', 'duos-green-rate', 'duos-green-kwh')
        },
        'DUoS Unit Charge 2': {
            None: ('duos-amber-gbp', 'duos-amber-rate', 'duos-amber-kwh')
        },
        'DUoS Unit Rate 2': {
            None: ('duos-amber-gbp', 'duos-amber-rate', 'duos-amber-kwh')
        },
        'DUoS Unit Charge 1': {
            None: ('duos-red-gbp', 'duos-red-kwh', 'duos-red-rate')
        },
        'DUoS Unit Rate 1': {
            None: ('duos-red-gbp', 'duos-red-kwh', 'duos-red-rate')
        },
        'DUoS Standing Charge': {
            None: ('duos-fixed-gbp', 'duos-fixed-rate', 'duos-fixed-days')
        },
        'DUoS Fixed': {
            None: ('duos-fixed-gbp', 'duos-fixed-rate', 'duos-fixed-days')
        },
        'DUoS Reactive': {
            None: (
                'duos-reactive-gbp', 'duos-reactive-rate',
                'duos-reactive-kvarh')
        }
    },
    'Meter - UK Electricity - FiT Pass-Thru': {
        None: ('fit-gbp', 'fit-rate', 'fit-msp-kwh')
    },
    'Pass Thru - UK Electricity Cost Component': {
        None: ('meter-rental-gbp', 'meter-rental-rate', 'meter-rental-days')
    },
    'Meter - UK Electricity - RO Pass-Thru': {
        None: ('ro-gbp', 'ro-rate', 'ro-msp-kwh')
    },
    'Meter - UK Electricity - TUoS': {
        None: ('triad-gbp', 'triad-rate', 'triad-gsp-kw')
    },
    'Meter - UK Electricity - Standard': {
        None: None,
        'Unit Rate': {
            'Summer Weekday': {
                None: (
                    'summer-weekday-gbp', 'summer-weekday-rate',
                    'summer-weekday-gsp-kwh')
            },
            'Peak': {
                None: ('peak-gbp', 'peak-rate', 'peak-gsp-kwh')
            },
            'Peak Shoulder': {
                None: (
                    'peak-shoulder-gbp', 'peak-shoulder-gsp-kwh',
                    'peak-shoulder-rate')
            },
            'Summer Night': {
                None: (
                    'summer-night-gbp', 'summer-night-rate',
                    'summer-night-gsp-kwh')
            },
            'Summer Weekend & Bank Holiday': {
                None: (
                    'summer-weekend-gbp', 'summer-weekend-rate',
                    'summer-weekend-gsp-kwh')
            },
            'Night': {
                None: ('night-gbp', 'night-rate', 'night-gsp-kwh')
            },
            'Winter Weekday': {
                None: (
                    'winter-weekday-gbp', 'winter-weekday-rate',
                    'winter-weekday-gsp-kwh')
            },
            'Winter Weekend & Bank Holiday': {
                None: (
                    'winter-weekend-gbp', 'winter-weekend-rate',
                    'winter-weekend-gsp-kwh')
            },
            'Winter Night': {
                None: (
                    'winter-night-gbp', 'winter-night-rate',
                    'winter-night-gsp-kwh')
            },
            'Day': {
                None: ('day-gbp', 'day-rate', 'day-gsp-kwh')
            },
            'Single': {
                None: ('day-gbp', 'day-rate', 'day-gsp-kwh')
            },
            'Off Peak / Weekends': {
                None: ('day-gbp', 'day-rate', 'day-gsp-kwh')
            },
        },
        'Reverse BSUoS in Unit Rate': {
            None: (
                'bsuos-reverse-gbp', 'bsuos-reverse-rate',
                'bsuos-reverse-nbp-kwh')
        }
    },
    'Meter - UK Gas - CCL': {
        None: ('ccl-gbp', 'ccl-rate', 'ccl-kwh')
    }
}


def _find_names(tree, path):
    if len(path) > 0:
        try:
            return _find_names(tree[path[0]], path[1:])
        except KeyError:
            pass

    return tree[None]


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
    dt = get_date_naive(row, name, datemode)
    return dt if dt is None else to_utc(to_ct(dt))


def get_date_naive(row, name, datemode):
    val = get_value(row, name)
    if isinstance(val, float):
        return Datetime(*xldate_as_tuple(val, datemode))
    else:
        return None


def get_value(row, name):
    idx = COLUMN_MAP[name]
    try:
        val = row[idx].value
    except IndexError:
        raise BadRequest(
            "For the name '" + name + "', the index is " + str(idx) +
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


def _bd_add(bd, el_name, val):
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
            raise BadRequest(
                "Problem with element name " + el_name + " and value '" +
                str(val) + "': " + str(e))


def _parse_row(row, row_index, datemode, title_row):
    val = get_value(row, 'Meter Point')
    try:
        mpan_core = parse_mpan_core(str(int(val)))
    except ValueError as e:
        raise BadRequest(
            "Can't parse the MPAN core in column 'Meter Point' with value '" +
            str(val) + "' : " + str(e))

    bill_period = get_value(row, 'Bill Period')
    if '-' in bill_period:
        period_start_naive, period_finish_naive = [
            Datetime.strptime(v, '%Y-%m-%d') for v in bill_period.split(' - ')]
        period_start = to_utc(to_ct(period_start_naive))
        period_finish = to_utc(
            to_ct(period_finish_naive + relativedelta(days=1) - HH))
    else:
        period_start, period_finish = None, None

    from_date = get_date(row, 'From Date', datemode)
    if from_date is None:
        if period_start is None:
            raise BadRequest("Can't find a bill start date.")
        else:
            from_date = period_start

    to_date_naive = get_date_naive(row, 'To Date', datemode)
    if to_date_naive is None:
        if period_finish is None:
            raise BadRequest("Can't find a bill finish date.")
        else:
            to_date = period_finish

    else:
        to_date = to_utc(to_ct(to_date_naive + relativedelta(days=1) - HH))

    issue_date = get_date(row, 'Bill Date', datemode)
    bill_number = get_value(row, 'Bill Number')
    bill = {
        'bill_type_code': 'N', 'kwh': Decimal(0),
        'vat': Decimal('0.00'), 'net': Decimal('0.00'), 'reads': [],
        'breakdown': {'raw_lines': [str(title_row)]},
        'account': mpan_core, 'issue_date': issue_date,
        'start_date': from_date, 'finish_date': to_date,
        'mpan_core': mpan_core,
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

        duos_avail_prefix = "DUoS Availability ("
        duos_excess_avail_prefix = "DUoS Excess Availability ("

        if description.startswith("DUoS Availability Adjustment "):
            _bd_add(bd, 'duos-availability-gbp', amount)
        elif description.startswith("DUoS Availability"):
            if description.startswith(duos_avail_prefix):
                _bd_add(
                    bd, 'duos-availability-kva',
                    int(description[len(duos_avail_prefix):-5]))
            _bd_add(bd, 'duos-availability-days', usage)
            _bd_add(bd, 'duos-availability-rate', price)
            _bd_add(bd, 'duos-availability-gbp', amount)
        elif description.startswith("DUoS Excess Availability"):
            if description.startswith(duos_excess_avail_prefix):
                kva = int(
                    description[len(duos_excess_avail_prefix):-5])
                _bd_add(bd, 'duos-excess-availability-kva', kva)
            _bd_add(bd, 'duos-excess-availability-days', usage)
            _bd_add(bd, 'duos-excess-availability-rate', price)
            _bd_add(bd, 'duos-excess-availability-gbp', amount)
        elif description.startswith('BSUoS Black Start '):
            _bd_add(bd, 'black-start-gbp', amount)
        elif description.startswith('BSUoS Reconciliation - '):
            if usage is not None:
                _bd_add(bd, 'bsuos-nbp-kwh', usage)
            if price is not None:
                _bd_add(bd, 'bsuos-rate', price)
            _bd_add(bd, 'bsuos-gbp', amount)
        elif description.startswith("FiT Rec - "):
            _bd_add(bd, 'fit-gbp', amount)
        elif description.startswith("FiT Reconciliation "):
            _bd_add(bd, 'fit-gbp', amount)
        elif description.startswith("CfD FiT Rec - "):
            _bd_add(bd, 'cfd-fit-gbp', amount)
        elif description.startswith("Flex"):
            _bd_add(bd, 'reconciliation-gbp', amount)
        elif description.startswith("Legacy TNUoS Reversal "):
            _bd_add(bd, 'triad-gbp', amount)
        elif description.startswith("Hand Held Read -"):
            _bd_add(bd, 'meter-rental-gbp', amount)
        elif description.startswith("RO Mutualisation "):
            _bd_add(bd, 'ro-gbp', amount)
        elif description.startswith("OOC MOP - "):
            _bd_add(bd, 'meter-rental-gbp', amount)
        elif description.startswith("KVa Adjustment "):
            _bd_add(bd, 'duos-availability-gbp', amount)
        elif names is not None:
            for elem_k, elem_v in zip(names, (amount, price, usage)):
                if elem_k is not None:
                    _bd_add(bd, elem_k, elem_v)
        else:
            raise BadRequest(
                "For the path " + str(path) +
                " the parser can't work out the element.")

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
            try:
                bills.append(_parse_row(row, row_index, datemode, title_row))
            except BadRequest as e:
                raise BadRequest(
                    "On row " + str(row_index + 1) + ": " + str(e.description))
        return bills
