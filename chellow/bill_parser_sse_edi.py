from decimal import Decimal
from collections import defaultdict
from chellow.edi_lib import EdiParser, to_decimal
from chellow.utils import to_ct, to_utc, ct_datetime, parse_mpan_core, HH
from werkzeug.exceptions import BadRequest
from io import StringIO
from datetime import datetime as Datetime


read_type_map = {
    '00': 'N', '09': 'N3', '04': 'C', '02': 'E', '11': 'E3', '01': 'EM',
    '03': 'W', '06': 'X', '05': 'CP', '12': 'IF'
}

tmod_map = {
    '0001': '00001',
    '3U93': '00001',
    'URQ1': '00001',
    'Z012': '00001',
    '246N': '00160',
    '0210': '00210',
    'W246': '00276',
    '0043': '00043',
    'DAQ2': '01071',
    'NIQ2': '01072',
    'NQ22': '00210',
    'DQ22': '00043',
    'D7P2': '00043',
    'N7P2': '00210',
    'MDC1': 'kW',
    'URC1': '00001',
    '0206': '00206',
    '0040': '00040',
    '1140': '01140',
    '1139': '01139',
    'A154': '01154',
    'A153': '01153',
    '0039': '00039',
    '0221': '00221',
    '210E': '00210',
    '1150': '01150',
    '1149': '01149',
    '0153': '00153',
    'WQ42': '00184',
    'NQ42': '00210',
    'EQ42': '00187',
    'WDQ3': '01073',
    'EWQ3': '01074',
    'WDQ4': '01075',
    'EWQ4': '01076',
    'NIQ4': '01077',
    'EQ32': '00072',
    'NQ32': '00184',
    '0276': '00276',
    '0277': '00277',
    '0160': '00160',
    '1152': '01152',
    '1151': '01151',
    '1142': '01142',
    '1141': '01141',
    '0249': '00249',
    '0252': '00252',
    '0240': '00240',
    '0244': '00244',
    '0092': '00092',
    '210A': '00210',
    'MAC2': 'kW',
    'DAC2': '00040',
    'NAC2': '00206',
    'NDC2': '00040',
    'NNC2': '00206',
    'MNC2': 'kW',
    '148A': '00148',
    '221B': '00221',
    '080A': '00080',
    'P1M3': '00248',
    'P2M3': '00251',
    'W1M3': '00239',
    'W2M3': '00073',
    'OTM3': '00093',
    'NIM3': '00208',
    'MDM3': 'kW',
    'URQD': '00001',
    'OPE3': '01088',
    'OEC2': '00190',
    '184A': '00184',
    '210J': '00210',
    '187A': '00187',
    '0183': '00183',
    '0071': '00071',
    'DAE7': '00043',
    'NIE7': '00210',
    'OPAC': '00010',
    'MDM1': 'kW',
    'D179': '01139',
    'N179': '01140',
    'O212': '00212',
    '0151': '00151',
    'SG1U': '00001',
    '0184': '00184',
    '0072': '00072',
    'DM22': '00039',
    'NM22': '00221',
    'MM22': 'kW',
    '0044': '00044',
    '0208': '00208',
    'URM1': '00001',
    '1043': '01043',
    '1042': '01042',
    'U393': '00001',
    'D244': '00040',
    'N244': '00206',
    '24D4': '00040',
    '24N4': '00206',
    'OFX2': '00001',
    'D151': '00043',
    'N151': '00210',
    'N184': '01150',
    'D184': '01149',
    'OPF2': '00257',
    'N154': '00221',
    'O2EC': '00190',
    'OFC2': '00159',
    'CMACUF': 'kW',
    '251A': '00251',
    '208D': '00208',
    '073A': '00073',
    '093A': '00093',
    '248A': '00248',
    '239A': '00239',
    'EA1E': 'kVA',
    'MDM2': 'kVA'}


def to_ct_date(component):
    return to_ct(Datetime.strptime(component, "%y%m%d"))


def to_start_date(component):
    return to_utc(to_ct_date(component))


def to_finish_date(component):
    d = to_ct_date(component)
    return to_utc(ct_datetime(d.year, d.month, d.day, 23, 30))


class Parser():
    def __init__(self, f):
        self.parser = EdiParser(
            StringIO(str(f.read(), 'utf-8', errors='ignore')))
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        breakdown = None
        for self.line_number, code in enumerate(self.parser):
            if code == "BCD":
                ivdt = self.parser.elements[0]
                issue_date = to_utc(to_ct_date(ivdt[0]))

                invn = self.parser.elements[2]
                reference = invn[0]
                account = 'SA' + reference[:9]

                btcd = self.parser.elements[5]
                bill_type_code = btcd[0]

                sumo = self.parser.elements[7]
                start_date = to_start_date(sumo[0])
                if to_ct_date(sumo[1]) in (
                        ct_datetime(2020, 4, 1), ct_datetime(2020, 3, 16)):
                    finish_date = to_start_date(sumo[1]) - HH
                else:
                    finish_date = to_finish_date(sumo[1])

            elif code == "MHD":
                type = self.parser.elements[1]
                message_type = type[0]
                if message_type == "UTLBIL":
                    issue_date = None
                    start_date = None
                    finish_date = None
                    account = None
                    reference = None
                    net = Decimal('0.00')
                    vat = Decimal('0.00')
                    gross = Decimal('0.00')
                    kwh = Decimal(0)
                    reads = []
                    bill_type_code = None
                    mpan_core = None
                    breakdown = defaultdict(int, {'raw-lines': []})

            elif code == "CCD":
                ccde = self.parser.elements[1]
                consumption_charge_indicator = ccde[0]

                if consumption_charge_indicator == "1":
                    prdt = self.parser.elements[6]
                    pvdt = self.parser.elements[7]

                    pres_read_date = to_finish_date(prdt[0])
                    prev_read_date = to_finish_date(pvdt[0])

                    tmod = self.parser.elements[3]
                    mtnr = self.parser.elements[4]
                    mloc = self.parser.elements[5]

                    mpan = mloc[0]
                    mpan = mpan[13:15] + ' ' + mpan[15:18] + ' ' + \
                        mpan[18:] + ' ' + mpan[:2] + ' ' + mpan[2:6] + ' ' + \
                        mpan[6:10] + ' ' + mpan[10:13]

                    prrd = self.parser.elements[9]
                    pres_read_type = read_type_map[prrd[1]]
                    prev_read_type = read_type_map[prrd[3]]

                    adjf = self.parser.elements[12]
                    cons = self.parser.elements[13]

                    coefficient = Decimal(adjf[1]) / Decimal(100000)
                    pres_reading_value = Decimal(prrd[0])
                    prev_reading_value = Decimal(prrd[2])
                    msn = mtnr[0]
                    tpr_native = tmod[0]
                    if tpr_native not in tmod_map:
                        raise BadRequest(
                            "The TPR code " + tpr_native +
                            " can't be found in the TPR list for mpan " +
                            mpan + ".")
                    tpr_code = tmod_map[tpr_native]
                    if tpr_code == 'kW':
                        units = 'kW'
                        tpr_code = None
                    elif tpr_code == 'kVA':
                        units = 'kVA'
                        tpr_code = None
                    else:
                        units = 'kWh'
                        kwh += to_decimal(cons) / Decimal('1000')

                    reads.append(
                        {
                            'msn': msn, 'mpan': mpan,
                            'coefficient': coefficient, 'units': units,
                            'tpr_code': tpr_code, 'prev_date': prev_read_date,
                            'prev_value': prev_reading_value,
                            'prev_type_code': prev_read_type,
                            'pres_date': pres_read_date,
                            'pres_value': pres_reading_value,
                            'pres_type_code': pres_read_type})
                elif consumption_charge_indicator == "2":
                    # tcod = self.parser.elements[2]
                    tmod = self.parser.elements[3]
                    mtnr = self.parser.elements[4]
                    mloc = self.parser.elements[5]

                    mpan = mloc[0]
                    mpan = mpan[13:15] + ' ' + mpan[15:18] + ' ' + \
                        mpan[18:] + ' ' + mpan[:2] + ' ' + mpan[2:6] + ' ' + \
                        mpan[6:10] + ' ' + mpan[10:13]

                    prdt = self.parser.elements[6]
                    pvdt = self.parser.elements[7]

                    pres_read_date = to_finish_date(prdt[0])
                    prev_read_date = to_finish_date(pvdt[0])

                    ndrp = self.parser.elements[8]
                    prrd = self.parser.elements[9]
                    pres_read_type = read_type_map[prrd[1]]
                    prev_read_type = read_type_map[prrd[3]]

                    adjf = self.parser.elements[12]
                    cona = self.parser.elements[13]

                    coefficient = Decimal(adjf[1]) / Decimal(100000)
                    pres_reading_value = Decimal(prrd[0])
                    prev_reading_value = Decimal(prrd[2])
                    msn = mtnr[0]
                    tpr_code = tmod[0]
                    if tpr_code not in tmod_map:
                        raise BadRequest(
                            "The TPR code " + tpr_code +
                            " can't be found in the TPR list for mpan " +
                            mpan + ".")
                    tpr = tmod_map[tpr_code]
                    if tpr == 'kW':
                        units = 'kW'
                        tpr = None
                        prefix = 'md-'
                    elif tpr == 'kVA':
                        units = 'kVA'
                        tpr = None
                        prefix = 'md-'
                    else:
                        units = 'kWh'
                        kwh += to_decimal(cona) / Decimal('1000')
                        prefix = tpr + '-'

                    nuct = self.parser.elements[15]
                    breakdown[prefix + 'kwh'] += \
                        to_decimal(nuct) / Decimal('1000')
                    cppu = self.parser.elements[18]
                    rate_key = prefix + 'rate'
                    if rate_key not in breakdown:
                        breakdown[rate_key] = set()
                    breakdown[rate_key].add(
                        to_decimal(cppu) / Decimal('100000'))
                    ctot = self.parser.elements[19]
                    breakdown[prefix + 'gbp'] += \
                        to_decimal(ctot) / Decimal('100')

                    reads.append(
                        {
                            'msn': msn, 'mpan': mpan,
                            'coefficient': coefficient, 'units': units,
                            'tpr_code': tpr, 'prev_date': prev_read_date,
                            'prev_value': prev_reading_value,
                            'prev_type_code': prev_read_type,
                            'pres_date': pres_read_date,
                            'pres_value': pres_reading_value,
                            'pres_type_code': pres_read_type})
                elif consumption_charge_indicator == '3':
                    # tcod = self.parser.elements[2]
                    tmod = self.parser.elements[3]
                    tmod0 = tmod[0]
                    if tmod0 == 'CCL':
                        prefix = kwh_prefix = 'ccl-'
                    elif tmod0 in ['CQFITC', 'CMFITC']:
                        prefix = 'fit-'
                        kwh_prefix = 'fit-msp-'
                    elif tmod0 == 'FITARR':
                        prefix = kwh_prefix = 'fit-reconciliation-'
                    else:
                        tpr_code = tmod0
                        if tpr_code not in tmod_map:
                            raise BadRequest(
                                "The TPR code " + tpr_code +
                                " can't be found in the TPR list for mpan " +
                                mpan + ".")
                        prefix = kwh_prefix = tmod_map[tpr_code] + '-'

                    mtnr = self.parser.elements[4]
                    ndrp = self.parser.elements[8]
                    cona = self.parser.elements[13]
                    nuct = self.parser.elements[15]
                    breakdown[kwh_prefix + 'kwh'] += \
                        to_decimal(nuct) / Decimal('1000')
                    cppu = self.parser.elements[18]

                    rate_key = prefix + 'rate'
                    if rate_key not in breakdown:
                        breakdown[rate_key] = set()
                    breakdown[rate_key].add(
                        to_decimal(cppu) / Decimal('100000'))

                    ctot = self.parser.elements[19]
                    breakdown[prefix + 'gbp'] += \
                        to_decimal(ctot) / Decimal('100')
                elif consumption_charge_indicator == '4':
                    # tcod = self.parser.elements[2]
                    tmod = self.parser.elements[3]
                    tmod0 = tmod[0]

                    mtnr = self.parser.elements[4]
                    ndrp = self.parser.elements[8]
                    if len(ndrp[0]) > 0:
                        breakdown['standing-days'] += \
                            to_decimal(ndrp)
                    cona = self.parser.elements[13]
                    nuct = self.parser.elements[15]
                    cppu = self.parser.elements[18]
                    ctot = self.parser.elements[19]
                    if len(ctot[0]) > 0:
                        breakdown['standing-gbp'] += \
                            to_decimal(ctot) / Decimal('100')
            elif code == "MTR":
                if message_type == "UTLBIL":
                    for k, v in tuple(breakdown.items()):
                        if isinstance(v, set):
                            breakdown[k] = ', '.join(sorted(map(str, v)))

                    raw_bill = {
                        'bill_type_code': bill_type_code, 'account': account,
                        'mpan_core': mpan_core, 'reference': reference,
                        'issue_date': issue_date, 'start_date': start_date,
                        'finish_date': finish_date, 'kwh': kwh, 'net': net,
                        'vat': vat, 'gross': gross, 'breakdown': breakdown,
                        'reads': reads
                    }
                    raw_bills.append(raw_bill)
                    breakdown = None

            elif code == "MAN":
                madn = self.parser.elements[2]
                '''
                pc_code = madn[3]
                mtc_code = madn[4]
                llfc_code = madn[5]
                '''

                mpan_core = parse_mpan_core(
                    ''.join((madn[0], madn[1], madn[2])))

            elif code == "VAT":
                uvla = self.parser.elements[5]
                net += to_decimal(uvla) / Decimal('100')
                uvtt = self.parser.elements[6]
                vat += to_decimal(uvtt) / Decimal('100')
                ucsi = self.parser.elements[7]
                gross += to_decimal(ucsi) / Decimal('100')

            if breakdown is not None:
                breakdown['raw-lines'].append(self.parser.line)

        return raw_bills
