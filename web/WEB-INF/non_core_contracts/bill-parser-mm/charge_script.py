from decimal import Decimal
from net.sf.chellow.monad import Monad
import datetime

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'bill_import')
validate_hh_start = utils.validate_hh_start

def parse_date(date_string):
    return validate_hh_start(datetime.datetime.strptime(date_string, "%Y%m%d"))


class Parser():
    def __init__(self, f):
        self.f = f
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        for i, line in enumerate(self.f):
            self.line_number = i
            record_type = line[62:66]
            if record_type == "0100":
                account = line[33:41]
                reference = line[41:46]
                start_date = None
                finish_date = None
                net = Decimal(0)
                vat = Decimal(0)
                mpan_strings = []
            elif record_type == "1460":
                net += Decimal(line[67:79]) / Decimal(100)
                vat += Decimal(line[85:97]) / Decimal(100)
            elif record_type == "0461":
                mpan_str = line[148:156] + line[135:148]
                if mpan_str not in mpan_strings:
                    mpan_strings.append(mpan_str)
            elif record_type == "0101":
                start_date = parse_date(line[66:74])
                finish_date = parse_date(line[74:82])
            elif record_type == "1500":
                raw_bills.append(
                    {
                        'bill_type_code': 'N', 'account': account,
                        'mpan_strings': mpan_strings, 'reference': reference,
                        'issue_date': start_date, 'start_date': start_date,
                        'finish_date': finish_date, 'kwh': Decimal(0),
                        'net': net, 'vat': vat, 'gross': Decimal(0),
                        'breakdown': {}, 'reads': []})

        return raw_bills
