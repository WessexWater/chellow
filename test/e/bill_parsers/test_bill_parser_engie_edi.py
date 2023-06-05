from decimal import Decimal
from io import BytesIO


from chellow.e.bill_parsers.engie_edi import (
    CODE_FUNCS,
    Parser,
    _process_BCD,
    _process_CCD1,
    _process_CCD2,
    _process_CCD3,
    _process_MHD,
    _process_NOOP,
    _process_VAT,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_CODE_FUNCS():
    assert CODE_FUNCS["BCD"] == _process_BCD
    assert CODE_FUNCS["BTL"] == _process_NOOP
    assert CODE_FUNCS["END"] == _process_NOOP
    assert CODE_FUNCS["TTL"] == _process_NOOP
    assert CODE_FUNCS["VTS"] == _process_NOOP


def test_process_CCD1(mocker):
    elements = {
        "CCDE": ["1", "f"],
        "TCOD": ["584867", "AAHEDC"],
        "TMOD": ["1", "2", "3", "4"],
        "MTNR": ["rikt8"],
        "MLOC": ["alskdj"],
        "PRDT": ["180901"],
        "PVDT": ["180801"],
        "NDRP": ["x"],
        "PRRD": ["9876", "00", 78649, "00"],
        "CONS": ["77", "kWh", "R"],
        "CONB": ["9850", "kWh", "R"],
        "ADJF": ["x", "688", "R"],
        "CONA": ["743", "kWh", "R"],
        "BPRI": ["895"],
        "NUCT": ["68349", "kWh", "R"],
        "CSDT": ["180901"],
        "CEDT": ["180801"],
        "CPPU": ["7003"],
        "CTOT": ["78679", "R"],
        "TSUP": ["jf"],
        "VATC": ["ig"],
        "VATP": ["77"],
        "MSAD": ["fk", "fdk"],
    }
    headers = {}
    _process_CCD1(elements, headers)
    expected_headers = {
        "reads": [
            {
                "msn": "rikt8",
                "mpan": "   al skdj  ",
                "coefficient": Decimal("0.00688"),
                "units": "kWh",
                "tpr_code": "1",
                "prev_date": utc_datetime(2018, 8, 1, 22, 30),
                "prev_value": Decimal("78649"),
                "prev_type_code": "N",
                "pres_date": utc_datetime(2018, 9, 1, 22, 30),
                "pres_value": Decimal("9876"),
                "pres_type_code": "N",
            }
        ]
    }
    assert headers == expected_headers


def test_process_CCD2_duos_availability(mocker):
    elements = {
        "CCDE": ["2", "ADD"],
        "TCOD": ["219182", "DUoS Availability"],
        "TMOD": [],
        "MTNR": [],
        "MLOC": ["22767395756734"],
        "PRDT": [],
        "PVDT": [],
        "NDRP": [],
        "PRRD": [],
        "CONS": ["877457492", "KWH"],
        "CONB": [],
        "ADJF": ["UG"],
        "CONA": [],
        "BPRI": ["974"],
        "NUCT": ["877457492", "KWH"],
        "CSDT": ["191001"],
        "CEDT": ["191101"],
        "CPPU": ["748"],
        "CTOT": ["76981"],
    }
    reference = "kdhgsf"
    issue_date = utc_datetime(2019, 4, 1)
    headers = {"reference": reference, "issue_date": issue_date, "bill_type_code": "N"}
    bill = _process_CCD2(elements, headers)
    expected_headers = {
        "bill_type_code": "N",
        "reference": reference,
        "issue_date": issue_date,
        "mpan_core": "22 7673 9575 6734",
        "bill_start_date": to_utc(ct_datetime(2019, 10, 1)),
        "bill_finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
    }
    expected_bill = {
        "bill_type_code": "N",
        "reference": "kdhgsf_duos-availability",
        "issue_date": issue_date,
        "mpan_core": "22 7673 9575 6734",
        "account": "22 7673 9575 6734",
        "start_date": utc_datetime(2019, 9, 30, 23, 0),
        "finish_date": utc_datetime(2019, 10, 31, 23, 30),
        "kwh": Decimal("0"),
        "net": Decimal("769.81"),
        "vat": Decimal("0.00"),
        "gross": Decimal("769.81"),
        "breakdown": {
            "duos-availability-kva": [Decimal("877457.492")],
            "duos-availability-rate": [Decimal("0.00974")],
            "duos-availability-gbp": Decimal("769.81"),
        },
        "reads": [],
    }

    assert headers == expected_headers
    print(bill)
    print(expected_bill)
    assert bill == expected_bill
    assert isinstance(bill["kwh"], Decimal)
    assert isinstance(bill["net"], Decimal)
    assert isinstance(bill["vat"], Decimal)
    assert isinstance(bill["gross"], Decimal)
    assert str(bill["net"]) == str(expected_bill["net"])


def test_process_CCD3(mocker):
    elements = {
        "CCDE": ["3", "ADD"],
        "TCOD": ["584867", "AAHEDC"],
        "TMOD": [],
        "MTNR": [],
        "MLOC": ["22767395756734"],
        "PRDT": [],
        "PVDT": [],
        "NDRP": [],
        "PRRD": [],
        "CONS": ["877457492", "KWH"],
        "CONB": [],
        "ADJF": ["UG"],
        "CONA": [],
        "BPRI": ["974"],
        "NUCT": ["877457492", "KWH"],
        "CSDT": ["191001"],
        "CEDT": ["191101"],
        "CPPU": ["748"],
        "CTOT": ["76981"],
    }

    issue_date = utc_datetime(2019, 9, 3)
    reference = "hgtuer8"
    headers = {"issue_date": issue_date, "reference": reference, "bill_type_code": "N"}
    _process_CCD3(elements, headers)
    expected_headers = {
        "mpan_core": "22 7673 9575 6734",
        "bill_start_date": to_utc(ct_datetime(2019, 10, 1)),
        "bill_finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
        "issue_date": issue_date,
        "reference": reference,
        "bill_type_code": "N",
    }
    assert headers == expected_headers


def test_process_CCD3_ro(mocker):
    elements = {
        "CCDE": ["3", "ADD"],
        "TCOD": ["425779", "RO Mutualisation"],
        "TMOD": [],
        "MTNR": [],
        "MLOC": ["22767395756734"],
        "PRDT": [],
        "PVDT": [],
        "NDRP": [],
        "PRRD": [],
        "CONS": ["", ""],
        "CONB": [],
        "ADJF": ["UG"],
        "CONA": [],
        "BPRI": ["974"],
        "NUCT": ["877457492", "KWH"],
        "CSDT": ["191001"],
        "CEDT": ["191101"],
        "CPPU": ["748"],
        "CTOT": ["76981"],
    }
    issue_date = utc_datetime(2019, 9, 3)
    reference = "hgtuer8"
    headers = {"issue_date": issue_date, "reference": reference, "bill_type_code": "N"}
    _process_CCD3(elements, headers)
    expected_headers = {
        "mpan_core": "22 7673 9575 6734",
        "bill_start_date": to_utc(ct_datetime(2019, 10, 1)),
        "bill_finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
        "issue_date": issue_date,
        "reference": reference,
        "bill_type_code": "N",
    }
    assert headers == expected_headers


def test_process_CCD2_no_CTOT(mocker):
    elements = {
        "CCDE": ["2", "ADD"],
        "TCOD": ["584867", "AAHEDC"],
        "TMOD": [],
        "MTNR": [],
        "MLOC": ["22767395756734"],
        "PRDT": [],
        "PVDT": [],
        "NDRP": [],
        "PRRD": [],
        "CONS": ["877457492", "KWH"],
        "CONB": [],
        "ADJF": ["UG"],
        "CONA": [],
        "BPRI": ["974"],
        "NUCT": ["877457492", "KWH"],
        "CSDT": ["191001"],
        "CEDT": ["191101"],
        "CPPU": ["748"],
    }
    headers = {
        "reference": "shkfsd",
        "bill_type_code": "N",
        "issue_date": utc_datetime(2019, 9, 3),
    }
    bill = _process_CCD2(elements, headers)
    assert str(bill["net"]) == "0.00"


def test_process_CCD2_blank_CONS(mocker):
    elements = {
        "CCDE": ["2", "ADD"],
        "TCOD": ["584867", "AAHEDC"],
        "TMOD": [],
        "MTNR": [],
        "MLOC": ["22767395756734"],
        "PRDT": [],
        "PVDT": [],
        "NDRP": [],
        "PRRD": [],
        "CONS": [""],
        "CONB": [],
        "ADJF": ["UG"],
        "CONA": [],
        "BPRI": ["974"],
        "NUCT": ["877457492", "KWH"],
        "CSDT": ["191001"],
        "CEDT": ["191101"],
        "CPPU": ["748"],
    }
    headers = {
        "reference": "hgdertk",
        "bill_type_code": "N",
        "issue_date": utc_datetime(2019, 9, 3),
    }
    _process_CCD2(elements, headers)


def test_process_segment_CCD2_blank_ro(mocker):
    elements = {
        "CCDE": ["2", "ADD"],
        "TCOD": ["378246", "Ro"],
        "TMOD": [],
        "MTNR": [],
        "MLOC": ["22767395756734"],
        "PRDT": [],
        "PVDT": [],
        "NDRP": [],
        "PRRD": [],
        "CONS": [""],
        "CONB": [],
        "ADJF": ["UG"],
        "CONA": [],
        "BPRI": ["974"],
        "NUCT": [],
        "CSDT": ["191001"],
        "CEDT": ["191101"],
        "CPPU": ["748"],
        "CTOT": ["76981"],
    }
    reference = "kdhgsf"
    issue_date = utc_datetime(2019, 4, 1)
    headers = {"reference": reference, "issue_date": issue_date, "bill_type_code": "N"}
    bill = _process_CCD2(elements, headers)
    expected_headers = {
        "bill_type_code": "N",
        "reference": reference,
        "issue_date": issue_date,
        "mpan_core": "22 7673 9575 6734",
        "bill_start_date": to_utc(ct_datetime(2019, 10, 1)),
        "bill_finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
    }
    expected_bill = {
        "bill_type_code": "N",
        "reference": "kdhgsf_ro",
        "issue_date": issue_date,
        "mpan_core": "22 7673 9575 6734",
        "account": "22 7673 9575 6734",
        "start_date": utc_datetime(2019, 9, 30, 23, 0),
        "finish_date": utc_datetime(2019, 10, 31, 23, 30),
        "kwh": Decimal("0.00"),
        "net": Decimal("769.81"),
        "vat": Decimal("0.00"),
        "gross": Decimal("769.81"),
        "breakdown": {
            "ro-rate": [Decimal("0.00974")],
            "ro-gbp": Decimal("769.81"),
        },
        "reads": [],
    }

    assert headers == expected_headers
    assert bill == expected_bill
    assert isinstance(bill["kwh"], Decimal)
    assert isinstance(bill["net"], Decimal)
    assert isinstance(bill["vat"], Decimal)
    assert isinstance(bill["gross"], Decimal)
    assert str(bill["net"]) == str(expected_bill["net"])


def test_process_MHD(mocker):
    elements = {
        "MSRF": ["ref"],
        "TYPE": ["a", "56"],
    }
    headers = {}
    _process_MHD(elements, headers)


def test_process_VAT(mocker):
    elements = {"UVTT": ["0"], "VATP": ["20"], "UVLA": ["4"]}
    headers = {
        "mpan_core": "22 7673 9575 6734",
        "reference": "xx2",
        "issue_date": to_utc(ct_datetime(2020, 3, 1)),
        "bill_start_date": to_utc(ct_datetime(2020, 1, 1)),
        "bill_finish_date": to_utc(ct_datetime(2020, 1, 31)),
        "bill_type_code": "N",
    }
    _process_VAT(elements, headers)


def test_make_raw_bills(mocker):
    edi_file = BytesIO()
    parser = Parser(edi_file)
    assert parser.make_raw_bills() == []
