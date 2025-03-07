import datetime
from collections import defaultdict
from decimal import Decimal
from io import StringIO

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest

from chellow.utils import parse_mpan_core, to_ct, to_utc


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
    parts = _chop_record(
        record,
        issue_date=DATE_LENGTH,
        unknown_1=12,
        unknown_2=12,
        unknown_3=12,
        unknown_4=12,
        late_payment=12,
    )
    headers["late_payment"] = Decimal(parts["late_payment"]) / Decimal(100)


def _handle_0051(headers, pre_record, record):
    pass


def _handle_0100(headers, pre_record, record):
    issue_date = headers["issue_date"]
    late_payment = headers.get("late_payment")
    headers.clear()
    headers["issue_date"] = issue_date
    if late_payment is not None:
        headers["late_payment"] = late_payment
    headers["account"] = pre_record[33:41]
    headers["reference"] = pre_record[41:46]
    headers["kwh"] = Decimal("0")
    headers["breakdown"] = defaultdict(int, {"vat": {}})
    headers["reads"] = []


def _handle_0101(headers, pre_record, record):
    parts = _chop_record(record, start_date=DATE_LENGTH, finish_date=DATE_LENGTH)
    headers["start_date"] = parse_date(parts["start_date"])
    headers["finish_date"] = to_utc(
        to_ct(
            parse_date_naive(parts["finish_date"]) + relativedelta(hours=23, minutes=30)
        )
    )


CHARGE_UNITS_LOOKUP = {
    "STDG": "days",
    "UNIT": "kwh",
    "AVAL": "kva",
    "EXAVAL": "kva",
    "MD": "kw",
    "LOADU": "kw",
    "SAG": "days",
    "TNUOS": "days",
    "REAP": "kvarh",
    "DCDA": "days",
    "MOP1": "days",
    "COMM": "days",
}

ELEMENT_LOOKUP = {
    "1ANNUAL": {"UNIT": "duos-red"},
    "2ANNUAL": {"UNIT": "duos-amber"},
    "3ANNUAL": {"UNIT": "duos-green"},
    "20RS0108": {"UNIT": "single"},
    "10ANNUAL": {
        "STDG": "standing",
        "DCDA": "dc",
    },
    "9ANNUAL": {"REAP": "duos-reactive"},
    "7ANNUAL": {"STDG": "duos-fixed"},
    "30ANNUAL": {"MOP1": "mop"},
    "50ANNUAL": {"COMM": "dc"},
    "9WANNUAL": {
        "STDG": "site-fee",
        "AVAL": "duos-availability",
    },
    "20RS0123": {"UNIT": "day"},
    "30RS0123": {"UNIT": "night"},
    "90ANNUAL": {"STDG": "duos-fixed"},
    "9QANNUAL": {"AVAL": "duos-availability"},
    "9UANNUAL": {"TNUOS": "tnuos"},
    "40ANNUAL": {"MD": "maximum-demand"},
    "20ANNUAL": {"LOADU": "triad"},
    "70ANNUAL": {"SAG": "elexon"},
    "10RS0050": {"UNIT": "duos-red"},
    "20RS0050": {"UNIT": "duos-amber"},
    "30RS0050": {"UNIT": "duos-red"},
    "9CANNUAL": {"REAP": "duos-reactive"},
    "40RS0050": {"UNIT": "duos-super-red"},
}


def _handle_0460(headers, pre_record, record):
    parts = _chop_record(
        record,
        unknown_1=12,
        unknown_2=12,
        code=8,
        quantity=12,
        units=22,
        rate=16,
        unknown_date=DATE_LENGTH,
        gbp=12,
        charge_description=35,
        unknown_3=51,
        days=2,
    )
    units_code = parts["units"].strip()
    units = CHARGE_UNITS_LOOKUP[units_code]
    gbp = Decimal(parts["gbp"]) / 100
    quantity = Decimal(parts["quantity"])
    rate = Decimal(parts["rate"])
    element_name = ELEMENT_LOOKUP[parts["code"].strip()][units_code]
    breakdown = headers["breakdown"]
    breakdown[f"{element_name}-{units}"] += quantity
    rate_name = f"{element_name}-rate"
    if rate_name in breakdown:
        rates = breakdown[rate_name]
    else:
        rates = breakdown[rate_name] = set()

    rates.add(rate)
    breakdown[f"{element_name}-gbp"] += gbp
    if element_name in ("duos-availability", "duos-excess-availability"):
        breakdown[f"{element_name}-days"] += Decimal(parts["days"])


CONSUMPTION_UNITS_LOOKUP = {"KWH": "kWh", "KVA": "kVA", "KVARH": "kVArh", "KW": "kW"}

REGISTER_CODE_LOOKUP = {"DAY": "00040", "NIGHT": "00206", "SINGLE": "00001"}

READ_TYPE_LOOKUP = {
    " ": "E",
    "E": "E",
    "N": "N",
    "S": "N",
}


def _handle_0461(headers, pre_record, record):
    parts = _chop_record(
        record,
        msn=11,
        unknown_1=2,
        prev_read_value=12,
        pres_read_value=12,
        coefficient=6,
        units=6,
        quantity=12,
        charge=6,
        prev_read_type=1,
        pres_read_type=1,
        mpan_core=13,
        mpan_top=8,
        register_code=19,
        pres_read_date=DATE_LENGTH,
        prev_read_date=DATE_LENGTH,
    )
    mpan_core = parse_mpan_core(parts["mpan_core"])
    headers["mpan_core"] = mpan_core
    units = CONSUMPTION_UNITS_LOOKUP[parts["units"].strip()]
    register_code = parts["register_code"].strip()
    if units == "kWh" and not (
        register_code.startswith("NOCHARGE") or register_code.endswith("XXXX")
    ):
        headers["kwh"] += Decimal(parts["quantity"])

    prev_read_date_str = parts["prev_read_date"].strip()
    if len(prev_read_date_str) > 0:
        tpr_code = REGISTER_CODE_LOOKUP[parts["register_code"].strip()]
        prev_type_code = READ_TYPE_LOOKUP[parts["prev_read_type"]]
        pres_type_code = READ_TYPE_LOOKUP[parts["pres_read_type"]]

        headers["reads"].append(
            {
                "msn": parts["msn"].strip(),
                "mpan": f"{parts['mpan_top']} {mpan_core}",
                "coefficient": Decimal(parts["coefficient"]),
                "units": units,
                "tpr_code": tpr_code,
                "prev_date": parse_date(parts["prev_read_date"]),
                "prev_value": Decimal(parts["prev_read_value"]),
                "prev_type_code": prev_type_code,
                "pres_date": parse_date(parts["pres_read_date"]),
                "pres_value": Decimal(parts["pres_read_value"]),
                "pres_type_code": pres_type_code,
            }
        )


def _handle_0470(headers, pre_record, record):
    pass


def _handle_0860(headers, pre_record, record):
    parts = _chop_record(
        record,
        metering_gbp=12,
        unknown_1=12,
        unknown_2=12,
        metering_date=DATE_LENGTH,
        description=80,
    )
    bd = headers["breakdown"]
    bd["metering-gbp"] += Decimal(parts["metering_gbp"]) / Decimal("100")


def _handle_1455(headers, pre_record, record):
    parts = _chop_record(
        record, ccl_kwh=13, unknown_1=10, ccl_rate=13, ccl_gbp=12, unkown_2=8
    )
    bd = headers["breakdown"]
    bd["ccl-kwh"] += Decimal(parts["ccl_kwh"])
    if "ccl-rate" in bd:
        ccl_rates = bd["ccl-rate"]
    else:
        ccl_rates = bd["ccl-rate"] = set()

    ccl_rates.add(Decimal(parts["ccl_rate"]) / Decimal("100"))
    bd["ccl-gbp"] += Decimal(parts["ccl_gbp"]) / Decimal("100")


def _handle_1460(headers, pre_record, record):
    parts = _chop_record(record, unknown_1=1, net=12, vat_rate=6, vat=12)
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
        unknown_3=10,
        unknown_4=10,
        unknown_5=20,
        unknown_6=10,
        unknown_7=10,
        unknown_8=20,
        gross=12,
        net=12,
        vat=12,
    )
    breakdown = headers["breakdown"]
    net = Decimal("0.00") + Decimal(parts["net"]) / Decimal("100")
    gross = Decimal("0.00") + Decimal(parts["gross"]) / Decimal("100")
    if "late_payment" in headers:
        late_payment_gbp = headers["late_payment"]
        net += late_payment_gbp
        gross += late_payment_gbp
        breakdown["late-payment-gbp"] += late_payment_gbp
        del headers["late_payment"]

    return {
        "bill_type_code": "W" if net < 0 else "N",
        "mpan_core": headers["mpan_core"],
        "account": headers["account"],
        "reference": headers["reference"],
        "issue_date": headers["issue_date"],
        "start_date": headers["start_date"],
        "finish_date": headers["finish_date"],
        "kwh": headers["kwh"],
        "net": net,
        "vat": Decimal("0.00") + Decimal(parts["vat"]) / Decimal("100"),
        "gross": gross,
        "breakdown": breakdown,
        "reads": headers["reads"],
    }


def _handle_1600(headers, pre_record, record):
    parts = _chop_record(
        record,
        unknown_1=12,
        unknown_2=12,
        late_payment_fee=12,
        late_payment_date=DATE_LENGTH,
        description=50,
    )
    late_payment_gbp = Decimal(parts["late_payment_fee"]) / Decimal(100)

    headers["breakdown"]["late-payment-gbp"] += late_payment_gbp


def _handle_1700(headers, pre_record, record):
    pass


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
    "0860": _handle_0860,
    "1455": _handle_1455,
    "1460": _handle_1460,
    "1500": _handle_1500,
    "1600": _handle_1600,
    "1700": _handle_1700,
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
