from decimal import Decimal
from io import BytesIO

from chellow.e.hh_parser_df2 import create_parser
from chellow.utils import utc_datetime


def test_parser():
    reader_lines = [
        "#F2",
        "#O 2248274887874-jlkkk38",
        "#S 1",
        "16/04/2024,00:30,0.77,A",
        "16/04/2024,01:00,0.064,A",
        "16/04/2024,01:30,0,A",
    ]
    reader = BytesIO("\n".join(reader_lines).encode("utf8"))
    mpan_map = {}
    messages = []

    parser = create_parser(reader, mpan_map, messages)
    actuals = list(parser)
    expected = [
        {
            "mpan_core": "22 4827 4887 874",
            "channel_type": "ACTIVE",
            "start_date": utc_datetime(2024, 4, 16, 0, 0),
            "value": Decimal("0.77"),
            "status": "A",
        },
        {
            "mpan_core": "22 4827 4887 874",
            "channel_type": "ACTIVE",
            "start_date": utc_datetime(2024, 4, 16, 0, 30),
            "value": Decimal("0.064"),
            "status": "A",
        },
        {
            "mpan_core": "22 4827 4887 874",
            "channel_type": "ACTIVE",
            "start_date": utc_datetime(2024, 4, 16, 1, 0),
            "value": Decimal("0"),
            "status": "A",
        },
    ]

    assert actuals == expected
