from decimal import Decimal
from net.sf.chellow.monad import Monad
from java.lang import System
import datetime
import csv
from dateutil.relativedelta import relativedelta
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'BillType', 'Tpr', 'set_read_write', 'RegisterRead', 'ReadType'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH', 'validate_hh_start'],
        'templater': ['render'],
        'bill_import': ['start_bill_importer', 'get_bill_importer_ids', 'get_bill_importer'],
        'edi_lib': ['EdiParser']})

col_map = {9: 'sum-gsp-kwh', 17: 'aahedc-rate', 18: 'aahedc-gsp-kwh', 19: 'aahedc-gbp', 20: 'fit-previous-actual-rate', 21: 'fit-previous-actual-msp-kwh', 22: 'fit-previous-actual-gbp', 23: 'duos-availability-rate', 24: 'duos-availability-kva', 25: 'duos-availability-gbp', 26: 'bsuos-actual-gsp-kwh', 27: 'bsuos-actual-gbp-info', 28: 'peak-rate', 29: 'peak-gsp-kwh', 30: 'peak-gbp', 31: 'peak-shoulder-rate', 32: 'peak-shoulder-gsp-kwh', 33: 'peak-shoulder-gbp', 34: 'summer-night-rate', 35: 'summer-night-gsp-kwh', 36: 'summer-night-gbp', 37: 'summer-weekday-rate', 38: 'summer-weekday-gsp-kwh', 39: 'summer-weekday-gbp', 40: 'summer-weekend-rate', 41: 'summer-weekend-gsp-kwh', 42: 'summer-weekend-gbp', 43: 'winter-night-rate', 44: 'winter-night-gsp-kwh', 45: 'winter-night-gbp', 46: 'winter-weekday-rate', 47: 'winter-weekday-gsp-kwh', 48: 'winter-weekday-gbp', 49: 'winter-weekend-rate', 50: 'winter-weekend-gsp-kwh', 51: 'winter-weekend-gbp', 52: 'fit-estimate-rate', 53: 'fit-estimate-msp-kwh', 54: 'fit-estimate-gbp', 55: 'duos-excess-availability-rate', 56: 'duos-excess-availability-kva', 57: 'duos-excess-availability-gbp', 60: 'duos-fixed-gbp', 61: 'lec-rate', 62: 'lec-kwh', 63: 'lec-gbp', 67: 'triad-estimate-gsp-kw', 68: 'triad-estimate-rate', 69: 'triad-estimate-gbp', 70: 'duos-red-rate', 71: 'duos-red-kwh', 72: 'duos-red-gbp', 73: 'duos-amber-rate', 74: 'duos-amber-kwh', 75: 'duos-amber-gbp', 76: 'duos-green-rate', 77: 'duos-green-kwh', 78: 'duos-green-gbp', 79: 'duos-reactive-rate', 80: 'duos-reactive-kvarh', 81: 'duos-reactive-gbp', 92: 'reconciliation-gbp', 93: 'reconciliation-gbp', 94: 'bsuos-gbp', 97: 'fit-total'}

TITLES = "Customer Name,Customer Address,Cust PC,Bill Ref No.,Invoice No.,Invoice Date,Bill Period Start,Bill Period End,Site Data,Gsp Data,Max kVA,Avg Pwr Factor,Max Pwr Factor,Min Power Factor,Max DMD Date,MX DMD,Mpan,AAHEDC Charge Price,AAHEDC Charge Units,AAHEDC Charge Charge,Actual FiT Charge Price,Actual FiT Charge Units,Actual FiT Charge Charge,Availability Charges Price,Availability Charges Units,Availability Charges Charge,BSUoS Actual Charge (Date) Units,BSUoS Actual Charge (Date) Charge,Energy Peak Price,Energy Peak Units,Energy Peak Charge,Energy Peak Shoulder Price,Energy Peak Shoulder Units,Energy Peak Shoulder Charge,Energy Summer Night Price,Energy Summer Night Units,Energy Summer Night Charge,Energy Summer Weekday Price,Energy Summer Weekday Units,Energy Summer Weekday Charge,Energy Summer Weekend Price,Energy Summer Weekend Units,Energy Summer Weekend Charge,Energy Winter Night Price,Energy Winter Night Units,Energy Winter Night Charge,Energy Winter Weekday Price,Energy Winter Weekday Units,Energy Winter Weekday Charge,Energy Winter Weekend Price,Energy Winter Weekend Units,Energy Winter Weekend Charge,Estimated FiT Charge Price,Estimated FiT Charge Units,Estimated FiT Charge Charge,Excess Availability Charges Price,Excess Availability Charges Units,Excess Availability Charges Charge,Fixed Charges Price,Fixed Charges Units,Fixed Charges Charge,Levy Exempt Energy Price,Levy Exempt Energy Units,Levy Exempt Energy Charge,Meter Reading Charges Price,Meter Reading Charges Units,Meter Reading Charges Charge,Network UoS Charges Price,Network UoS Charges Units,Network UoS Charges Charge,Rate 1 Price,Rate 1 Units,Rate 1 Charge,Rate 2 Price,Rate 2 Units,Rate 2 Charge,Rate 3 Price,Rate 3 Units,Rate 3 Charge,Reactive Power Charge Price,Reactive Power Charge Units,Reactive Power Charge Charge,VAT @ 0% Price,VAT @ 0% Units,VAT @ 0% Charge,VAT @ STD Price,VAT @ STD Units,VAT @ STD Charge,VAT @ 5% Price,VAT @ 5% Units,VAT @ 5% Charge,ADDTTL,AHC_NRG1,AHC_TTL,BSUOSTTL,DUOSTTL,DUOS_UNITTL,FiT_TTL,LEETTL,NET_AMT,NRGTTL,NRGTTL_HH,SUBTTL,TTLCHG,TUSTTL,VATTTL,GDF REG NO.,REG VAT NO"


class Parser():
    def __init__(self, f):
        self.last_line = None
        lines = (self._set_last_line(l) for l in f)
        self.reader = csv.reader(lines, skipinitialspace=True)
        self._line_number = None

    @property
    def line_number(self):
        return None if self._line_number is None else self._line_number + 2

    def _set_last_line(self, line):
        self.last_line = line
        return line

    def make_raw_bills(self):
        iter(self.reader).next()  # skip title row
        raw_bills = []

        for self._line_number, vals in enumerate(self.reader):
            if len(vals) == 0 or vals[0].startswith('#'):
                continue
            mpan_strings = [vals[16][1:]]
            issue_date = datetime.datetime.strptime(vals[5], "%d/%m/%Y").replace(tzinfo=pytz.utc)
            bill_from = validate_hh_start(datetime.datetime.strptime(vals[6], "%d/%m/%Y").replace(tzinfo=pytz.utc))
            bill_to = validate_hh_start(datetime.datetime.strptime(vals[7], "%d/%m/%Y").replace(tzinfo=pytz.utc)) + relativedelta(days=1) - HH
            kwh = Decimal(vals[8])
            breakdown = dict([(v, float(vals[k])) for k, v in col_map.iteritems()])
            breakdown['raw-lines'] = [TITLES, self.last_line]
            net = Decimal(vals[99])
            vat = Decimal(vals[105])
            gross = Decimal(vals[103])
            raw_bills.append({'bill_type_code': 'N', 'account': vals[3], 'mpans': [], 'reference': vals[4], 'issue_date': issue_date, 'start_date': bill_from, 'finish_date': bill_to, 'kwh': kwh, 'net': net, 'vat': vat, 'gross': gross, 'breakdown': breakdown, 'reads': []})
        return raw_bills