from decimal import Decimal
import chellow.edi_lib
from chellow.utils import hh_after
from io import StringIO

read_type_map = {
    '00': 'N', '01': 'E', '02': 'E', '04': 'C', '06': 'X', '07': 'N'}


class Parser():
    def __init__(self, f):
        self.parser = chellow.edi_lib.EdiParser(
            StringIO(str(f.read(), 'utf-8', errors='ignore')))
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        for self.line_number, code in enumerate(self.parser):
            if code == "CLO":
                cloc = self.parser.elements[0]
                account = cloc[1]
            elif code == "BCD":
                ivdt = self.parser.elements[0]
                invn = self.parser.elements[2]
                btcd = self.parser.elements[5]

                reference = invn[0]
                bill_type_code = btcd[0]
                issue_date = self.parser.to_date(ivdt[0])
            elif code == "MHD":
                typ = self.parser.elements[1]
                message_type = typ[0]
                if message_type == "UTLBIL":
                    issue_date = None
                    start_date = None
                    finish_date = None
                    account = None
                    reference = None
                    net = Decimal(0.00)
                    vat = Decimal(0.00)
                    reads = []
                    mpan_strings = []
            elif code == "CCD":
                ccde = self.parser.elements[1]
                consumption_charge_indicator = ccde[0]
                charge_type = ccde[2]
                if consumption_charge_indicator != "5" and \
                        charge_type in ["7", "8", "9"]:
                    prev_read_date = self.parser.to_date(
                        self.parser.elements[7][0])
                if hh_after(start_date, prev_read_date):
                    start_date = prev_read_date
                register_finish_date = self.parser.to_date(
                    self.parser.elements[6][0])
                if finish_date is None or finish_date < register_finish_date:
                    finish_date = register_finish_date
                if charge_type == "7":
                    tmod = self.parser.elements[3]
                    mtnr = self.parser.elements[4]
                    mloc = self.parser.elements[5]
                    prrd = self.parser.elements[9]
                    adjf = self.parser.elements[12]
                    pres_read_type = read_type_map[prrd[1]]
                    prev_read_type = read_type_map[prrd[3]]
                    coefficient = Decimal(adjf[1]) / Decimal(100000)
                    pres_read_value = Decimal(prrd[0]) / Decimal(1000)
                    prev_read_value = Decimal(prrd[2]) / Decimal(1000)
                    msn = mtnr[0]
                    tpr_code = tmod[0].zfill(5)
                    reads.append(
                        {
                            'msn': msn, 'mpan': mloc[0],
                            'coefficient': coefficient, 'units': 'kWh',
                            'tpr_code': tpr_code, 'prev_date': prev_read_date,
                            'prev_value': prev_read_value,
                            'prev_type_code': prev_read_type,
                            'pres_date': register_finish_date,
                            'pres_value': pres_read_value,
                            'pres_type_code': pres_read_type})
            elif code == "MTR":
                if message_type == "UTLBIL":
                    raw_bills.append(
                        {
                            'bill_type_code': bill_type_code,
                            'account': account, 'mpans': mpan_strings,
                            'reference': reference, 'issue_date': issue_date,
                            'start_date': start_date,
                            'finish_date': finish_date, 'kwh': Decimal(0),
                            'net': net, 'vat': vat, 'gross': Decimal('0.00'),
                            'breakdown': {}, 'reads': reads})
            elif code == "MAN":
                madn = self.parser.elements[2]
                pc_code = "0" + madn[3]
                mtc_code = madn[4]
                llfc_code = madn[5]

                mpan_strings.append(
                    pc_code + " " + mtc_code + " " + llfc_code + " " +
                    madn[0] + " " + madn[1] + madn[2])
            elif code == "VAT":
                uvla = self.parser.elements[5]
                net = Decimal('0.00') + self.parser.to_decimal(uvla)
                uvtt = self.parser.elements[6]
                vat = Decimal('0.00') + self.parser.to_decimal(uvtt)
        return raw_bills
