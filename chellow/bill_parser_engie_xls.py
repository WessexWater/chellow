from decimal import Decimal
from datetime import datetime as Datetime
import csv
import pytz
from chellow.utils import parse_mpan_core, HH
from itertools import count
from xlrd import xldate_as_tuple, open_workbook
from dateutil.relativedelta import relativedelta


ELEM_MAP = {
    ('Assistance for Areas with High Electricity Distribution Costs (AAHEDC)',
        '', 'Usage'): 'aahedc-gsp-kwh',
    ('Assistance for Areas with High Electricity Distribution Costs (AAHEDC)',
        '', 'Price'): 'aahedc-rate',
    ('Assistance for Areas with High Electricity Distribution Costs (AAHEDC)',
        '', 'Amount'): 'aahedc-gbp',
    ('Capacity Market (Estimate)', '', 'Amount'): 'capacity-market-gbp',
    ('CfD FiT (Actual)', '', 'Usage'): 'cfd-fit-prev-actual-nbp-kwh',
    ('CfD FiT (Actual)', '', 'Price'): 'cfd-fit-prev-actual-rate',
    ('CfD FiT (Actual)', '', 'Amount'): 'cfd-fit-prev-actual-gbp',
    ('CfD FiT (Estimate)', '', 'Usage'): 'cfd-fit-estimate-nbp-kwh',
    ('CfD FiT (Estimate)', '', 'Price'): 'cfd-fit-estimate-rate',
    ('CfD FiT (Estimate)', '', 'Amount'): 'cfd-fit-estimate-gbp',
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
    ('Feed in Tariff (FiT)', '', 'Usage'): 'fit-estimate-msp-kwh',
    ('Feed in Tariff (FiT)', '', 'Price'): 'fit-estimate-rate',
    ('Feed in Tariff (FiT)', '', 'Amount'): 'fit-estimate-gbp',
    ('Feed in Tariff (FiT) Actual', '', 'Usage'): 'fit-prev-actual-msp-kwh',
    ('Feed in Tariff (FiT) Actual', '', 'Price'): 'fit-prev-actual-rate',
    ('Feed in Tariff (FiT) Actual', '', 'Amount'): 'fit-prev-actual-gbp',
    ('Feed in Tariff (FiT) Estimate', '', 'Usage'):
        'fit-prev-estimate-msp-kwh',
    ('Feed in Tariff (FiT) Estimate', '', 'Price'): 'fit-prev-estimate-rate',
    ('Feed in Tariff (FiT) Estimate', '', 'Amount'): 'fit-prev-estimate-gbp',
    ('Meter Rental', '', 'Usage'): 'meter-rental-days',
    ('Meter Rental', '', 'Price'): 'meter-rental-rate',
    ('Meter Rental', '', 'Amount'): 'meter-rental-gbp',
    ('Renewables Obligation (RO)', '', 'Usage'): 'ro-msp-kwh',
    ('Renewables Obligation (RO)', '', 'Price'): 'ro-rate',
    ('Renewables Obligation (RO)', '', 'Amount'): 'ro-gbp',
    ('TNUoS (Estimated)', '', 'Usage'): 'triad-estimate-gsp-kw',
    ('TNUoS (Estimated)', '', 'Price'): 'triad-estimate-rate',
    ('TNUoS (Estimated)', '', 'Amount'): 'triad-estimate-gbp',
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
    ('Unit Rate', 'Summer Weekend', 'Usage'): 'summer-weekend-gsp-kwh',
    ('Unit Rate', 'Summer Weekend', 'Price'): 'summer-weekend-rate',
    ('Unit Rate', 'Summer Weekend', 'Amount'): 'summer-weekend-gbp',
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
    ('Reverse CfD FiT (Estimate)', '', 'Usage'):
        'cfd-fit-prev-estimate-nbp-kwh',
    ('Reverse CfD FiT (Estimate)', '', 'Price'): 'cfd-fit-prev-estimate-rate',
    ('Reverse CfD FiT (Estimate)', '', 'Amount'): 'cfd-fit-prev-estimate-gbp'}


CT_TZ = pytz.timezone('Europe/London')


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
    if val == '':
        return None
    else:
        dt_raw = Datetime(*xldate_as_tuple(get_value(row, name), datemode))
        dt_ct = CT_TZ.localize(dt_raw)
        return pytz.utc.normalize(dt_ct.astimezone(pytz.utc))


def get_value(row, name):
    val = row[COLUMN_MAP[name]].value
    if isinstance(val, str):
        return val.strip()
    else:
        return val


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
        raw_bills = []
        last_key = None
        title_row = self.sheet.row(0)
        for row_index in range(1, self.sheet.nrows):
            row = self.sheet.row(row_index)
            mpan_core = parse_mpan_core(
                str(int(get_value(row, 'Meter Point'))))
            bill_period = get_value(row, 'Bill Period')
            start_date, finish_date = [
                pytz.utc.normalize(
                    CT_TZ.localize(
                        Datetime.strptime(d, '%Y-%m-%d')).astimezone(pytz.utc))
                for d in bill_period.split(' - ')]
            finish_date = finish_date + relativedelta(days=1) - HH
            key = (start_date, finish_date, mpan_core)
            from_date = get_date(row, 'From Date', self.book.datemode)
            # to_date = get_date(row, 'To Date', self.book.datemode) + \
            #    relativedelta(days=1) - HH
            issue_date = get_date(row, 'Bill Date', self.book.datemode)
            if last_key != key:
                last_key = key

                bd = {}
                bill = {
                    'bill_type_code': 'N', 'account': mpan_core,
                    'mpans': [mpan_core],
                    'reference': '_'.join(
                        (
                            start_date.strftime('%Y%m%d'),
                            finish_date.strftime('%Y%m%d'), mpan_core)),
                    'issue_date': issue_date, 'start_date': start_date,
                    'finish_date': finish_date, 'kwh': Decimal(0),
                    'net': Decimal('0'), 'vat': Decimal('0'),
                    'breakdown': bd, 'reads': []}
                raw_bills.append(bill)

            usage = get_value(row, 'Usage')
            usage_units = get_value(row, 'Usage Unit')
            price = get_value(row, 'Price')
            amount = get_value(row, 'Amount')
            amount_dec = Decimal(amount)
            product_item_name = get_value(row, 'Product Item Name')
            rate_name = get_value(row, 'Rate Name')
            if usage_units == 'kWh' and \
                    product_item_name == 'Renewables Obligation (RO)':
                bill['kwh'] += round(Decimal(usage), 2)
            description = get_value(row, 'Description')
            if description == 'Standard VAT@20%':
                bill['vat'] = round(amount_dec, 2)
            else:
                bill['net'] += round(amount_dec, 2)

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
            elif description == 'Balancing Services Use of System (BSUoS)':
                if from_date == start_date:
                    bd_add(bd, 'bsuos-estimated-nbp-kwh', usage)
                    bd_add(bd, 'bsuos-estimated-rate', price)
                    bd_add(bd, 'bsuos-estimated-gbp', amount)
                elif amount < 0:
                    bd_add(bd, 'bsuos-prev-estimated-nbp-kwh', usage)
                    bd_add(bd, 'bsuos-prev-estimated-rate', price)
                    bd_add(bd, 'bsuos-prev-estimated-gbp', amount)
                else:
                    bd_add(bd, 'bsuos-prev-sf-nbp-kwh', usage)
                    bd_add(bd, 'bsuos-prev-sf-rate', price)
                    bd_add(bd, 'bsuos-prev-sf-gbp', amount)
            elif description.startswith("FiT Rec - "):
                bd_add(bd, 'fit-reconciliation-gbp', amount)
            elif description.startswith("CfD FiT Rec - "):
                bd_add(bd, 'cfd-fit-reconciliation-gbp', amount)

            bd['raw_lines'] = [str(title_row), str(row)]
            bill['gross'] = bill['net'] + bill['vat']

        for raw_bill in raw_bills:
            bd = raw_bill['breakdown']
            for k, v in tuple(bd.items()):
                if isinstance(v, set):
                    val = ', '.join(sorted(map(str, v)))
                else:
                    val = v
                bd[k] = val

        return raw_bills
