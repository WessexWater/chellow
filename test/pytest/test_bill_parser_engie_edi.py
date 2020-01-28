import chellow.bill_parser_engie_edi
from io import BytesIO
from chellow.utils import to_utc, ct_datetime, utc_datetime
import pytest
from werkzeug.exceptions import BadRequest
from decimal import Decimal


def test_to_decimal():
    components = ['x']
    with pytest.raises(BadRequest):
        chellow.bill_parser_engie_edi._to_decimal(components)


def test_find_elements(mocker):
    code = 'MHD'
    elements = [
        ['ref'],
        ['a', '56'],
    ]
    actual = chellow.bill_parser_engie_edi._find_elements(code, elements)
    expected = {
        'MSRF': ['ref'],
        'TYPE': ['a', '56']
    }

    assert actual == expected


def test_make_raw_bills(mocker):
    mocker.patch(
        'chellow.bill_parser_engie_edi._process_segment', return_value=None)
    edi_file = BytesIO("DNA=3'".encode('utf-8'))
    parser = chellow.bill_parser_engie_edi.Parser(edi_file)
    assert parser.make_raw_bills() == []


def test_process_segment_CCD1(mocker):
    code = 'CCD'
    elements = {
        'CCDE': ['1', 'f'],
        'TCOD': ['584867', 'AAHEDC'],
        'TMOD': ['1', '2', '3', '4'],
        'MTNR': ['rikt8'],
        'MLOC': ['alskdj'],
        'PRDT': ['180901'],
        'PVDT': ['180801'],
        'NDRP': ['x'],
        'PRRD': ['9876', '00', 78649, '00'],
        'CONS': ['77', 'kWh', 'R'],
        'CONB': ['9850', 'kWh', 'R'],
        'ADJF': ['x', '688', 'R'],
        'CONA': ['743', 'kWh', 'R'],
        'BPRI': ['895'],
        'NUCT': ['68349', 'kWh', 'R'],
        'CSDT': ['180901'],
        'CEDT': ['180801'],
        'CPPU': ['7003'],
        'CTOT': ['78679', 'R'],
        'TSUP': ['jf'],
        'VATC': ['ig'],
        'VATP': ['77'],
        'MSAD': ['fk', 'fdk'],
    }
    line = ''
    headers = {}
    chellow.bill_parser_engie_edi._process_segment(
        code, elements, line, headers)
    expected_headers = {
        'reads': [
            {
                'msn': 'rikt8',
                'mpan': '   al skdj  ',
                'coefficient': Decimal('0.00688'),
                'units': 'kWh',
                'tpr_code': '1',
                'prev_date': utc_datetime(2018, 8, 1, 22, 30),
                'prev_value': Decimal('78649'),
                'prev_type_code': 'N',
                'pres_date': utc_datetime(2018, 9, 1, 22, 30),
                'pres_value': Decimal('9876'),
                'pres_type_code': 'N'
            }
        ]
    }
    assert headers == expected_headers


def test_process_segment_CCD2(mocker):
    code = 'CCD'
    elements = {
        'CCDE': ['2', 'ADD'],
        'TCOD': ['584867', 'AAHEDC'],
        'TMOD': [],
        'MTNR': [],
        'MLOC': ['22767395756734'],
        'PRDT': [],
        'PVDT': [],
        'NDRP': [],
        'PRRD': [],
        'CONS': ['877457492', 'KWH'],
        'CONB': [],
        'ADJF': ['UG'],
        'CONA': [],
        'BPRI': ['974'],
        'NUCT': ['877457492', 'KWH'],
        'CSDT': ['191001'],
        'CEDT': ['191101'],
        'CPPU': ['748'],
        'CTOT': ['76981'],
    }
    line = ''
    reference = 'kdhgsf'
    issue_date = utc_datetime(2019, 4, 1)
    headers = {
        'reference': reference,
        'issue_date': issue_date,
        'bill_type_code': 'N'
    }
    bill = chellow.bill_parser_engie_edi._process_segment(
        code, elements, line, headers)
    expected_headers = {
        'bill_type_code': 'N',
        'reference': reference,
        'issue_date': issue_date,
        'mpan_core': '22 7673 9575 6734',
        'bill_start_date': to_utc(ct_datetime(2019, 10, 1)),
        'bill_finish_date': to_utc(ct_datetime(2019, 10, 31, 23, 30)),
    }
    expected_bill = {
        'bill_type_code': 'N',
        'reference': 'kdhgsf_aahedc',
        'issue_date': issue_date,
        'mpan_cores': '22 7673 9575 6734',
        'account': '22 7673 9575 6734',
        'start_date': utc_datetime(2019, 9, 30, 23, 0),
        'finish_date': utc_datetime(2019, 10, 31, 23, 30),
        'kwh': Decimal('0.00'),
        'net': Decimal('769.81'),
        'vat': 0,
        'gross': Decimal('769.81'),
        'breakdown': {
            'raw-lines': '',
            'aahedc-kwh': Decimal('877457.492'),
            'aahedc-rate': [Decimal('0.00974')],
            'aahedc-gbp': Decimal('769.81')
        },
        'reads': []
    }

    assert headers == expected_headers
    print(bill)
    assert bill == expected_bill
    assert isinstance(bill['kwh'], Decimal)
    assert isinstance(bill['net'], Decimal)
    assert isinstance(bill['vat'], Decimal)
    assert isinstance(bill['gross'], Decimal)
    assert str(bill['net']) == str(expected_bill['net'])


def test_process_segment_CCD3(mocker):
    code = 'CCD'
    elements = {
        'CCDE': ['3', 'ADD'],
        'TCOD': ['584867', 'AAHEDC'],
        'TMOD': [],
        'MTNR': [],
        'MLOC': ['22767395756734'],
        'PRDT': [],
        'PVDT': [],
        'NDRP': [],
        'PRRD': [],
        'CONS': ['877457492', 'KWH'],
        'CONB': [],
        'ADJF': ['UG'],
        'CONA': [],
        'BPRI': ['974'],
        'NUCT': ['877457492', 'KWH'],
        'CSDT': ['191001'],
        'CEDT': ['191101'],
        'CPPU': ['748'],
        'CTOT': ['76981'],
    }
    line = ''

    issue_date = utc_datetime(2019, 9, 3)
    reference = 'hgtuer8'
    headers = {
        'issue_date': issue_date,
        'reference': reference,
        'bill_type_code': 'N'
    }
    chellow.bill_parser_engie_edi._process_segment(
        code, elements, line, headers)
    expected_headers = {
        'mpan_core': '22 7673 9575 6734',
        'bill_start_date': to_utc(ct_datetime(2019, 10, 1)),
        'bill_finish_date': to_utc(ct_datetime(2019, 10, 31, 23, 30)),
        'issue_date': issue_date,
        'reference': reference,
        'bill_type_code': 'N'
    }
    assert headers == expected_headers


def test_process_segment_CCD3_ro(mocker):
    code = 'CCD'
    elements = {
        'CCDE': ['3', 'ADD'],
        'TCOD': ['425779', 'RO Mutualisation'],
        'TMOD': [],
        'MTNR': [],
        'MLOC': ['22767395756734'],
        'PRDT': [],
        'PVDT': [],
        'NDRP': [],
        'PRRD': [],
        'CONS': ['', ''],
        'CONB': [],
        'ADJF': ['UG'],
        'CONA': [],
        'BPRI': ['974'],
        'NUCT': ['877457492', 'KWH'],
        'CSDT': ['191001'],
        'CEDT': ['191101'],
        'CPPU': ['748'],
        'CTOT': ['76981'],
    }
    line = ''

    issue_date = utc_datetime(2019, 9, 3)
    reference = 'hgtuer8'
    headers = {
        'issue_date': issue_date,
        'reference': reference,
        'bill_type_code': 'N'
    }
    chellow.bill_parser_engie_edi._process_segment(
        code, elements, line, headers)
    expected_headers = {
        'mpan_core': '22 7673 9575 6734',
        'bill_start_date': to_utc(ct_datetime(2019, 10, 1)),
        'bill_finish_date': to_utc(ct_datetime(2019, 10, 31, 23, 30)),
        'issue_date': issue_date,
        'reference': reference,
        'bill_type_code': 'N'
    }
    assert headers == expected_headers


def test_process_segment_MHD(mocker):
    code = 'MHD'
    elements = {
        'MSRF': ['ref'],
        'TYPE': ['a', '56'],
    }
    line = ''
    headers = {}
    chellow.bill_parser_engie_edi._process_segment(
        code, elements, line, headers)


def test_process_segment_ccd2_no_CTOT(mocker):
    code = 'CCD'
    elements = {
        'CCDE': ['2', 'ADD'],
        'TCOD': ['584867', 'AAHEDC'],
        'TMOD': [],
        'MTNR': [],
        'MLOC': ['22767395756734'],
        'PRDT': [],
        'PVDT': [],
        'NDRP': [],
        'PRRD': [],
        'CONS': ['877457492', 'KWH'],
        'CONB': [],
        'ADJF': ['UG'],
        'CONA': [],
        'BPRI': ['974'],
        'NUCT': ['877457492', 'KWH'],
        'CSDT': ['191001'],
        'CEDT': ['191101'],
        'CPPU': ['748'],
    }
    line = ''
    headers = {
        'reference': 'shkfsd',
        'bill_type_code': 'N',
        'issue_date': utc_datetime(2019, 9, 3)
    }
    bill = chellow.bill_parser_engie_edi._process_segment(
        code, elements, line, headers)
    assert str(bill['net']) == '0.00'


def test_process_segment_ccd2_blank_CONS(mocker):
    code = 'CCD'
    elements = {
        'CCDE': ['2', 'ADD'],
        'TCOD': ['584867', 'AAHEDC'],
        'TMOD': [],
        'MTNR': [],
        'MLOC': ['22767395756734'],
        'PRDT': [],
        'PVDT': [],
        'NDRP': [],
        'PRRD': [],
        'CONS': [''],
        'CONB': [],
        'ADJF': ['UG'],
        'CONA': [],
        'BPRI': ['974'],
        'NUCT': ['877457492', 'KWH'],
        'CSDT': ['191001'],
        'CEDT': ['191101'],
        'CPPU': ['748'],
    }
    line = ''
    headers = {
        'reference': 'hgdertk',
        'bill_type_code': 'N',
        'issue_date': utc_datetime(2019, 9, 3)
    }
    chellow.bill_parser_engie_edi._process_segment(
        code, elements, line, headers)
