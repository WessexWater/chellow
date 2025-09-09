from decimal import Decimal
from io import BytesIO


from chellow.e.bill_parsers.engie_edi import (
    CODE_FUNCS,
    Parser,
    _process_BCD,
    _process_BTL,
    _process_CCD1,
    _process_CCD2,
    _process_CCD3,
    _process_END,
    _process_MHD,
    _process_NOOP,
    _process_VAT,
)
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_CODE_FUNCS():
    assert CODE_FUNCS["BCD"] == _process_BCD
    assert CODE_FUNCS["BTL"] == _process_BTL
    assert CODE_FUNCS["END"] == _process_END
    assert CODE_FUNCS["TTL"] == _process_NOOP
    assert CODE_FUNCS["VTS"] == _process_NOOP


def test_process_CCD1(mocker):
    elements = {
        "CCDE": ["1", "f"],
        "TCOD": ["584867", "Day"],
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
    headers = {"reads": []}
    _process_CCD1(elements, headers)
    expected_headers = {
        "reads": [
            {
                "msn": "rikt8",
                "mpan": "   al skdj  ",
                "coefficient": Decimal("0.00688"),
                "units": "kWh",
                "tpr_code": "00043",
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


def test_process_CCD2_ro(mocker):
    elements = {
        "CCDE": ["2", "ADD"],
        "TCOD": ["307660", "RO"],
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
    headers = {"elements": [], "kwh": Decimal("0")}
    _process_CCD2(elements, headers)
    expected_headers = {
        "elements": [
            {
                "name": "ro",
                "net": Decimal("769.81"),
                "breakdown": {
                    "kwh": Decimal("877457.492"),
                    "rate": {Decimal("0.00974")},
                },
                "start_date": to_utc(ct_datetime(2019, 10, 1)),
                "finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
            },
        ],
        "kwh": Decimal("877457.492"),
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
    headers = {
        "elements": [],
    }
    _process_CCD2(elements, headers)
    expected_headers = {
        "elements": [
            {
                "name": "duos-availability",
                "net": Decimal("769.81"),
                "breakdown": {
                    "kva": {Decimal("877457.492")},
                    "rate": {Decimal("0.00974")},
                },
                "start_date": to_utc(ct_datetime(2019, 10, 1)),
                "finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
            },
        ],
    }

    assert headers == expected_headers


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

    headers = {"elements": []}
    _process_CCD3(elements, headers)
    expected_headers = {
        "elements": [
            {
                "name": "aahedc",
                "net": Decimal("769.81"),
                "start_date": to_utc(ct_datetime(2019, 10, 1)),
                "finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
                "breakdown": {
                    "kwh": Decimal("877457.492"),
                    "rate": {
                        Decimal("0.00974"),
                    },
                },
            }
        ],
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
    headers = {"elements": []}
    _process_CCD3(elements, headers)
    expected_headers = {
        "elements": [
            {
                "name": "ro",
                "net": Decimal("769.81"),
                "start_date": to_utc(ct_datetime(2019, 10, 1)),
                "finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
                "breakdown": {"rate": {Decimal("0.00974")}},
            }
        ],
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
        "elements": [],
    }
    _process_CCD2(elements, headers)

    assert headers == {
        "elements": [
            {
                "net": Decimal("0.00"),
                "breakdown": {
                    "kwh": Decimal("877457.492"),
                    "rate": {
                        Decimal("0.00974"),
                    },
                },
                "finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
                "name": "aahedc",
                "start_date": to_utc(ct_datetime(2019, 10, 1, 0, 0)),
            }
        ]
    }


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
        "elements": [],
    }
    _process_CCD2(elements, headers)

    assert headers == {
        "elements": [
            {
                "breakdown": {
                    "rate": {
                        Decimal("0.00974"),
                    },
                },
                "finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
                "name": "aahedc",
                "net": Decimal("0.00"),
                "start_date": to_utc(ct_datetime(2019, 10, 1, 0, 0)),
            },
        ]
    }


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
    headers = {"elements": []}
    _process_CCD2(elements, headers)
    expected_headers = {
        "elements": [
            {
                "name": "ro",
                "net": Decimal("769.81"),
                "start_date": to_utc(ct_datetime(2019, 10, 1)),
                "finish_date": to_utc(ct_datetime(2019, 10, 31, 23, 30)),
                "breakdown": {
                    "rate": {Decimal("0.00974")},
                },
            },
        ],
    }

    assert headers == expected_headers
    element = headers["elements"][0]
    assert isinstance(element["net"], Decimal)


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
        "breakdown": {},
    }
    _process_VAT(elements, headers)

    assert headers == {
        "breakdown": {
            "vat": {
                Decimal("0.02"): {
                    "net": Decimal("0.04"),
                    "vat": Decimal("0.00"),
                },
            },
        }
    }


def test_make_raw_bills(mocker):
    edi_file = BytesIO()
    parser = Parser(edi_file)
    assert parser.make_raw_bills() == []


def test_make_raw_bills_bill(mocker):
    edi_lines = [
        "STX=ANA:1+ENGIE REX:ENGIE Revised Electricity XML+"
        "SPECTRE:Spectre Inc- SPEC+230427:141606+768389++UTLHDR'",
        "MHD=1+UTLHDR:3'",
        "TYP=7698'",
        "SDT=ENGIE REX+ENGIE Revised Electricity XML++741911934'",
        "CDT=SPECTRE:SPECTERELEC+Spectre Inc- SPECTRE++1'",
        "FIL=49+1+230427'",
        "MTR=6'",
        "MHD=2+UTLBIL:3'",
        "CLO=::756697345++Volcano:Island:::BA6 99J'",
        "BCD=230414+230414+2-03185844++M+N++230301:230401'",
        "CCD=1+2::ADD+579387:Capacity Market (Estimate)+++2287572747106+++++7883:KWH++"
        "CF++009521+7883:KWH+230301+230401+009521+8773'",
        "MAN=1+1+22:8757274710:9:00:845:N11+E12D88751'",
        "VAT=1+++S+20000+7332+98677+38196'",
        "BTL=000+97732+967712++76882'",
        "MTR=43'",
        "END=425'",
    ]
    edi_file = BytesIO("".join(f"{line}\n" for line in edi_lines).encode())
    parser = Parser(edi_file)
    actual = parser.make_raw_bills()
    expected = [
        {
            "bill_type_code": "N",
            "reference": "2-03185844",
            "issue_date": utc_datetime(2023, 4, 13, 23, 0),
            "mpan_core": "22 8757 2747 109",
            "account": "756697345",
            "start_date": utc_datetime(2023, 3, 1, 0, 0),
            "finish_date": utc_datetime(2023, 3, 31, 22, 30),
            "kwh": Decimal("0"),
            "net": Decimal("977.32"),
            "vat": Decimal("9677.12"),
            "gross": Decimal("768.82"),
            "breakdown": {
                "vat": {
                    Decimal("20"): {
                        "vat": Decimal("986.77"),
                        "net": Decimal("73.32"),
                    }
                },
                "raw-lines": [
                    "MHD=2+UTLBIL:3'",
                    "CLO=::756697345++Volcano:Island:::BA6 99J'",
                    "BCD=230414+230414+2-03185844++M+N++230301:230401'",
                    "CCD=1+2::ADD+579387:Capacity Market (Estimate)+++"
                    "2287572747106+++++7883:KWH++"
                    "CF++009521+7883:KWH+230301+230401+009521+8773'",
                    "MAN=1+1+22:8757274710:9:00:845:N11+E12D88751'",
                    "VAT=1+++S+20000+7332+98677+38196'",
                    "BTL=000+97732+967712++76882'",
                    "MTR=43'",
                ],
            },
            "elements": [
                {
                    "name": "capacity",
                    "net": Decimal("87.73"),
                    "breakdown": {
                        "kwh": Decimal("7.883"),
                        "rate": {Decimal("0.09521")},
                    },
                    "start_date": to_utc(ct_datetime(2023, 3, 1, 0, 0)),
                    "finish_date": to_utc(ct_datetime(2023, 3, 31, 23, 30)),
                }
            ],
            "reads": [],
        },
    ]
    for i, (expected_bill, actual_bill) in enumerate(zip(expected, actual)):
        assert expected_bill == actual_bill, f"problem with bill {i}"
    assert actual == expected
