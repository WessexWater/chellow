from decimal import Decimal
from datetime import datetime as Datetime
import csv
from dateutil.relativedelta import relativedelta
from werkzeug.exceptions import BadRequest
from chellow.utils import validate_hh_start, HH, to_utc, parse_mpan_core
from io import StringIO


col_map = {
    'Gsp Data': 'sum-gsp-kwh',
    'Levy Exempt Energy Units': 'lec-kwh',
    'Levy Exempt Energy Price': 'lec-rate',
    'Levy Exempt Energy Charge': 'lec-gbp',
    'Meter Reading Charges Charge': 'meter-reading-gbp',
    'Availability Charges Units': 'duos-availability-kva',
    'Availability Charges Price': 'duos-availability-rate',
    'Availability Charges Charge': 'duos-availability-gbp',
    'Excess Availability Charges Units': 'duos-excess-availability-kva',
    'Excess Availability Charges Price': 'duos-excess-availability-rate',
    'Excess Availability Charges Charge': 'duos-excess-availability-gbp',
    'Fixed Charges Units': 'duos-fixed-days',
    'Fixed Charges Price': 'duos-fixed-rate',
    'Fixed Charges Charge': 'duos-fixed-gbp',
    'Rate 1 Units': 'duos-red-kwh',
    'Rate 1 Price': 'duos-red-rate',
    'Rate 1 Charge': 'duos-red-gbp',
    'Rate 2 Units': 'duos-amber-kwh',
    'Rate 2 Price': 'duos-amber-rate',
    'Rate 2 Charge': 'duos-amber-gbp',
    'Rate 3 Units': 'duos-green-kwh',
    'Rate 3 Price': 'duos-green-rate',
    'Rate 3 Charge': 'duos-green-gbp',
    'Reactive Power Charge Units': 'duos-reactive-kvarh',
    'Reactive Power Charge Price': 'duos-reactive-rate',
    'Reactive Power Charge Charge': 'duos-reactive-gbp',
    'BSUoS Actual Charge (Date) Charge': 'bsuos-actual-gbp-info',
    'BSUOSTTL': 'bsuos-gbp',
    'AAHEDC Charge Units': 'aahedc-gsp-kwh',
    'AAHEDC Charge Price': 'aahedc-rate',
    'AAHEDC Charge Charge': 'aahedc-gbp',
    'RO Adjustment Units': 'ro-msp-kwh',
    'RO Adjustment Price': 'ro-rate',
    'RO Adjustment Charge': 'ro-gbp',
    'Estimated FiT Charge Units': 'fit-estimate-msp-kwh',
    'Estimated FiT Charge Price': 'fit-estimate-rate',
    'Estimated FiT Charge Charge': 'fit-estimate-gbp',
    'Actual FiT Charge Price': 'fit-previous-actual-rate',
    'Actual FiT Charge Charge': 'fit-previous-actual-gbp',
    'Estimated CfD Charge Units': 'cfd-fit-estimate-nbp-kwh',
    'Estimated CfD Charge Price': 'cfd-fit-estimate-rate',
    'Estimated CfD Charge Charge': 'cfd-fit-estimate-gbp',
    'Actual CfD Charge Units': 'cfd-fit-previous-actual-nbp-kwh',
    'Actual CfD Charge Price': 'cfd-fit-previous-actual-rate',
    'Actual CfD Charge Charge': 'cfd-fit-previous-actual-gbp',
    'CFD_Total': 'cfd-fit-total',
    'AHC_NRG1': 'reconciliation-gbp',
    'Energy Peak Units': 'peak-gsp-kwh',
    'Energy Peak Price': 'peak-rate',
    'Energy Peak Charge': 'peak-gbp',
    'Energy Peak Shoulder Units': 'peak-shoulder-gsp-kwh',
    'Energy Peak Shoulder Price': 'peak-shoulder-rate',
    'Energy Peak Shoulder Charge': 'peak-shoulder-gbp',
    'Energy Summer Night Units': 'summer-night-gsp-kwh',
    'Energy Summer Night Price': 'summer-night-rate',
    'Energy Summer Night Charge': 'summer-night-gbp',
    'Energy Summer Weekday Units': 'summer-weekday-gsp-kwh',
    'Energy Summer Weekday Price': 'summer-weekday-rate',
    'Energy Summer Weekday Charge': 'summer-weekday-gbp',
    'Energy Summer Weekend Units': 'summer-weekend-gsp-kwh',
    'Energy Summer Weekend Price': 'summer-weekend-rate',
    'Energy Summer Weekend Charge': 'summer-weekend-gbp',
    'Energy Winter Night Units': 'winter-night-gsp-kwh',
    'Energy Winter Night Price': 'winter-night-rate',
    'Energy Winter Night Charge': 'winter-night-gbp',
    'Energy Winter Weekday Units': 'winter-weekday-gsp-kwh',
    'Energy Winter Weekday Price': 'winter-weekday-rate',
    'Energy Winter Weekday Charge': 'winter-weekday-gbp',
    'Energy Winter Weekend Units': 'winter-weekend-gsp-kwh',
    'Energy Winter Weekend Price': 'winter-weekend-rate',
    'Energy Winter Weekend Charge': 'winter-weekend-gbp',
    'Network UoS Charges Price': 'triad-estimate-rate',
    'Network UoS Charges Units': 'triad-estimate-gsp-kw',
    'Network UoS Charges Charge': 'triad-estimate-gbp',
    'CAP_M_TTL': 'capacity-market-gbp'
}


class Parser():
    def __init__(self, f):
        self.last_line = None
        tf = StringIO(str(f.read(), 'utf-8', errors='ignore'))
        lines = (self._set_last_line(i, l) for i, l in enumerate(tf))
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
        titles = [t.strip() for t in next(iter(self.reader))]
        title_idx = dict((title, i) for i, title in enumerate(titles))

        raw_bills = []

        for vals in self.reader:
            if len(vals) == 0 or vals[0].startswith('#') or \
                    ''.join(vals) == '':
                continue

            def val(title):
                idx = title_idx[title]
                try:
                    return vals[idx]
                except KeyError:
                    raise BadRequest(
                        "For title " + title + " and index " + str(idx))

            def date_val(title):
                try:
                    return to_utc(Datetime.strptime(val(title), "%d/%m/%Y"))
                except ValueError as e:
                    raise BadRequest(
                        "At line number " + str(self._line_number) +
                        ", while trying to find the value of " + title +
                        " the date couldn't be parsed. " + str(e) +
                        " The full line is " + self.last_line)

            def dec_val(title):
                return Decimal(val(title))

            issue_date = date_val('Invoice Date')
            bill_from = validate_hh_start(date_val('Bill Period Start'))
            bill_to = validate_hh_start(date_val('Bill Period End')) + \
                relativedelta(days=1) - HH
            kwh = dec_val('Site Data')
            breakdown = dict(
                [(v, dec_val(k)) for k, v in col_map.items() if k in titles])
            breakdown['raw_lines'] = [
                self._title_line.strip(), self.last_line.strip()]
            net = Decimal('0.00') + dec_val('NET_AMT')
            vat = Decimal('0.00') + dec_val('VATTTL')
            gross = Decimal('0.00') + dec_val('TTLCHG')
            mpan_core = parse_mpan_core(val('Mpan'))
            raw_bill = {
                'bill_type_code': 'N', 'account': val('Bill Ref No.'),
                'mpan_core': mpan_core, 'reference': val('Invoice No.'),
                'issue_date': issue_date, 'start_date': bill_from,
                'finish_date': bill_to, 'kwh': kwh, 'net': net, 'vat': vat,
                'gross': gross, 'breakdown': breakdown, 'reads': []
            }
            raw_bills.append(raw_bill)

        return raw_bills
