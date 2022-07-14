from io import BytesIO

import chellow
import chellow.e.bill_parsers.csv


def test_bill_parser_csv():
    """
    Check bills have a UTC timezone
    """

    f = BytesIO()
    for vals in [
        [
            "#InvoiceType",
            "Account Reference",
            "Mpans",
            "Invoice Reference",
            "Issue Date",
            "Start Date",
            "Finish Date",
            "kWh",
            "Net",
            "VAT",
            "Gross",
            "Breakdown",
            "R1 Meter Serial Number",
            "R1 MPAN",
            "R1 Coefficient",
            "R1 Units",
            "R1 TPR",
            "R1 Previous Read Date",
            "R1 Previous Read Value",
            "R1 Previous Read Type",
            "R1 Present Read Date",
            "R1 Present Read Value",
            "R1 Present Read Type",
        ],
        [
            "N",
            "SA342376000",
            "22 1065 3921 534",
            "3423760004",
            "2010-02-02 00:00",
            "2010-01-05 00:00",
            "2010-01-10 23:30",
            "150",
            "98.17",
            "15.01",
            "0",
            "",
            "I02D89150",
            "22 1065 3921 534",
            "1",
            "kWh",
            "1",
            "2010-01-04 23:30",
            "14281",
            "E",
            "2010-01-06 23:30",
            "15924",
            "N",
        ],
        [
            "N",
            "SA342376000",
            "22 1065 3921 534",
            "3423760005",
            "2011-02-02 00:00",
            "2011-01-05 00:00",
            "2011-01-10 23:30",
            "150",
            "98.17",
            "15.01",
            "0",
            "",
            "I02D89150",
            "22 1065 3921 534",
            "1",
            "kWh",
            "1",
            "2011-01-04 23:30",
            "24286",
            "E",
            "2011-01-06 23:30",
            "25927",
            "E",
            "I02D89150",
            "22 1065 3921 534",
            "1",
            "kWh",
            "1",
            "2011-02-04 23:30",
            "34285",
            "E",
            "2011-02-06 23:30",
            "46883",
            "E",
            "I02D89150",
            "22 1065 3921 534",
            "1",
            "kWh",
            "3",
            "2011-02-04 23:30",
            "8553",
            "E",
            "2011-02-06 23:30",
            "8553",
            "E",
        ],
    ]:
        line = ",".join(vals)
        f.write(f"{line}\n".encode("utf8"))
    f.seek(0)
    parser = chellow.e.bill_parsers.csv.Parser(f)
    for bill in parser.make_raw_bills():
        for read in bill["reads"]:
            for k in ("prev_date", "pres_date"):
                assert read[k].tzinfo is not None
