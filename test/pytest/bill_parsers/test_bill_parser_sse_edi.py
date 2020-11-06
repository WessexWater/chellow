from io import BytesIO

from chellow.bill_parser_sse_edi import Parser


def test_missing_mpan_core(mocker, sess):
    file_lines = [
        "MHD=2+UTLBIL:3'",
        "MTR=6'",
    ]
    f = BytesIO(b'\n'.join(n.encode('utf8') for n in file_lines))
    parser = Parser(f)
    parser.make_raw_bills()
