from decimal import Decimal

from chellow.gas.bill_parser_engie_edi import Parser, _process_MHD, _to_finish_date
from chellow.utils import ct_datetime, to_utc, utc_datetime


def test_to_finish_date():
    actual = _to_finish_date("211031")
    assert actual == to_utc(ct_datetime(2021, 10, 31, 23, 30))


def test_process_MHD():
    message_type = "UTLBIL"
    headers = {}
    elements = {"TYPE": [message_type, "3"]}
    _process_MHD(elements, headers)

    expected_headers = {
        "message_type": message_type,
        "reads": [],
        "raw_lines": [],
        "breakdown": {"units_consumed": Decimal("0")},
        "kwh": Decimal("0.00"),
        "net": Decimal("0.00"),
        "vat": Decimal("0.00"),
        "gross": Decimal("0.00"),
    }
    assert headers == expected_headers


def test_Parser_minimal(mocker):
    edi_lines = (
        "STX=ANA:1+Marsh Gas:MARSH Gas Limited+BPAJA:"
        "Bill Paja 771+171023:867369+856123++UTLHDR'",
        "MHD=1+UTLHDR:3'",
        "TYP=0715'",
        "SDT=Marsh Gas+Marsh Gas Limited++818671845'",
        "CDT=BPAJA:BPAJA+Bill Paja Limited - BPAJA++1'",
        "FIL=1+1+171023'",
        "MTR=6'",
        "END=288'",
    )
    edi_bytes = "\n".join(edi_lines).encode("utf8")

    parser = Parser(edi_bytes)
    bills = parser.make_raw_bills()
    assert bills == []


def test_Parser(mocker):
    edi_lines = (
        "STX=ANA:1+Marsh Gas:MARSH Gas Limited+BPAJA:Bill Paja 771+171023:867369+"
        "856123++UTLHDR'",
        "MHD=1+UTLHDR:3'",
        "TYP=0715'",
        "SDT=Marsh Gas+Marsh Gas Limited++818671845'",
        "CDT=BPAJA:BPAJA+Bill Paja Limited - BPAJA++1'",
        "FIL=1+1+171023'",
        "MTR=6'",
        "MHD=2+UTLBIL:3'",
        "CLO=::10205041+Bill Paja Limited+Mole Hall, BATH::BA1 9MH'",
        "BCD=171022+171022+7868273476++M+N++170601:170630'",
        "CCD=1+1::GAS+MARSH6:Meter Reading++hyygk4882+87614362+170701+170601++"
        "83551:01:81773:01+8746000+771000:M3+CF:102264+841349:M3++831200:KWH+170601+"
        "170701'",
        "ADJ=1+1+CV:3930000'",
        "CCD=2+3::PPK+MARSH6:Unidentified Gas++++++++8746000++CF:100000++008521+"
        "8746000+170601+170631+008727+091'",
        "CCD=3+3::PPK+MARSH6:Commodity++++++++8746000++CF:100000++9873510+8746000+"
        "170601+170630+815510+9931'",
        "CCD=4+3::PPD+MARSH6:Transportation++++++++30000++CF:100000++86221004+30000+"
        "170601+170630+86221004+9224'",
        "CCD=5+3::PPD+MARSH6:Meter Reading++++++++30000++CF:100000++82113473+30000+"
        "170601+170630+8582284+941'",
        "CCD=6+3::PPD+MARSH6:Meter Rental++++++++30000++CF:100000++3228000+30000+"
        "170601+170630+8993000+841'",
        "CCD=7+3::PPK+MARSH6:Transportation++++++++8116500++CF:100000++005337+4617800+"
        "170601+170630+006120+882'",
        "VAT=1+++L+7986+23885+331+86334'",
        "BTL=000+88772+332++77345'",
        "MTR=14'",
        "MHD=2+UTLBIL:3'",
        "CLO=::10205041+Bill Paja Limited+Mole Hall, BATH::BA1 9MH'",
        "BCD=171022+171022+7868273476++M+N++170601:170630'",
        "CCD=1+1::GAS+MARSH6:Meter Reading++hyygk4882+87614362+170701+170601++"
        "83551:01:81773:01+8746000+771000:M3+CF:102264+841349:M3++831200:KWH+"
        "170601+170701'",
        "ADJ=1+1+CV:3930000'",
        "CCD=2+3::PPK+MARSH6:Unidentified Gas++++++++8746000++CF:100000++008521+"
        "8746000+170601+170631+008727+091'",
        "CCD=3+3::PPK+MARSH6:Commodity++++++++8746000++CF:100000++9873510+8746000+"
        "170601+170630+815510'",
        "CCD=4+3::PPD+MARSH6:Transportation++++++++30000++CF:100000++86221004+30000+"
        "170601+170630+86221004+9224'",
        "CCD=5+3::PPD+MARSH6:Meter Reading++++++++30000++CF:100000++82113473+30000+"
        "170601+170630+8582284+941'",
        "CCD=6+3::PPD+MARSH6:Meter Rental++++++++30000++CF:100000++3228000+30000+"
        "170601+170630+8993000+841'",
        "CCD=7+3::PPK+MARSH6:Transportation++++++++8116500++CF:100000++005337+4617800+"
        "170601+170630+006120+882'",
        "VAT=1+++L+7986+23885+331+86334'",
        "BTL=000+88772+332++77345'",
        "MTR=14'",
        "MHD=54+UVATLR:9'",
        "VTS=1+L+5000+76984+670349+47987'",
        "VTS=2+S+20000+574903+836579+58291'",
        "MTR=18'",
        "MHD=59+UTLTLR:7'",
        "TTL=78956+7349867+789+327+7894683+32'",
        "MTR=74'",
        "END=288'",
    )
    edi_bytes = "\n".join(edi_lines).encode("utf8")

    parser = Parser(edi_bytes)
    bills = parser.make_raw_bills()
    expected_bill_1 = {
        "raw_lines": "\n".join(
            [
                "MHD=2+UTLBIL:3'",
                "CLO=::10205041+Bill Paja Limited+Mole Hall, BATH::BA1 9MH'",
                "BCD=171022+171022+7868273476++M+N++170601:170630'",
                "CCD=1+1::GAS+MARSH6:Meter Reading++hyygk4882+87614362+170701+170601++"
                "83551:01:81773:01+8746000+771000:M3+CF:102264+841349:M3++831200:KWH+"
                "170601+170701'",
                "ADJ=1+1+CV:3930000'",
                "CCD=2+3::PPK+MARSH6:Unidentified Gas++++++++8746000++CF:100000++"
                "008521+8746000+170601+170631+008727+091'",
                "CCD=3+3::PPK+MARSH6:Commodity++++++++8746000++CF:100000++9873510+"
                "8746000+170601+170630+815510+9931'",
                "CCD=4+3::PPD+MARSH6:Transportation++++++++30000++CF:100000++86221004+"
                "30000+170601+170630+86221004+9224'",
                "CCD=5+3::PPD+MARSH6:Meter Reading++++++++30000++CF:100000++82113473+"
                "30000+170601+170630+8582284+941'",
                "CCD=6+3::PPD+MARSH6:Meter Rental++++++++30000++CF:100000++3228000+"
                "30000+170601+170630+8993000+841'",
                "CCD=7+3::PPK+MARSH6:Transportation++++++++8116500++CF:100000++005337+"
                "4617800+170601+170630+006120+882'",
                "VAT=1+++L+7986+23885+331+86334'",
                "BTL=000+88772+332++77345'",
            ]
        ),
        "mprn": "87614362",
        "reference": "7868273476",
        "account": "87614362",
        "reads": [
            {
                "msn": "hyygk4882",
                "unit": "M3",
                "correction_factor": Decimal("1.02264"),
                "prev_date": utc_datetime(2017, 5, 31, 23, 0),
                "prev_value": Decimal("81773"),
                "prev_type_code": "E",
                "pres_date": utc_datetime(2017, 6, 30, 23, 0),
                "pres_value": Decimal("83551"),
                "pres_type_code": "E",
                "calorific_value": Decimal("39.3"),
            }
        ],
        "kwh": Decimal("831.20"),
        "breakdown": {
            "units_consumed": Decimal("771"),
            "ug_rate": [Decimal("0.0008521")],
            "ug_gbp": Decimal("0.91"),
            "ug_kwh": Decimal("8746"),
            "commodity_rate": [Decimal("0.987351")],
            "commodity_gbp": Decimal("99.31"),
            "commodity_kwh": Decimal("8746"),
            "transportation_fixed_rate": [Decimal("8.6221004")],
            "transportation_fixed_gbp": Decimal("92.24"),
            "transportation_fixed_days": Decimal("30"),
            "meter_read_rate": [Decimal("8.2113473")],
            "meter_read_gbp": Decimal("9.41"),
            "meter_read_days": Decimal("30"),
            "metering_rate": [Decimal("0.3228")],
            "metering_gbp": Decimal("8.41"),
            "metering_days": Decimal("30"),
            "transportation_variable_rate": [Decimal("0.0005337")],
            "transportation_variable_gbp": Decimal("8.82"),
            "transportation_variable_kwh": Decimal("4617.8"),
            "vat_rate": [Decimal("0.07986")],
        },
        "net_gbp": Decimal("238.85"),
        "vat_gbp": Decimal("3.31"),
        "gross_gbp": Decimal("863.34"),
        "bill_type_code": "N",
        "start_date": utc_datetime(2017, 5, 31, 23, 0),
        "finish_date": utc_datetime(2017, 6, 30, 22, 30),
        "issue_date": utc_datetime(
            2017,
            10,
            21,
            23,
            0,
        ),
    }
    expected_bill_2 = {
        "raw_lines": "\n".join(
            [
                "MHD=2+UTLBIL:3'",
                "CLO=::10205041+Bill Paja Limited+Mole Hall, BATH::BA1 9MH'",
                "BCD=171022+171022+7868273476++M+N++170601:170630'",
                "CCD=1+1::GAS+MARSH6:Meter Reading++hyygk4882+87614362+170701+170601++"
                "83551:01:81773:01+8746000+771000:M3+CF:102264+841349:M3++831200:KWH+"
                "170601+170701'",
                "ADJ=1+1+CV:3930000'",
                "CCD=2+3::PPK+MARSH6:Unidentified Gas++++++++8746000++CF:100000++"
                "008521+8746000+170601+170631+008727+091'",
                "CCD=3+3::PPK+MARSH6:Commodity++++++++8746000++CF:100000++9873510+"
                "8746000+170601+170630+815510'",
                "CCD=4+3::PPD+MARSH6:Transportation++++++++30000++CF:100000++86221004+"
                "30000+170601+170630+86221004+9224'",
                "CCD=5+3::PPD+MARSH6:Meter Reading++++++++30000++CF:100000++82113473+"
                "30000+170601+170630+8582284+941'",
                "CCD=6+3::PPD+MARSH6:Meter Rental++++++++30000++CF:100000++3228000+"
                "30000+170601+170630+8993000+841'",
                "CCD=7+3::PPK+MARSH6:Transportation++++++++8116500++CF:100000++005337+"
                "4617800+170601+170630+006120+882'",
                "VAT=1+++L+7986+23885+331+86334'",
                "BTL=000+88772+332++77345'",
            ],
        ),
        "mprn": "87614362",
        "reference": "7868273476",
        "account": "87614362",
        "reads": [
            {
                "msn": "hyygk4882",
                "unit": "M3",
                "correction_factor": Decimal("1.02264"),
                "prev_date": utc_datetime(2017, 5, 31, 23, 0),
                "prev_value": Decimal("81773"),
                "prev_type_code": "E",
                "pres_date": utc_datetime(2017, 6, 30, 23, 0),
                "pres_value": Decimal("83551"),
                "pres_type_code": "E",
                "calorific_value": Decimal("39.3"),
            }
        ],
        "kwh": Decimal("831.20"),
        "breakdown": {
            "units_consumed": Decimal("771"),
            "ug_rate": [Decimal("0.0008521")],
            "ug_gbp": Decimal("0.91"),
            "ug_kwh": Decimal("8746"),
            "commodity_rate": [Decimal("0.987351")],
            "transportation_fixed_rate": [Decimal("8.6221004")],
            "transportation_fixed_gbp": Decimal("92.24"),
            "transportation_fixed_days": Decimal("30"),
            "meter_read_rate": [Decimal("8.2113473")],
            "meter_read_gbp": Decimal("9.41"),
            "meter_read_days": Decimal("30"),
            "metering_rate": [Decimal("0.3228")],
            "metering_gbp": Decimal("8.41"),
            "metering_days": Decimal("30"),
            "transportation_variable_rate": [Decimal("0.0005337")],
            "transportation_variable_gbp": Decimal("8.82"),
            "transportation_variable_kwh": Decimal("4617.8"),
            "vat_rate": [Decimal("0.07986")],
        },
        "net_gbp": Decimal("238.85"),
        "vat_gbp": Decimal("3.31"),
        "gross_gbp": Decimal("863.34"),
        "bill_type_code": "N",
        "start_date": utc_datetime(2017, 5, 31, 23, 0),
        "finish_date": utc_datetime(2017, 6, 30, 22, 30),
        "issue_date": utc_datetime(2017, 10, 21, 23, 0),
    }
    assert bills == [expected_bill_1, expected_bill_2]
