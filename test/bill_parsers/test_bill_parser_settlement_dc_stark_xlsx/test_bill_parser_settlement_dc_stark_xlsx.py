from chellow.bill_parser_settlement_dc_stark_xlsx import Parser


def test(sess):
    f = open(
        "test/bill_parsers/test_bill_parser_settlement_dc_stark_xlsx/"
        "bills.settlement.dc.stark.xlsx",
        mode="rb",
    )
    parser = Parser(f)
    parser.make_raw_bills()
