import chellow.bill_parser_csv
from chellow.utils import to_utc, ct_datetime, dumps
from pytz import utc
from datetime import datetime as Datetime
from collections import OrderedDict
from decimal import Decimal


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


def test_dumps():
    assert dumps(OrderedDict()) == """$ion_1_0 {
}"""

    desired = OrderedDict(
        (
            ('hello', Decimal('89')), ('me', '99')))
    assert dumps(desired) == """$ion_1_0 {
  "hello": 89,
  "me": "99"}"""
