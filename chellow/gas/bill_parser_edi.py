from collections import defaultdict
from datetime import datetime as Datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest

from chellow.edi_lib import parse_edi, to_date, to_decimal
from chellow.utils import HH, to_ct, to_utc


READ_TYPE_MAP = {"00": "A", "01": "E", "02": "E"}

TCOD_MAP = {
    "Energy Bill Discount Scheme": {"PPK": "ebrs"},
    "Energy Bill Relief Scheme": {"PPK": "ebrs"},
    "Energy Bill Relief Scheme Discount": {"PPK": "ebrs"},
    "Unidentified Gas": {"PPK": "ug"},
    "Commodity": {"PPK": "commodity"},
    "Transportation": {"PPD": "transportation_fixed", "PPK": "transportation_variable"},
    "Gas Flexi": {"PPK": "commodity"},
    "Flex - Gas Flexi (New)": {"PPK": "commodity"},
    "Meter Reading": {"PPD": "meter_read"},
    "Meter Reading Credit Oct 19": {"FIX": "meter_read"},
    "Meter Rental": {"PPD": "metering"},
    "CCL": {"PPK": "ccl"},
    "Consumption Based Administration": {"PPK": "admin_variable"},
    "Swing": {"PPK": "swing"},
}

SUPPLIER_CODE_MAP = {
    "STD": "standing",
    "MET": "commodity",
    "CCL": "ccl",
}

UNIT_MAP = {"M3": "M3", "HH": "HCUF", "HCUF": "HCUF"}


def _to_finish_date(date_str):
    if len(date_str) == 0:
        return None
    return to_utc(
        to_ct(Datetime.strptime(date_str, "%y%m%d") + relativedelta(days=1) - HH)
    )


def _process_ADJ(elements, headers):
    adjf = elements["ADJF"]
    if adjf[0] == "CV":
        headers["cv"] = Decimal(adjf[1]) / Decimal(100000)


def _process_BCD(elements, headers):
    ivdt = elements["IVDT"]
    headers["issue_date"] = to_date(ivdt[0])

    invn = elements["INVN"]
    headers["reference"] = invn[0]

    btcd = elements["BTCD"]
    headers["bill_type_code"] = btcd[0]

    sumo = elements["SUMO"]
    start_date = to_date(sumo[0])
    if start_date is not None:
        headers["start_date"] = start_date

    if len(sumo) > 1:
        finish_date = _to_finish_date(sumo[1])
        if finish_date is not None:
            headers["finish_date"] = finish_date


def _process_MHD(elements, headers):
    headers.clear()

    typ = elements["TYPE"]
    message_type = headers["message_type"] = typ[0]
    if message_type == "UTLBIL":
        headers["reads"] = []
        headers["raw_lines"] = []
        headers["breakdown"] = defaultdict(int, {"units_consumed": Decimal(0)})
        headers["kwh"] = Decimal("0.00")
        headers["net"] = Decimal("0.00")
        headers["vat"] = Decimal("0.00")
        headers["gross"] = Decimal("0.00")


def _process_CCD1(elements, headers):
    mtnr = elements["MTNR"]
    msn = mtnr[0]

    mloc = elements["MLOC"]

    # Bug in EDI where MPRN missing in second CCD 1
    if "mprn" not in headers:
        headers["mprn"] = mloc[0]

    prdt = elements["PRDT"]
    pvdt = elements["PVDT"]

    pres_read_date = to_date(prdt[0])
    prev_read_date = to_date(pvdt[0])

    prrd = elements["PRRD"]
    pres_read_value = Decimal(prrd[0])
    pres_read_type = READ_TYPE_MAP[prrd[1]]
    prev_read_value = Decimal(prrd[2])
    prev_read_type = READ_TYPE_MAP[prrd[3]]

    conb = elements["CONB"]
    unit = UNIT_MAP[conb[1]]
    headers["breakdown"]["units_consumed"] += to_decimal(conb) / Decimal("1000")

    adjf = elements["ADJF"]
    correction_factor = Decimal(adjf[1]) / Decimal(100000)

    nuct = elements["NUCT"]

    headers["kwh"] += to_decimal(nuct) / Decimal("1000")

    headers["reads"].append(
        {
            "msn": msn,
            "unit": unit,
            "correction_factor": correction_factor,
            "prev_date": prev_read_date,
            "prev_value": prev_read_value,
            "prev_type_code": prev_read_type,
            "pres_date": pres_read_date,
            "pres_value": pres_read_value,
            "pres_type_code": pres_read_type,
        }
    )


NUCT_LOOKUP = {"DAY": "days", "KWH": "kwh"}


def _process_CCD2(elements, headers):
    breakdown = headers["breakdown"]
    ccde = elements["CCDE"]
    ccde_supplier_code = ccde[2]
    tcod = elements["TCOD"]
    nuct = elements["NUCT"]
    mtnr = elements["MTNR"]
    conb = elements["CONB"]
    adjf = elements["ADJF"]
    prdt = elements["PRDT"]
    pvdt = elements["PVDT"]
    prrd = elements["PRRD"]

    if len(tcod) > 1:
        tpref_lookup = TCOD_MAP[tcod[1]]
    else:
        tpref_lookup = SUPPLIER_CODE_MAP

    tpref = tpref_lookup[ccde_supplier_code]

    bpri = elements["BPRI"]
    if len(bpri[0]) > 0:
        rate_key = f"{tpref}_rate"
        if rate_key not in breakdown:
            breakdown[rate_key] = set()
        rate = Decimal(bpri[0]) / Decimal("10000000")
        breakdown[rate_key].add(rate)

    try:
        ctot = elements["CTOT"]
        breakdown[f"{tpref}_gbp"] += to_decimal(ctot) / Decimal("100")

        if len(nuct) > 1:
            key = NUCT_LOOKUP[nuct[1]]
        else:
            if ccde_supplier_code == "PPK":
                key = f"{tpref}_kwh"
            elif ccde_supplier_code == "PPD":
                key = f"{tpref}_days"

        breakdown[key] += to_decimal(nuct) / Decimal("1000")
    except KeyError:
        pass

    if "start_date" not in headers:
        csdt = elements["CSDT"]
        start_date = to_date(csdt[0])
        if start_date is not None:
            headers["start_date"] = start_date

    if "finish_date" not in headers:
        cedt = elements["CSDT"]
        finish_date = _to_finish_date(cedt[0])
        if finish_date is not None:
            headers["finish_date"] = finish_date

    if "mprn" not in headers:
        mloc = elements["MLOC"]
        headers["mprn"] = mloc[0]

    if len(conb) > 0 and len(conb[0]) > 0:
        headers["breakdown"]["units_consumed"] += to_decimal(conb) / Decimal("1000")

    if len(prrd) > 0 and len(prrd[0]) > 0:
        pres_read_date = to_date(prdt[0])
        prev_read_date = to_date(pvdt[0])

        pres_read_value = Decimal(prrd[0])
        pres_read_type = READ_TYPE_MAP[prrd[1]]
        prev_read_value = Decimal(prrd[2])
        prev_read_type = READ_TYPE_MAP[prrd[3]]
        msn = mtnr[0]
        unit = UNIT_MAP[conb[1]]
        correction_factor = Decimal(adjf[1]) / Decimal(100000)

        headers["reads"].append(
            {
                "msn": msn,
                "unit": unit,
                "correction_factor": correction_factor,
                "prev_date": prev_read_date,
                "prev_value": prev_read_value,
                "prev_type_code": prev_read_type,
                "pres_date": pres_read_date,
                "pres_value": pres_read_value,
                "pres_type_code": pres_read_type,
            }
        )


def _process_CCD3(elements, headers):
    breakdown = headers["breakdown"]
    ccde = elements["CCDE"]
    ccde_supplier_code = ccde[2]
    tcod = elements["TCOD"]

    tpref = TCOD_MAP[tcod[1]][ccde_supplier_code]

    bpri = elements["BPRI"]
    bpri_str = bpri[0]
    if len(bpri_str) > 0:
        rate_key = f"{tpref}_rate"
        if rate_key not in breakdown:
            breakdown[rate_key] = set()
        rate = Decimal(bpri_str) / Decimal("10000000")
        breakdown[rate_key].add(rate)

    nuct = elements["NUCT"]

    try:
        ctot = elements["CTOT"]
        breakdown[f"{tpref}_gbp"] += to_decimal(ctot) / Decimal("100")

        if ccde_supplier_code == "PPK":
            key = f"{tpref}_kwh"
        elif ccde_supplier_code == "PPD":
            key = f"{tpref}_days"

        breakdown[key] += to_decimal(nuct) / Decimal("1000")
    except KeyError:
        pass


def _process_CCD4(elements, headers):
    breakdown = headers["breakdown"]
    ccde = elements["ccde"]
    ccde_supplier_code = ccde[2]
    tcod = elements["TCOD"]

    tpref = TCOD_MAP[tcod[1]][ccde_supplier_code]

    bpri = elements["BPRI"]
    rate_key = f"{tpref}_rate"
    if rate_key not in breakdown:
        breakdown[rate_key] = set()
    rate = Decimal(bpri[0]) / Decimal("10000000")
    breakdown[rate_key].add(rate)

    nuct = elements["NUCT"]

    try:
        ctot = elements["CTOT"]
        breakdown[tpref + "_gbp"] += to_decimal(ctot) / Decimal("100")

        if ccde_supplier_code == "PPK":
            key = f"{tpref}_kwh"
        elif ccde_supplier_code == "PPD":
            key = f"{tpref}_days"

        breakdown[key] += to_decimal(nuct) / Decimal("1000")
    except KeyError:
        pass


def _process_MTR(elements, headers):
    if headers["message_type"] == "UTLBIL":
        breakdown = headers["breakdown"]
        for k, v in tuple(breakdown.items()):
            if isinstance(v, set):
                breakdown[k] = sorted(v)

        for read in headers["reads"]:
            read["calorific_value"] = headers["cv"]

        return {
            "raw_lines": "\n".join(headers["raw_lines"]),
            "mprn": headers["mprn"],
            "reference": headers["reference"],
            "account": headers["mprn"],
            "reads": headers["reads"],
            "kwh": headers["kwh"],
            "breakdown": headers["breakdown"],
            "net_gbp": headers["net"],
            "vat_gbp": headers["vat"],
            "gross_gbp": headers["gross"],
            "bill_type_code": headers["bill_type_code"],
            "start_date": headers["start_date"],
            "finish_date": headers["finish_date"],
            "issue_date": headers["issue_date"],
        }


def _process_VAT(elements, headers):
    breakdown = headers["breakdown"]
    vatp = elements["VATP"]
    if "vat" in breakdown:
        vat = breakdown["vat"]
    else:
        vat = breakdown["vat"] = {}

    vat_perc = to_decimal(vatp) / Decimal(1000)
    try:
        vat_bd = vat[vat_perc]
    except KeyError:
        vat_bd = vat[vat_perc] = defaultdict(int)

    uvtt = elements["UVTT"]
    vat_gbp = to_decimal(uvtt) / Decimal("100")

    vat_bd["vat"] += vat_gbp

    uvla = elements["UVLA"]
    net_gbp = to_decimal(uvla) / Decimal("100")
    vat_bd["net"] += net_gbp
    headers["net"] += net_gbp
    headers["vat"] += vat_gbp
    ucsi = elements["UCSI"]
    headers["gross"] += to_decimal(ucsi) / Decimal("100")


def _process_NOOP(elements, headers):
    pass


CODE_FUNCS = {
    "ADJ": _process_ADJ,
    "BCD": _process_BCD,
    "BTL": _process_NOOP,
    "CCD1": _process_CCD1,
    "CCD2": _process_CCD2,
    "CCD3": _process_CCD3,
    "CCD4": _process_CCD4,
    "CDT": _process_NOOP,
    "CLO": _process_NOOP,
    "END": _process_NOOP,
    "FIL": _process_NOOP,
    "MHD": _process_MHD,
    "MTR": _process_MTR,
    "SDT": _process_NOOP,
    "STX": _process_NOOP,
    "TYP": _process_NOOP,
    "TTL": _process_NOOP,
    "VAT": _process_VAT,
    "VTS": _process_NOOP,
}


class Parser:
    def __init__(self, file_bytes):
        self.edi_str = str(file_bytes, "utf-8", errors="ignore")
        self.line_number = None

    def make_raw_bills(self):
        bills = []
        headers = {}
        bill = None
        for self.line_number, line, seg_name, elements in parse_edi(self.edi_str):
            try:
                func = CODE_FUNCS[seg_name]
            except KeyError:
                raise BadRequest(f"Code {seg_name} not recognized.")
            try:
                bill = func(elements, headers)
            except BaseException as e:
                raise Exception(f"Propblem with segment {line}: {e}") from e

            if "raw_lines" in headers:
                headers["raw_lines"].append(line)
            if bill is not None:
                bills.append(bill)

        return bills
