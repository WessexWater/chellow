import chellow.bill_parser_csv
from chellow.utils import to_utc, ct_datetime
from chellow.computer import PropDict
from pytz import utc
from datetime import datetime as Datetime


def test_bill_parser_csv():
    '''
    Check bills have a UTC timezone
    '''

    with open('test/bills-nhh.csv', 'rb') as f:
        parser = chellow.bill_parser_csv.Parser(f)
        for bill in parser.make_raw_bills():
            for read in bill['reads']:
                for k in ('prev_date', 'pres_date'):
                    assert read[k].tzinfo is not None


def test_to_utc():
    dt_utc = to_utc(ct_datetime(2014, 9, 6, 1))
    assert dt_utc == Datetime(2014, 9, 6, 0, 0, tzinfo=utc)


def test_propdict_get():
    assert PropDict(
        'cont ' + str(Datetime(2017, 1, 1)), {}, []).get('akey') is None


def test_propdict():
    assert PropDict('', {'*': 5})[1] == 5


def test_propdict_nested():
    assert PropDict('', {1: {'*': 5}})[1][1] == 5
