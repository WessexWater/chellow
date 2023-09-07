from collections import defaultdict
from decimal import Decimal

from werkzeug.exceptions import BadRequest

from chellow.edi_lib import parse_edi, to_ct_date, to_date, to_decimal, to_finish_date
from chellow.models import Era, Session
from chellow.utils import HH, ct_datetime, parse_mpan_core


read_type_map = {
    "00": "N",
    "09": "N3",
    "04": "C",
    "02": "E",
    "11": "E3",
    "01": "EM",
    "03": "W",
    "06": "X",
    "05": "CP",
    "12": "IF",
}


def _process_BCD(elements, headers):
    ivdt = elements["IVDT"]
    headers["issue_date"] = to_date(ivdt[0])

    invn = elements["INVN"]
    reference = invn[0]
    headers["reference"] = reference

    btcd = elements["BTCD"]
    headers["bill_type_code"] = btcd[0]

    sumo = elements["SUMO"]
    headers["start_date"] = to_date(sumo[0])
    headers["is_ebatch"] = to_ct_date(sumo[1]) in (
        ct_datetime(2020, 4, 1),
        ct_datetime(2020, 3, 16),
    )
    if headers["is_ebatch"]:
        headers["finish_date"] = to_date(sumo[1]) - HH
    else:
        headers["finish_date"] = to_finish_date(sumo[1])


def _process_MHD(elements, headers):
    message_type = elements["TYPE"][0]
    sess = headers["sess"]
    if message_type == "UTLBIL":
        headers.clear()
        headers["kwh"] = Decimal("0")
        headers["reads"] = []
        headers["breakdown"] = defaultdict(int, {"raw-lines": []})
        headers["bill_elements"] = []
        headers["errors"] = []
        headers["sess"] = sess
        headers["mpan_core"] = None
        headers["account"] = None
        headers["is_ebatch"] = False
        headers["bill_type_code"] = None
        headers["reference"] = None
        headers["issue_date"] = None
        headers["start_date"] = None
        headers["finish_date"] = None
        headers["net"] = Decimal("0.00")
        headers["vat"] = Decimal("0.00")
        headers["gross"] = Decimal("0.00")
    headers["message_type"] = message_type


def _process_CCD1(elements, headers):
    prdt = elements["PRDT"]
    pvdt = elements["PVDT"]

    pres_read_date = to_finish_date(prdt[0])
    prev_read_date = to_finish_date(pvdt[0])

    tmod = elements["TMOD"]
    mtnr = elements["MTNR"]
    mloc = elements["MLOC"]

    mpan = mloc[0]
    mpan_core = parse_mpan_core(f"{mpan[:2]}{mpan[2:6]}{mpan[6:10]}{mpan[10:13]}")
    headers["mpan_core"] = mpan_core
    mpan = f"{mpan[13:15]} {mpan[15:18]} {mpan[18:]} {mpan_core}"

    prrd = elements["PRRD"]
    pres_read_type = read_type_map[prrd[1]]
    prev_read_type = read_type_map[prrd[3]]

    adjf = elements["ADJF"]

    coefficient = Decimal(adjf[1]) / Decimal(100000)
    pres_reading_value = Decimal(prrd[0])
    prev_reading_value = Decimal(prrd[2])
    msn = mtnr[0]
    tpr_code = tmod[0]
    if tpr_code == "kW":
        units = "kW"
        tpr_code = None
    elif tpr_code == "kVA":
        units = "kVA"
        tpr_code = None
    else:
        units = "kWh"

    headers["reads"].append(
        {
            "msn": msn,
            "mpan": mpan,
            "coefficient": coefficient,
            "units": units,
            "tpr_code": tpr_code,
            "prev_date": prev_read_date,
            "prev_value": prev_reading_value,
            "prev_type_code": prev_read_type,
            "pres_date": pres_read_date,
            "pres_value": pres_reading_value,
            "pres_type_code": pres_read_type,
        }
    )


def _process_CCD2(elements, headers):
    tmod = elements["TMOD"]
    mtnr = elements["MTNR"]
    mloc = elements["MLOC"]

    mpan = mloc[0]
    mpan_core = parse_mpan_core(f"{mpan[:2]}{mpan[2:6]}{mpan[6:10]}{mpan[10:13]}")
    mpan = f"{mpan[13:15]} {mpan[15:18]} {mpan[18:]} {mpan_core}"

    prdt = elements["PRDT"]
    pvdt = elements["PVDT"]

    pres_read_date = to_finish_date(prdt[0])
    prev_read_date = to_finish_date(pvdt[0])

    prrd = elements["PRRD"]
    pres_read_type = read_type_map[prrd[1]]
    prev_read_type = read_type_map[prrd[3]]

    adjf = elements["ADJF"]
    cona = elements["CONA"]

    coefficient = Decimal(adjf[1]) / Decimal(100000)
    pres_reading_value = Decimal(prrd[0])
    prev_reading_value = Decimal(prrd[2])
    msn = mtnr[0]
    tpr_code = tmod[0]
    if tpr_code == "kW":
        units = "kW"
        tpr_code = None
        prefix = "md-"
    elif tpr_code == "kVA":
        units = "kVA"
        tpr_code = None
        prefix = "md-"
    else:
        units = "kWh"
        headers["kwh"] += to_decimal(cona) / Decimal("1000")
        prefix = tpr_code + "-"

    nuct = elements["NUCT"]
    breakdown = headers["breakdown"]
    breakdown[prefix + "kwh"] += to_decimal(nuct) / Decimal("1000")
    cppu = elements["CPPU"]
    rate_key = prefix + "rate"
    if rate_key not in breakdown:
        breakdown[rate_key] = set()
    breakdown[rate_key].add(to_decimal(cppu) / Decimal("100000"))
    ctot = elements["CTOT"]
    breakdown[prefix + "gbp"] += to_decimal(ctot) / Decimal("100")

    headers["reads"].append(
        {
            "msn": msn,
            "mpan": mpan,
            "coefficient": coefficient,
            "units": units,
            "tpr_code": tpr_code,
            "prev_date": prev_read_date,
            "prev_value": prev_reading_value,
            "prev_type_code": prev_read_type,
            "pres_date": pres_read_date,
            "pres_value": pres_reading_value,
            "pres_type_code": pres_read_type,
        }
    )


def _decimal(elements, element_name):
    try:
        return to_decimal(elements[element_name])
    except BadRequest as e:
        raise BadRequest(f"For element {element_name}: {e.description}")


def _process_CCD3(elements, headers):
    breakdown = headers["breakdown"]

    tcod = elements["TCOD"]
    tcod0 = tcod[1]
    tmod = elements["TMOD"]
    tmod0 = tmod[0]
    ignore_rate = ignore_kwh = False
    if tmod0 == "422733":
        prefix = "ccl"
    elif tmod0 == "493988":
        prefix = "reconciliation"
    elif tmod0 == "761963":
        prefix = "reconciliation"
        ignore_rate = ignore_kwh = True
    elif tmod0 == "700285":
        prefix = "standing"
    elif tmod0 in ("823408", "504364"):
        prefix = "ebrs"
    elif tmod0 == "893084":
        prefix = "ebrs"
        ignore_rate = ignore_kwh = True
    else:
        if tcod0 == "Energy and Trade Intensive Industries":
            prefix = "ebrs"
            ignore_rate = ignore_kwh = True
        elif tcod0 in (
            "Energy Bill Discount Scheme",
            "Energy Bill Relief Scheme Discount",
        ):
            prefix = "ebrs"
        else:
            prefix = tmod0

    if not ignore_kwh and "NUCT" in elements and len(elements["NUCT"][0]) > 0:
        kwh = _decimal(elements, "NUCT") / Decimal("1000")
        breakdown[f"{prefix}-kwh"] += kwh
        if prefix == tmod0:
            headers["kwh"] += kwh

    if not ignore_rate and "CPPU" in elements and len(elements["CPPU"][0]) > 0:
        rate_key = f"{prefix}-rate"
        if rate_key not in breakdown:
            breakdown[rate_key] = set()
        breakdown[rate_key].add(_decimal(elements, "CPPU") / Decimal("100000"))

    if "CTOT" in elements:
        breakdown[f"{prefix}-gbp"] += _decimal(elements, "CTOT") / Decimal("100")


def _process_CCD4(elements, headers):
    ndrp = elements["NDRP"]
    breakdown = headers["breakdown"]
    if len(ndrp[0]) > 0:
        breakdown["standing-days"] += to_decimal(ndrp)
    ctot = elements["CTOT"]
    if len(ctot[0]) > 0:
        breakdown["standing-gbp"] += to_decimal(ctot) / Decimal("100")


def _process_CLO(elements, headers):
    cloc = elements["CLOC"]
    headers["account"] = cloc[1]


def _process_MTR(elements, headers):
    if headers["message_type"] == "UTLBIL":
        if headers["mpan_core"] is None:
            sess = headers["sess"]
            era = (
                sess.query(Era)
                .filter(Era.imp_supplier_account == headers["account"])
                .first()
            )
            if era is not None:
                headers["mpan_core"] = era.imp_mpan_core
            sess.close()

        reads = headers["reads"]
        if headers["is_ebatch"]:
            for r in headers["reads"]:
                if r["pres_type_code"] == "C":
                    r["pres_type_code"] = "E"

        dup_reads = set()
        new_reads = []
        for r in reads:
            k = tuple(v for n, v in sorted(r.items()))
            if k in dup_reads:
                continue
            dup_reads.add(k)
            new_reads.append(r)

        raw_bill = {
            "bill_type_code": headers["bill_type_code"],
            "account": headers["account"],
            "mpan_core": headers["mpan_core"],
            "reference": headers["reference"],
            "issue_date": headers["issue_date"],
            "start_date": headers["start_date"],
            "finish_date": headers["finish_date"],
            "kwh": headers["kwh"],
            "net": headers["net"],
            "vat": headers["vat"],
            "gross": headers["gross"],
            "breakdown": headers["breakdown"],
            "reads": new_reads,
        }
        return raw_bill


def _process_MAN(elements, headers):
    madn = elements["MADN"]
    headers["mpan_core"] = parse_mpan_core("".join((madn[0], madn[1], madn[2])))


def _process_VAT(elements, headers):
    uvla = elements["UVLA"]
    net = Decimal("0.00") + to_decimal(uvla) / Decimal("100")
    headers["net"] += net
    uvtt = elements["UVTT"]
    vat = Decimal("0.00") + to_decimal(uvtt) / Decimal("100")
    headers["vat"] += vat
    ucsi = elements["UCSI"]
    headers["gross"] += Decimal("0.00") + to_decimal(ucsi) / Decimal("100")
    vat_percentage = to_decimal(elements["VATP"]) / Decimal("1000")
    bd = headers["breakdown"]
    if "vat" in bd:
        vat_breakdown = bd["vat"]
    else:
        vat_breakdown = bd["vat"] = {}

    try:
        vat_values = vat_breakdown[vat_percentage]
    except KeyError:
        vat_values = vat_breakdown[vat_percentage] = {
            "vat": Decimal("0.00"),
            "net": Decimal("0.00"),
        }
    vat_values["vat"] += vat
    vat_values["net"] += net


def _process_NOOP(elements, headers):
    pass


CODE_FUNCS = {
    "BCD": _process_BCD,
    "BTL": _process_NOOP,
    "CCD1": _process_CCD1,
    "CCD2": _process_CCD2,
    "CCD3": _process_CCD3,
    "CCD4": _process_CCD4,
    "CDA": _process_NOOP,
    "CDT": _process_NOOP,
    "CLO": _process_CLO,
    "DNA": _process_NOOP,
    "END": _process_NOOP,
    "FIL": _process_NOOP,
    "MAN": _process_MAN,
    "MHD": _process_MHD,
    "MTR": _process_MTR,
    "REF": _process_NOOP,
    "SDT": _process_NOOP,
    "STX": _process_NOOP,
    "TYP": _process_NOOP,
    "TTL": _process_NOOP,
    "VAT": _process_VAT,
    "VTS": _process_NOOP,
}


class Parser:
    def __init__(self, f):
        self.edi_str = str(f.read(), "utf-8", errors="ignore")
        self.line_number = None

    def make_raw_bills(self):
        bills = []
        bill = None
        with Session() as sess:
            headers = {"sess": sess}
            for self.line_number, line, seg_name, elements in parse_edi(self.edi_str):
                try:
                    func = CODE_FUNCS[seg_name]
                except KeyError:
                    raise BadRequest(f"Code {seg_name} not recognized.")

                try:
                    bill = func(elements, headers)
                except BadRequest as e:
                    raise BadRequest(
                        f"{e.description} on line {self.line_number} line {line} "
                        f"seg_name {seg_name} elements {elements}"
                    )

                if "breakdown" in headers:
                    headers["breakdown"]["raw-lines"].append(line)

                if bill is not None:
                    bills.append(bill)

        return bills
