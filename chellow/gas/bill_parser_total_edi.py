from collections import defaultdict
from datetime import datetime as Datetime
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from sqlalchemy import select

from werkzeug.exceptions import BadRequest

from chellow.edi_lib import parse_edi, to_date, to_decimal
from chellow.models import GEra, Session
from chellow.utils import HH, to_ct, to_utc

# From Total 2024-05-29
# ReadType == "C"  = "00"
# ReadType == "N" = "00"
# ReadType == "A" = "00"
# ReadType == "PA" = "00"
# ReadType == "S"  = "00"
# ReadType == "I"  = "00"
# ReadType == "E" = "02"
# ReadType == "AE"  = "02"
# ReadType == "M"  = "02"
# ReadType == "PE"  = "02"

READ_TYPE_MAP = {"00": "A", "02": "E"}


SUPPLIER_CODE_MAP = {
    "STD": ("standing", Decimal("1000"), Decimal("1")),
    "MET": ("commodity", Decimal("100000"), Decimal("1000")),
    "CCL": ("ccl", Decimal("100000"), Decimal("1000")),
    "SUN": ("sundry", Decimal("1000"), Decimal("100")),
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
        headers["reads"][-1]["calorific_value"] = Decimal(adjf[1]) / Decimal(100000)


def _process_BCD(elements, headers):
    ivdt = elements["IVDT"]
    headers["issue_date"] = to_date(ivdt[0])

    invn = elements["INVN"]
    headers["reference"] = invn[0]

    btcd = elements["BTCD"]
    headers["bill_type_code"] = btcd[0]


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


NUCT_LOOKUP = {"DAY": "days", "KWH": "kwh"}


def _process_CCD2(elements, headers):
    breakdown = headers["breakdown"]
    ccde = elements["CCDE"]
    nuct = elements["NUCT"]
    mtnr = elements["MTNR"]
    conb = elements["CONB"]
    adjf = elements["ADJF"]
    prdt = elements["PRDT"]
    pvdt = elements["PVDT"]
    prrd = elements["PRRD"]
    cppu = elements["CPPU"]
    ctot = elements["CTOT"]
    csdt = elements["CSDT"]
    cedt = elements["CEDT"]
    mloc = elements["MLOC"]

    ccde_supplier_code = ccde[2]
    tpref, rate_divisor, units_divisor = SUPPLIER_CODE_MAP[ccde_supplier_code]

    rate_str = cppu[0]

    rate_key = f"{tpref}_rate"
    if rate_key not in breakdown:
        breakdown[rate_key] = set()
    rate = Decimal(rate_str) / rate_divisor
    breakdown[rate_key].add(rate)

    breakdown[f"{tpref}_gbp"] += to_decimal(ctot) / Decimal("100")

    suff = NUCT_LOOKUP[nuct[1].strip()]
    key = f"{tpref}_{suff}"
    units_billed = to_decimal(nuct) / units_divisor
    breakdown[key] += units_billed

    start_date = to_date(csdt[0])
    if start_date is not None and (tpref == "standing" or "start_date" not in headers):
        headers["start_date"] = start_date

    finish_date = _to_finish_date(cedt[0])
    if finish_date is not None and (
        tpref == "standing" or "finish_date" not in headers
    ):
        headers["finish_date"] = finish_date

    mprn = mloc[0]
    if "mprn" not in headers and len(mprn) > 0:
        headers["mprn"] = mprn

    if len(conb) > 0 and len(conb[0]) > 0:
        headers["breakdown"]["units_consumed"] += to_decimal(conb) / Decimal("1000")

    if tpref == "commodity":
        headers["kwh"] += units_billed

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
    nuct = elements["NUCT"]
    mtnr = elements["MTNR"]
    conb = elements["CONB"]
    adjf = elements["ADJF"]
    prdt = elements["PRDT"]
    pvdt = elements["PVDT"]
    prrd = elements["PRRD"]
    cppu = elements["CPPU"]
    ctot = elements["CTOT"]
    csdt = elements["CSDT"]
    cedt = elements["CEDT"]
    mloc = elements["MLOC"]

    ccde_supplier_code = ccde[2]
    tpref, rate_divisor, units_divisor = SUPPLIER_CODE_MAP[ccde_supplier_code]

    rate_str = cppu[0]
    if len(rate_str.strip()) > 0:
        rate_key = f"{tpref}_rate"
        if rate_key not in breakdown:
            breakdown[rate_key] = set()
        rate = Decimal(rate_str) / rate_divisor
        breakdown[rate_key].add(rate)

    breakdown[f"{tpref}_gbp"] += to_decimal(ctot) / Decimal("100")

    if len(nuct) > 1:
        suff = NUCT_LOOKUP[nuct[1].strip()]
        key = f"{tpref}_{suff}"
        units_billed = to_decimal(nuct) / units_divisor
        breakdown[key] += units_billed

    start_date = to_date(csdt[0])
    if start_date is not None and (tpref == "standing" or "start_date" not in headers):
        headers["start_date"] = start_date

    finish_date = _to_finish_date(cedt[0])
    if finish_date is not None and (
        tpref == "standing" or "finish_date" not in headers
    ):
        headers["finish_date"] = finish_date

    mprn = mloc[0]
    if "mprn" not in headers and len(mprn) > 0:
        headers["mprn"] = mprn

    if len(conb) > 0 and len(conb[0]) > 0:
        headers["breakdown"]["units_consumed"] += to_decimal(conb) / Decimal("1000")

    if tpref == "commodity":
        headers["kwh"] += units_billed

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


def _process_CLO(elements, headers):
    cloc = elements["CLOC"]
    headers["account"] = cloc[2]


def _process_MTR(elements, headers):
    if headers["message_type"] == "UTLBIL":
        breakdown = headers["breakdown"]
        for k, v in tuple(breakdown.items()):
            if isinstance(v, set):
                breakdown[k] = sorted(v)

        account = headers["account"]
        try:
            mprn = headers["mprn"]
        except KeyError:
            with Session() as sess:
                g_era = sess.scalars(
                    select(GEra)
                    .where(GEra.account == account)
                    .order_by(GEra.start_date)
                ).first()
                if g_era is None:
                    raise BadRequest(
                        f"Couldn't find an MPRN, and then couldn't fine a supply "
                        f"with account {account}."
                    )
                else:
                    mprn = g_era.g_supply.mprn

        start_date = headers["start_date"]
        if "finish_date" in headers:
            finish_date = headers["finish_date"]
        else:
            finish_date = start_date

        return {
            "raw_lines": "\n".join(headers["raw_lines"]),
            "mprn": mprn,
            "reference": headers["reference"],
            "account": account,
            "reads": headers["reads"],
            "kwh": headers["kwh"],
            "breakdown": headers["breakdown"],
            "net_gbp": headers["net"],
            "vat_gbp": headers["vat"],
            "gross_gbp": headers["gross"],
            "bill_type_code": headers["bill_type_code"],
            "start_date": start_date,
            "finish_date": finish_date,
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
    "CCD1": _process_NOOP,
    "CCD2": _process_CCD2,
    "CCD3": _process_CCD3,
    "CCD4": _process_NOOP,
    "CDT": _process_NOOP,
    "CLO": _process_CLO,
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
