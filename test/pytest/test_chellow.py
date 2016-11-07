import chellow.bill_parser_csv


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
