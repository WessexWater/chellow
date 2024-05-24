import datetime
from collections import defaultdict
from decimal import Decimal
from io import StringIO

from werkzeug.exceptions import BadRequest

from chellow.utils import HH, to_ct, to_utc


def parse_date(date_str):
    return to_utc(to_ct(parse_date_naive(date_str)))


def parse_date_naive(date_str):
    return datetime.datetime.strptime(date_str, "%Y%m%d")


def _chop_record(record, **kwargs):
    parts = {}
    idx = 0
    for name, length in kwargs.items():
        parts[name] = record[idx : idx + length]
        idx += length
    return parts


DATE_LENGTH = 8


def _handle_0000(headers, pre_record, record):
    parts = _chop_record(record, unknown_1=9, issue_date=DATE_LENGTH)
    headers["issue_date"] = parse_date(parts["issue_date"])


def _handle_0050(headers, pre_record, record):
    pass


def _handle_0051(headers, pre_record, record):
    pass


def _handle_0100(headers, pre_record, record):
    issue_date = headers["issue_date"]
    headers.clear()
    headers["issue_date"] = issue_date
    headers["account"] = pre_record[33:41]
    headers["reference"] = pre_record[41:46]
    headers["kwh"] = Decimal("0")
    headers["breakdown"] = defaultdict(int, {"vat": {}})
    headers["reads"] = []


def _handle_0101(headers, pre_record, record):
    parts = _chop_record(record, start_date=DATE_LENGTH, finish_date=DATE_LENGTH)
    headers["start_date"] = parse_date(parts["start_date"])
    headers["finish_date"] = to_utc(to_ct(parse_date_naive(parts["finish_date"]) - HH))


CHARGE_LOOKUP = {
    "STDG": "days",
    "UNIT": "kwh",
}

ELEMENT_LOOKUP = {"10ANNUAL": "standing", "20RS0108": "0001", "9WANNUAL": "site_fee"}


def _handle_0460(headers, pre_record, record):
    parts = _chop_record(
        record,
        unknown_1=12,
        gbp=12,
        code=8,
        quantity=12,
        charge=4,
        unknown_2=18,
        rate=16,
        unknown_date=DATE_LENGTH,
        another_gbp=12,
        charge_description=35,
    )
    units = CHARGE_LOOKUP[parts["charge"]]
    gbp = Decimal(parts["gbp"]) / 100
    quantity = Decimal(parts["quantity"])
    rate = Decimal(parts["rate"])
    element_name = ELEMENT_LOOKUP[parts["code"]]
    breakdown = headers["breakdown"]
    breakdown[f"{element_name}-{units}"] += quantity
    rate_name = f"{element_name}-rate"
    if rate_name in breakdown:
        rates = breakdown[rate_name]
    else:
        rates = breakdown[rate_name] = set()

    rates.add(rate)
    breakdown[f"{element_name}-gbp"] += gbp


UNITS_LOOKUP = {"KWH": "kwh"}

REGISTER_CODE_LOOKUP = {"000001": "0001"}


def _handle_0461(headers, pre_record, record):
    parts = _chop_record(
        record,
        msn=11,
        unknown_1=2,
        prev_read_value=12,
        pres_read_value=12,
        register_code=6,
        units=6,
        quantity=12,
        charge=6,
        prev_read_type=1,
        pres_read_type=1,
        mpan_core=13,
        mpan_top=8,
        tariff_code=19,
        pres_read_date=DATE_LENGTH,
        prev_read_date=DATE_LENGTH,
    )
    mpan_core = parts["mpan_core"]
    headers["mpan_core"] = mpan_core
    units = UNITS_LOOKUP[parts["units"].strip()]
    if units == "kwh":
        headers["kwh"] += Decimal(parts["quantity"])
    tpr_code = REGISTER_CODE_LOOKUP[parts["register_code"]]

    headers["reads"].append(
        {
            "msn": parts["msn"].strip(),
            "mpan": f"{parts['mpan_top']} {mpan_core}",
            "coefficient": 1,
            "units": units,
            "tpr_code": tpr_code,
            "prev_date": parse_date(parts["prev_read_date"]),
            "prev_value": Decimal(parts["prev_read_value"]),
            "prev_type_code": parts["prev_read_type"],
            "pres_date": parse_date(parts["pres_read_date"]),
            "pres_value": Decimal(parts["pres_read_value"]),
            "pres_type_code": parts["pres_read_type"],
        }
    )


def _handle_0470(headers, pre_record, record):
    pass


def _handle_1460(headers, pre_record, record):
    parts = _chop_record(record, unknown_1=1, net=12, vat_rate=5, vat=12)
    net = Decimal(parts["net"]) / Decimal(100)
    vat_rate = int(Decimal(parts["vat_rate"]))
    vat = Decimal(parts["vat"]) / Decimal(100)

    vat_breakdown = headers["breakdown"]["vat"]
    try:
        vat_bd = vat_breakdown[vat_rate]
    except KeyError:
        vat_bd = vat_breakdown[vat_rate] = {"vat": Decimal("0"), "net": Decimal("0")}

    vat_bd["vat"] += vat
    vat_bd["net"] += net


def _handle_1500(headers, pre_record, record):
    parts = _chop_record(
        record,
        unknown_1=8,
        unknown_2=10,
        net=10,
        unknown_3=10,
        unknown_4=20,
        vat=10,
        unknown_5=10,
        unknown_6=20,
        gross=12,
    )
    return {
        "bill_type_code": "N",
        "mpan_core": headers["mpan_core"],
        "account": headers["account"],
        "reference": headers["reference"],
        "issue_date": headers["issue_date"],
        "start_date": headers["start_date"],
        "finish_date": headers["finish_date"],
        "kwh": headers["kwh"],
        "net": Decimal(parts["net"]),
        "vat": Decimal(parts["vat"]),
        "gross": Decimal(parts["gross"]),
        "breakdown": headers["breakdown"],
        "reads": headers["reads"],
    }


def _handle_2000(headers, pre_record, record):
    pass


def _handle_9999(headers, pre_record, record):
    pass


LINE_HANDLERS = {
    "0000": _handle_0000,
    "0050": _handle_0050,
    "0051": _handle_0051,
    "0100": _handle_0100,
    "0101": _handle_0101,
    "0460": _handle_0460,
    "0461": _handle_0461,
    "0470": _handle_0470,
    "1460": _handle_1460,
    "1500": _handle_1500,
    "2000": _handle_2000,
    "9999": _handle_9999,
}


class Parser:
    def __init__(self, f):
        self.f = StringIO(str(f.read(), "utf-8", errors="ignore"))
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        headers = {}
        for self.line_number, line in enumerate(self.f, 1):
            pre_record, record_type, record = line[:80], line[80:84], line[84:]
            try:
                handler = LINE_HANDLERS[record_type]
            except KeyError:
                raise BadRequest(
                    f"Record type {record_type} not recognized on line "
                    f"{self.line_number} {line}"
                )

            try:
                bill = handler(headers, pre_record, record)
            except BadRequest as e:
                raise BadRequest(
                    f"Problem at line {self.line_number} {line}: {e.description}"
                )
            except BaseException as e:
                raise Exception(
                    f"Problem at line {self.line_number} {line}: {e}"
                ) from e
            if bill is not None:
                raw_bills.append(bill)

        return raw_bills
