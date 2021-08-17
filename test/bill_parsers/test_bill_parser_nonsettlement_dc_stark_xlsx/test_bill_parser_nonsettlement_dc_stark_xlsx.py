from chellow.bill_parser_nonsettlement_dc_stark_xlsx import Parser


def test(sess):
    f = open(
        "test/pytest/bill_parsers/"
        "test_bill_parser_nonsettlement_dc_stark_xlsx/"
        "bills.nonsettlement.dc.stark.xlsx",
        mode="rb",
    )
    parser = Parser(f)
    parser.make_raw_bills()


def test_old(sess):
    f = open(
        "test/pytest/bill_parsers/"
        "test_bill_parser_nonsettlement_dc_stark_xlsx/"
        "bills_old.nonsettlement.dc.stark.xlsx",
        mode="rb",
    )
    parser = Parser(f)
    parser.make_raw_bills()
