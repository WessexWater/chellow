from decimal import Decimal
from net.sf.chellow.monad import Monad
from java.lang import System
import datetime
import csv
import pytz
from dateutil.relativedelta import relativedelta

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'BillType', 'Tpr', 'set_read_write', 'RegisterRead', 'ReadType'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH', 'validate_hh_start'],
        'templater': ['render'],
        'bill_import': ['start_bill_importer', 'get_bill_importer_ids', 'get_bill_importer'],
        'edi_lib': ['EdiParser']})

def parse_date(date_str, is_finish):
    date_str = date_str.strip()
    if len(date_str) == 10:
        dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        dt.replace(tzinfo=pytz.utc)
        if is_finish:
            dt = dt + relativedelta(days=1) - HH
        return dt
    else:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M").replace(tzinfo=pytz.utc)

class Parser():
    def __init__(self, f):
        self.reader = csv.reader(f, skipinitialspace=True)
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        iter(self.reader).next()  # skip title row
        for self.line_number, self.vals in enumerate(self.reader):
            bill_type_code = self.vals[0]
            if bill_type_code.startswith('#'):
                continue  # skip comment lines
            account = self.vals[1]
            mpan_strings = self.vals[2].split(",")
            reference = self.vals[3]
            issue_date = parse_date(self.vals[4], False)
            start_date = validate_hh_start(parse_date(self.vals[5], False))
            finish_date = validate_hh_start(parse_date(self.vals[6], True))
            
            kwh = self.big_decimal(7, 'kwh')            
            net = self.big_decimal(8, 'net')
            vat = self.big_decimal(9, 'vat')
            gross = self.big_decimal(10, 'gross')

            if len(self.vals) > 11:
                breakdown = self.vals[11].strip()
                if len(breakdown) == 0:
                    breakdown = {}
                else:
                    try:
                        breakdown = eval(breakdown)
                    except SyntaxError, e:
                        raise UserException(str(e))
            else:
                raise UserException("For the line, " + str(self.vals) + " there isn't a 'breakdown' field on the end.")

            while self.vals[-1] == '' and len(self.vals) > 12:
                del self.vals[-1]

            reads = []
            for i in range(12, len(self.vals), 11):
                tpr_str = self.vals[i + 4].strip()
                tpr_code = None if len(tpr_str) == 0 else tpr_str.zfill(5)
                reads.append({'msn': self.vals[i], 'mpan': self.vals[i + 1], 'coefficient': self.big_decimal(i + 2, 'coefficient'), 'units': self.vals[i + 3], 'tpr_code': tpr_code, 'prev_date': validate_hh_start(datetime.datetime.strptime(self.vals[i + 5], "%Y-%m-%d %H:%M")), 'prev_value': Decimal(self.vals[i + 6]), 'prev_type_code': self.vals[i + 7], 'pres_date': validate_hh_start(datetime.datetime.strptime(self.vals[i + 8], "%Y-%m-%d %H:%M")), 'pres_value': Decimal(self.vals[i + 9]), 'pres_type_code': self.vals[i + 10]})
            
            raw_bills.append({'bill_type_code': bill_type_code, 'account': account, 'mpans': mpan_strings, 'reference': reference, 'issue_date': issue_date, 'start_date': start_date, 'finish_date': finish_date, 'kwh': kwh, 'net': net, 'vat': vat, 'gross': gross, 'breakdown': breakdown, 'reads': reads})
        return raw_bills


    def big_decimal(self, bd_index, bd_name):
        try:
            bd_str = self.vals[bd_index]
            return Decimal(bd_str)
        except IndexError:
            raise UserException("The field '" + bd_name + "' can't be found. It's expected at position " + str(bd_index) + " in the list of fields.")
        except NumberFormatException:
            raise UserException("The " + bd_name + " field '" + bd_str + "' cannot be parsed as a number. The " + bd_name + " field is the " + str(bd_index) + " field of " + str(self.vals) + ".")