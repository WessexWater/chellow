from decimal import Decimal
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from chellow.edi_lib import EdiParser, to_decimal, to_date
from chellow.utils import HH
from io import StringIO


READ_TYPE_MAP = {
    '00': 'A',
    '01': 'E'
}

TCOD_MAP = {
    'Unidentified Gas': {
        'PPK': 'ug'
    },
    'Commodity': {
        'PPK': 'commodity'
    },
    'Transportation': {
        'PPD': 'transportation_fixed',
        'PPK': 'transportation_variable'
    },
    'Gas Flexi': {
        'PPK': 'commodity'
    },
    'Flex - Gas Flexi (New)': {
        'PPK': 'commodity'
    },
    'Meter Reading': {
        'PPD': 'meter_read'
    },
    'Meter Reading Credit Oct 19': {
        'FIX': 'meter_read'
    },
    'Meter Rental': {
        'PPD': 'metering'
    },
    'CCL': {
        'PPK': 'ccl'
    },
    'Consumption Based Administration': {
        'PPK': 'admin_variable'
    },
    'Swing': {
        'PPK': 'swing'
    }
}

UNIT_MAP = {
    'M3': 'M3',
    'HH': 'HCUF'
}


class Parser():
    def __init__(self, f):
        self.parser = EdiParser(
            StringIO(str(f.read(), 'utf-8', errors='ignore')))
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        message_type = breakdown = raw_lines = None
        for self.line_number, code in enumerate(self.parser):
            if code == "ADJ":
                # seqa = self.parser.elements[0]
                # seqb = self.parser.elements[1]
                adjf = self.parser.elements[2]
                if adjf[0] == 'CV':
                    cv = Decimal(adjf[1]) / Decimal(100000)

            if code == "BCD":
                ivdt = self.parser.elements[0]
                issue_date = to_date(ivdt[0])

                invn = self.parser.elements[2]
                reference = invn[0]

                btcd = self.parser.elements[5]
                bill_type_code = btcd[0]

                sumo = self.parser.elements[7]
                start_date = to_date(sumo[0])
                finish_date = to_date(sumo[1]) + relativedelta(days=1) - HH

            elif code == "MHD":
                typ = self.parser.elements[1]
                message_type = typ[0]
                if message_type == "UTLBIL":
                    issue_date = None
                    start_date = None
                    finish_date = None
                    reference = None
                    net = Decimal('0.00')
                    vat = Decimal('0.00')
                    gross = Decimal('0.00')
                    kwh = Decimal(0)
                    reads = []
                    bill_type_code = None
                    mprn = None
                    raw_lines = []
                    breakdown = defaultdict(
                        int, {
                            'units_consumed': Decimal(0)
                        }
                    )
                    cv = None
            elif code == "CCD":
                ccde = self.parser.elements[1]
                consumption_charge_indicator = ccde[0]

                if consumption_charge_indicator == "1":

                    # tmod = self.parser.elements[3]

                    mtnr = self.parser.elements[4]
                    msn = mtnr[0]

                    mloc = self.parser.elements[5]

                    # Bug in EDI where MPRN missing in second CCD 1
                    if mprn is None:
                        mprn = mloc[0]

                    prdt = self.parser.elements[6]
                    pvdt = self.parser.elements[7]

                    pres_read_date = to_date(prdt[0])
                    prev_read_date = to_date(pvdt[0])

                    prrd = self.parser.elements[9]
                    pres_read_value = Decimal(prrd[0])
                    pres_read_type = READ_TYPE_MAP[prrd[1]]
                    prev_read_value = Decimal(prrd[2])
                    prev_read_type = READ_TYPE_MAP[prrd[3]]

                    # cons = self.parser.elements[10]

                    conb = self.parser.elements[11]
                    unit = UNIT_MAP[conb[1]]
                    breakdown['units_consumed'] += \
                        to_decimal(conb) / Decimal('1000')

                    adjf = self.parser.elements[12]
                    correction_factor = Decimal(adjf[1]) / Decimal(100000)

                    # cona = self.parser.elements[13]
                    # bpri = self.parser.elements[14]

                    nuct = self.parser.elements[15]

                    kwh += to_decimal(nuct) / Decimal('1000')

                    reads.append(
                        {
                            'msn': msn,
                            'unit': unit,
                            'correction_factor': correction_factor,
                            'prev_date': prev_read_date,
                            'prev_value': prev_read_value,
                            'prev_type_code': prev_read_type,
                            'pres_date': pres_read_date,
                            'pres_value': pres_read_value,
                            'pres_type_code': pres_read_type
                        }
                    )

                elif consumption_charge_indicator == "2":
                    ccde_supplier_code = ccde[2]
                    tcod = self.parser.elements[2]

                    tpref = TCOD_MAP[tcod[1]][ccde_supplier_code]

                    # tmod = self.parser.elements[3]

                    mtnr = self.parser.elements[4]
                    mloc = self.parser.elements[5]
                    prdt = self.parser.elements[6]
                    pvdt = self.parser.elements[7]
                    # ndrp = self.parser.elements[8]
                    prrd = self.parser.elements[9]
                    # cons = self.parser.elements[10]
                    conb = self.parser.elements[11]
                    adjf = self.parser.elements[12]
                    # cona = self.parser.elements[13]

                    bpri = self.parser.elements[14]
                    rate_key = tpref + '_rate'
                    if rate_key not in breakdown:
                        breakdown[rate_key] = set()
                    rate = Decimal(bpri[0]) / Decimal('10000000')
                    breakdown[rate_key].add(rate)

                    nuct = self.parser.elements[15]

                    # csdt = self.parser.elements[16]
                    # cedt = self.parser.elements[17]
                    # cppu = self.parser.elements[18]

                    try:
                        ctot = self.parser.elements[19]
                        breakdown[tpref + '_gbp'] += \
                            to_decimal(ctot) / Decimal('100')

                        # tsup = self.parser.elements[20]
                        # vatc = self.parser.elements[21]
                        # vatp = self.parser.elements[22]
                        # msad = self.parser.elements[23]
                        if ccde_supplier_code == 'PPK':
                            key = tpref + '_kwh'
                        elif ccde_supplier_code == 'PPD':
                            key = tpref + '_days'

                        breakdown[key] += to_decimal(nuct) / Decimal('1000')
                    except IndexError:
                        pass

                elif consumption_charge_indicator == '3':
                    ccde_supplier_code = ccde[2]
                    tcod = self.parser.elements[2]

                    tpref = TCOD_MAP[tcod[1]][ccde_supplier_code]

                    # tmod = self.parser.elements[3]

                    mtnr = self.parser.elements[4]
                    mloc = self.parser.elements[5]
                    prdt = self.parser.elements[6]
                    pvdt = self.parser.elements[7]
                    # ndrp = self.parser.elements[8]
                    prrd = self.parser.elements[9]
                    # cons = self.parser.elements[10]
                    conb = self.parser.elements[11]
                    adjf = self.parser.elements[12]
                    # cona = self.parser.elements[13]

                    bpri = self.parser.elements[14]
                    rate_key = tpref + '_rate'
                    if rate_key not in breakdown:
                        breakdown[rate_key] = set()
                    rate = Decimal(bpri[0]) / Decimal('10000000')
                    breakdown[rate_key].add(rate)

                    nuct = self.parser.elements[15]

                    # csdt = self.parser.elements[16]
                    # cedt = self.parser.elements[17]
                    # cppu = self.parser.elements[18]

                    try:
                        ctot = self.parser.elements[19]
                        breakdown[tpref + '_gbp'] += \
                            to_decimal(ctot) / Decimal('100')

                        # tsup = self.parser.elements[20]
                        # vatc = self.parser.elements[21]
                        # vatp = self.parser.elements[22]
                        # msad = self.parser.elements[23]
                        if ccde_supplier_code == 'PPK':
                            key = tpref + '_kwh'
                        elif ccde_supplier_code == 'PPD':
                            key = tpref + '_days'

                        breakdown[key] += to_decimal(nuct) / Decimal('1000')
                    except IndexError:
                        pass

                elif consumption_charge_indicator == "4":
                    ccde_supplier_code = ccde[2]
                    tcod = self.parser.elements[2]

                    tpref = TCOD_MAP[tcod[1]][ccde_supplier_code]

                    # tmod = self.parser.elements[3]

                    mtnr = self.parser.elements[4]
                    mloc = self.parser.elements[5]
                    prdt = self.parser.elements[6]
                    pvdt = self.parser.elements[7]
                    # ndrp = self.parser.elements[8]
                    prrd = self.parser.elements[9]
                    # cons = self.parser.elements[10]
                    conb = self.parser.elements[11]
                    adjf = self.parser.elements[12]
                    # cona = self.parser.elements[13]

                    bpri = self.parser.elements[14]
                    rate_key = tpref + '_rate'
                    if rate_key not in breakdown:
                        breakdown[rate_key] = set()
                    rate = Decimal(bpri[0]) / Decimal('10000000')
                    breakdown[rate_key].add(rate)

                    nuct = self.parser.elements[15]

                    # csdt = self.parser.elements[16]
                    # cedt = self.parser.elements[17]
                    # cppu = self.parser.elements[18]

                    try:
                        ctot = self.parser.elements[19]
                        breakdown[tpref + '_gbp'] += \
                            to_decimal(ctot) / Decimal('100')

                        # tsup = self.parser.elements[20]
                        # vatc = self.parser.elements[21]
                        # vatp = self.parser.elements[22]
                        # msad = self.parser.elements[23]
                        if ccde_supplier_code == 'PPK':
                            key = tpref + '_kwh'
                        elif ccde_supplier_code == 'PPD':
                            key = tpref + '_days'

                        breakdown[key] += to_decimal(nuct) / Decimal('1000')
                    except IndexError:
                        pass

            elif code == "MTR":
                if message_type == 'UTLBIL':
                    for k, v in tuple(breakdown.items()):
                        if isinstance(v, set):
                            breakdown[k] = sorted(v)

                    for read in reads:
                        read['calorific_value'] = cv

                    raw_bills.append(
                        {
                            'raw_lines': '\n'.join(raw_lines),
                            'mprn': mprn,
                            'reference': reference,
                            'account': mprn,
                            'reads': reads,
                            'kwh': kwh,
                            'breakdown': breakdown,
                            'net_gbp': net,
                            'vat_gbp': vat,
                            'gross_gbp': gross,
                            'bill_type_code': bill_type_code,
                            'start_date': start_date,
                            'finish_date': finish_date,
                            'issue_date': issue_date
                        }
                    )

            elif code == "VAT":
                vatp = self.parser.elements[4]
                if 'vat_rate' not in breakdown:
                    breakdown['vat_rate'] = set()
                breakdown['vat_rate'].add(to_decimal(vatp) / Decimal(100000))

                uvla = self.parser.elements[5]
                net += to_decimal(uvla) / Decimal('100')
                uvtt = self.parser.elements[6]
                vat += to_decimal(uvtt) / Decimal('100')
                ucsi = self.parser.elements[7]
                gross += to_decimal(ucsi) / Decimal('100')

            if raw_lines is not None:
                raw_lines.append(self.parser.line)

        return raw_bills
