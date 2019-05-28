from chellow.utils import utc_datetime
import chellow.bill_parser_engie_xls
import xlrd.sheet


def test_parse_row(mocker):
    row = []
    for val in [
            'Power Comany Ltd.',
            'Bill Paja',
            '556',
            'BILL PAJA',
            '883',
            '1 True Way',
            '672770',
            43555.00,
            43555.00,
            '',
            '2019-03-01 - 2019-03-31',
            '',
            '',
            '',
            'Draft',
            '',
            'Product',
            'Hand Held Read -',
            43555.00,
            43555.00,
            '',
            '2299999999929',
            '',
            '',
            '',
            '785',
            'GBP',
            'INV',
            '',
            '']:
        cell = mocker.Mock(spec=xlrd.sheet.Cell)
        cell.value = val
        row.append(cell)

    row_index = 2
    datemode = 0
    title_row = ['To Date']

    bill = chellow.bill_parser_engie_xls._parse_row(
        row, row_index, datemode, title_row)
    print(bill)
    assert bill['finish_date'] == utc_datetime(2019, 3, 31, 22, 30)
