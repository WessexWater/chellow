import chellow.bill_parser_haven_edi
from decimal import Decimal


def test_process_BTL(mocker):
    elements = {
        'PTOT': ['0'],
        'UVLT': ['0'],
        'UTVA': ['0'],
    }
    headers = {
    }
    chellow.bill_parser_haven_edi._process_BTL(elements, headers)
    expected_headers = {
        'net': Decimal('0.00'),
        'vat': Decimal('0.00'),
        'gross': Decimal('0.00'),
    }
    assert headers == expected_headers
    assert str(headers['net']) == '0.00'


def test_process_MTR_UTLHDR(mocker):
    elements = {}
    headers = {
        'message_type': "UTLHDR",
        'breakdown': {}
    }
    bill = chellow.bill_parser_haven_edi._process_MTR(elements, headers)
    assert bill is None


def test_process_MTR_UTLBIL(mocker):
    elements = {}
    headers = {
        'message_type': "UTLBIL",
        'breakdown': {},
        'kwh': 8,
        'reference': 'a',
        'issue_date': 'd',
        'account': 'acc',
        'start_date': 'd',
        'finish_date': 'd',
        'net': 0,
        'vat': 0,
        'gross': 0,
        'reads': [],
        'bill_type_code': 'N',
    }
    chellow.bill_parser_haven_edi._process_MTR(elements, headers)


def test_process_MHD(mocker):
    message_type = 'UTLBIL'
    elements = {
        'TYPE': [message_type]
    }

    headers = {}
    chellow.bill_parser_haven_edi._process_MHD(elements, headers)
    expected_headers = {
        'message_type': message_type,
        'reads': [],
        'breakdown': {
            'raw-lines': []
        }
    }
    assert headers == expected_headers


def test_process_CCD3_NRG(mocker):
    elements = {
        'CCDE': ['3', '', 'NRG'],
        'TMOD': ['068476'],
        'CONS': [[]],
        'BPRI': ['10'],
    }

    headers = {
        'breakdown': {
            'raw-lines': []
        }
    }

    chellow.bill_parser_haven_edi._process_CCD(elements, headers)

    expected_headers = {
        'kwh': 0,
        'breakdown': {
            'raw-lines': [],
            '00442-rate': [Decimal('0.0001')],
            '00442-gbp': Decimal('0.00')
        }
    }
    assert headers == expected_headers
