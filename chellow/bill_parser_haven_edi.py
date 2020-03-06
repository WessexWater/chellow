from decimal import Decimal, InvalidOperation
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from chellow.edi_lib import EdiParser, SEGMENTS
from chellow.utils import HH, to_utc, to_ct
from io import StringIO
from werkzeug.exceptions import BadRequest
from datetime import datetime as Datetime


READ_TYPE_MAP = {
    'A': 'A',
    'C': 'C',
    'D': 'D',
    'E': 'E',
    'F': 'F',
    'X': 'H',
    'I': 'I',
    'R': 'N',
    'O': 'O',
    'Q': 'Q',
    'S': 'S',
    'Z': 'Z',
}

TMOD_MAP = {
    '700285': ('standing-gbp', 'standing-rate', 'standing-days'),
    '422733': ('ccl-gbp', 'ccl-rate', 'ccl-kwh'),
    '068476': ('00442-gbp', '00442-rate', '00442-kwh'),
    '265091': ('00443-gbp', '00443-rate', '00443-kwh'),
}


def _to_date(component):
    return to_utc(to_ct(Datetime.strptime(component, "%y%m%d")))


def _to_decimal(components, divisor=None):
    comp_0 = components[0]

    try:
        result = Decimal(comp_0)
    except InvalidOperation as e:
        raise BadRequest(
            "Can't parse '" + str(comp_0) + "' of " + str(components) +
            " as a decimal:" + str(e))

    if len(components) > 1 and components[-1] == "R":
        result *= Decimal("-1")

    if divisor is not None:
        result /= Decimal(divisor)

    return result


def _find_elements(code, elements):
    segment_name = code + elements[1][0] if code == 'CCD' else code
    elem_codes = [m['code'] for m in SEGMENTS[segment_name]['elements']]
    return dict(zip(elem_codes, elements))


class Parser():
    def __init__(self, f):
        self.parser = EdiParser(
            StringIO(str(f.read(), 'utf-8', errors='ignore')))
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        headers = {}
        for self.line_number, code in enumerate(self.parser):
            elements = _find_elements(code, self.parser.elements)
            line = self.parser.line
            try:
                bill = _process_segment(code, elements, line, headers)
            except BadRequest as e:
                raise BadRequest(
                    "Can't parse the line: " + line + " :" + e.description)
            if bill is not None:
                raw_bills.append(bill)
        return raw_bills


def _process_segment(code, elements, line, headers):
    if 'breakdown' in headers:
        headers['breakdown']['raw-lines'].append(line)

    if code == "BCD":
        headers['issue_date'] = _to_date(elements['IVDT'][0])
        headers['reference'] = elements['INVN'][0]
        headers['bill_type_code'] = elements['BTCD'][0]

        sumo = elements['SUMO']
        headers['start_date'] = _to_date(sumo[0])
        headers['finish_date'] = _to_date(sumo[1]) + relativedelta(days=1) - HH

    elif code == "BTL":
        _process_BTL(elements, headers)

    elif code == "MHD":
        _process_MHD(elements, headers)

    elif code == "CCD":
        _process_CCD(elements, headers)

    elif code == 'CLO':
        _process_CLO(elements, headers)

    elif code == "MTR":
        return _process_MTR(elements, headers)

    elif code == "MAN":
        _process_MAN(elements, headers)


def _process_BTL(elements, headers):
    headers['gross'] = Decimal('0.00') + _to_decimal(elements['PTOT'], '1000')
    headers['net'] = Decimal('0.00') + _to_decimal(elements['UVLT'], '1000')
    headers['vat'] = Decimal('0.00') + _to_decimal(elements['UTVA'], '1000')


def _process_CLO(elements, headers):
    cloc = elements['CLOC']
    headers['account'] = cloc[1]
    headers['msn'] = cloc[2]


def _process_MAN(elements, headers):
    madn = elements['MADN']
    dno = madn[0]
    unique = madn[1]
    check_digit = madn[2]
    pc = madn[3]
    mtc = madn[4]
    llfc = madn[5]

    headers['mpan_cores'].append(''.join([dno, unique + check_digit]))
    headers['mpan'] = ' '.join([pc, mtc, llfc, dno, unique + check_digit])


def _process_MTR(elements, headers):
    if headers['message_type'] == "UTLBIL":
        return {
            'kwh': headers['kwh'],
            'reference': headers['reference'],
            'mpan_cores': ', '.join(headers['mpan_cores']),
            'issue_date': headers['issue_date'],
            'account': headers['account'],
            'start_date': headers['start_date'],
            'finish_date': headers['finish_date'],
            'net': headers['net'],
            'vat': headers['vat'],
            'gross': headers['gross'],
            'breakdown': headers['breakdown'],
            'reads': headers['reads'],
            'bill_type_code': headers['bill_type_code'],
        }


def _process_MHD(elements, headers):
    message_type = elements['TYPE'][0]
    if message_type == "UTLBIL":
        headers.clear()
        headers['reads'] = []
        headers['mpan_cores'] = []
        headers['breakdown'] = defaultdict(int, {'raw-lines': []})
    headers['message_type'] = message_type


def _process_CCD(elements, headers):
    ccde = elements['CCDE']
    consumption_charge_indicator = ccde[0]

    if consumption_charge_indicator == "1":
        pres_read_date = _to_date(elements['PRDT'][0]) + relativedelta(
            days=1) - HH

        prev_read_date = _to_date(elements['PVDT'][0]) + relativedelta(
            days=1) - HH

        # m = elements['MLOC'][0]

        prrd = elements['PRRD']
        pres_read_type = READ_TYPE_MAP[prrd[1]]
        prev_read_type = READ_TYPE_MAP[prrd[3]]

        coefficient = Decimal(elements['ADJF'][1]) / Decimal(100000)
        pres_reading_value = Decimal(prrd[0])
        prev_reading_value = Decimal(prrd[2])
        # msn = elements['MTNR'][0]
        tpr_code = elements['TMOD'][0]
        if tpr_code == 'kW':
            units = 'kW'
            tpr_code = None
        elif tpr_code == 'kVA':
            units = 'kVA'
            tpr_code = None
        else:
            units = 'kWh'
            kwh = _to_decimal(elements['CONS'], '1000')

        headers['reads'].append(
            {
                'msn': headers['msn'],
                'mpan': headers['mpan'],
                'coefficient': coefficient, 'units': units,
                'tpr_code': tpr_code, 'prev_date': prev_read_date,
                'prev_value': prev_reading_value,
                'prev_type_code': prev_read_type,
                'pres_date': pres_read_date,
                'pres_value': pres_reading_value,
                'pres_type_code': pres_read_type
            }
        )

    elif consumption_charge_indicator == "2":

        tmod_1 = elements['TMOD'][0]
        try:
            eln_gbp, eln_rate, eln_cons = TMOD_MAP[tmod_1]
        except KeyError:
            raise BadRequest(
                "Can't find the Tariff Modifier Code 1 " + tmod_1 +
                " in the TMOD_MAP.")

        '''
        m = elements['MLOC'][0]
        mpan_core = ' '.join((m[:2], m[2:6], m[6:10], m[10:]))
        '''

        cons = elements['CONS']
        kwh = None
        if eln_cons is not None and len(cons[0]) > 0:
            el_cons = _to_decimal(cons, '1000')
            headers['breakdown'][eln_cons] = kwh = el_cons

        if eln_rate is not None:
            rate = _to_decimal(elements['BPRI'], '100000')
            headers['breakdown'][eln_rate] = [rate]

        '''
        start_date = _to_date(elements['CSDT'][0])
        finish_date = _to_date(elements['CEDT'][0]) - HH
        '''

        if 'CTOT' in elements:
            net = Decimal('0.00') + _to_decimal(elements['CTOT'], '100')
        else:
            net = Decimal('0.00')

        headers['breakdown'][eln_gbp] = net

        if eln_gbp == 'ccl-gbp':
            kwh

    elif consumption_charge_indicator == '3':
        supplier_code = elements['CCDE'][2]

        tmod_1 = elements['TMOD'][0]
        try:
            eln_gbp, eln_rate, eln_cons = TMOD_MAP[tmod_1]
        except KeyError:
            raise BadRequest(
                "Can't find the Tariff Code Modifier 1 " + tmod_1 +
                " in the TMOD_MAP.")

        '''
        m = elements['MLOC'][0]
        mpan_core = ' '.join((m[:2], m[2:6], m[6:10], m[10:]))
        '''

        cons = elements['CONS']
        if eln_cons is not None and len(cons[0]) > 0:
            el_cons = _to_decimal(cons, '1000')
            headers['breakdown'][eln_cons] = kwh = el_cons
        else:
            kwh = Decimal('0')

        if eln_rate is not None:
            rate = _to_decimal(elements['BPRI'], '100000')
            headers['breakdown'][eln_rate] = [rate]

        '''
        start_date = _to_date(elements['CSDT'][0])
        finish_date = _to_date(elements['CEDT'][0]) - HH
        '''

        if 'CTOT' in elements:
            net = Decimal('0.00') + _to_decimal(elements['CTOT'], '100')
        else:
            net = Decimal('0.00')

        headers['breakdown'][eln_gbp] = net

        if supplier_code == 'NRG':
            headers['kwh'] = kwh

    elif consumption_charge_indicator == '4':
        tmod_1 = elements['TMOD'][0]
        try:
            eln_gbp, eln_rate, eln_cons = TMOD_MAP[tmod_1]
        except KeyError:
            raise BadRequest(
                "Can't find the Tariff Modifer Code 1 " + tmod_1 +
                " in the TMOD_MAP.")

        '''
        m = elements['MLOC'][0]
        mpan_core = ' '.join((m[:2], m[2:6], m[6:10], m[10:]))
        '''

        cons = elements['CONS']
        if eln_cons is not None and len(cons[0]) > 0:
            el_cons = _to_decimal(cons, '1000')
            headers['breakdown'][eln_cons] = kwh = el_cons

        if eln_rate is not None:
            rate = _to_decimal(elements['BPRI'], '100000')
            headers['breakdown'][eln_rate] = [rate]

        '''
        start_date = _to_date(elements['CSDT'][0])
        finish_date = _to_date(elements['CEDT'][0]) - HH
        '''

        if 'CTOT' in elements:
            net = Decimal('0.00') + _to_decimal(elements['CTOT'], '100')
        else:
            net = Decimal('0.00')

        headers['breakdown'][eln_gbp] = net

        if eln_gbp == 'ccl-gbp':
            headers['kwh'] = kwh
