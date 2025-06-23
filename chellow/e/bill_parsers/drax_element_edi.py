from collections import defaultdict
from decimal import Decimal


from werkzeug.exceptions import BadRequest

from chellow.edi_lib import (
    ct_datetime,
    parse_edi,
    to_date,
    to_decimal,
    to_finish_date,
    to_utc,
)
from chellow.utils import HH, parse_mpan_core


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


TMOD_MAP = {
    "139039": ("aahedc-gbp", "aahedc-rate", "aahedc-kwh"),
    "064305": ("fit-gbp", None, None),
    "590346": ("cfd-operational-gbp", None, None),
    "269100": ("bsuos-gbp", "bsuos-rate", "bsuos-kwh"),
    "422733": ("ccl-gbp", "ccl-rate", "ccl-kwh"),
    "273237": ("cfd-operational-gbp", "cfd-operational-rate", "cfd-operational-kwh"),
    "954379": ("cfd-interim-gbp", "cfd-interim-rate", "cfd-interim-kwh"),
    "538249": ("capaity-gbp", None, None),
    "568307": ("capacity-gbp", "capacity-rate", "capacity-kwh"),
    "020330": ("eii-gbp", None, None),
    "439724": ("eii-gbp", None, None),
    "247610": ("eii-gbp", None, None),
    "930504": ("eii-gbp", None, None),
    "331201": ("eii-gbp", None, None),
    "307253": ("eii-gbp", "eii-rate", "eii-kwh"),
    "065950": ("eii-gbp", "eii-rate", "eii-kwh"),
    "095469": ("meter-rental-gbp", "meter-rental-rate", "meter-rental-days"),
    "637050": ("meter-rental-gbp", "meter-rental-rate", "meter-rental-days"),
    "489920": ("elexon-gbp", "elexon-rate", "elexon-nbp-kwh"),
    "704107": ("fit-gbp", None, None),
    "019090": ("rego-gbp", "rego-rate", "rego-kwh"),
    "033667": ("management-gbp", "management-rate", "management-kwh"),
    "091890": ("shape-gbp", "shape-rate", "shape-kwh"),
    "122568": ("nrg-msp-gbp", "nrg-rate", "nrg-msp-kwh"),
    "716514": ("duos-amber-gbp", "duos-amber-rate", "duos-amber-kwh"),
    "769979": ("duos-red-gbp", "duos-red-rate", "duos-red-kwh"),
    "794486": ("capacity-gbp", "capacity-rate", "capacity-kwh"),
    "797790": ("duos-reactive-gbp", "duos-reactive-rate", "duos-reactive-kvarh"),
    "709522": (
        "duos-excess-availability-gbp",
        "duos-excess-availability-rate",
        "duos-excess-availability-kva",
    ),
    "644819": ("duos-fixed-gbp", "duos-fixed-rate", "duos-fixed-days"),
    "806318": ("duos-green-gbp", "duos-green-rate", "duos-green-kwh"),
    "209269": ("tnuos-gbp", "tnuos-rate", "tnuos-days"),
    "229128": ("ro-gbp", "ro-rate", "ro-kwh"),
    "012069": ("tnuos-gbp", None, None),
}

TPR_LOOKUP = {
    "Day": "00043",
    "Off Peak / Weekends": "00210",
    "Night": "00210",
    "Default Rate": "00043",
    "Single": "00210",
}


def _process_BCD(elements, headers):
    issue_date = to_date(elements["IVDT"][0])
    reference = elements["INVN"][0]
    bill_type_code = elements["BTCD"][0]

    headers["issue_date"] = issue_date
    headers["bill_type_code"] = bill_type_code
    headers["reference"] = reference


def _process_BTL(elements, headers):
    for bill in headers["bills"]:
        bill["mpan_core"] = headers["mpan_core"]
        bill["account"] = headers["account"]
        _customer_mods(headers, bill)
    return headers["bills"]


def _process_CCD1(elements, headers):
    tcod = elements["TCOD"]
    pres_read_date = to_finish_date(elements["PRDT"][0])

    prev_read_date = to_finish_date(elements["PVDT"][0])

    m = elements["MLOC"][0]
    mpan = " ".join((m[13:15], m[15:18], m[18:], m[:2], m[2:6], m[6:10], m[10:13]))

    prrd = elements["PRRD"]
    if len(prrd) < 4:
        return
    pres_read_type = read_type_map[prrd[1]]
    prev_read_type = read_type_map[prrd[3]]

    coefficient = Decimal(elements["ADJF"][1]) / Decimal(100000)
    pres_reading_value = Decimal(prrd[0])
    prev_reading_value = Decimal(prrd[2])
    msn = elements["MTNR"][0]
    tpr_code = elements["TMOD"][0]
    if tpr_code == "kW":
        units = "kW"
        tpr_code = None
    elif tpr_code == "kVA":
        units = "kVA"
        tpr_code = None
    else:
        units = "kWh"
        tpr_code = TPR_LOOKUP[tcod[1]]

    try:
        reads = headers["reads"]
    except KeyError:
        reads = headers["reads"] = []

    reads.append(
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
    breakdown = defaultdict(int)

    element_code = elements["TMOD"][0]
    headers["element_code"] = element_code
    try:
        eln_gbp, eln_rate, eln_cons = TMOD_MAP[element_code]
    except KeyError:
        raise BadRequest(f"Can't find the element code {element_code} in the TMOD_MAP.")

    cons = elements["CONS"]
    kwh = Decimal("0")
    if eln_cons is not None and len(cons[0]) > 0:
        el_cons = to_decimal(cons) / Decimal("1000")
        if eln_gbp == "duos-availability-gbp":
            breakdown[eln_cons] = [el_cons]
        else:
            breakdown[eln_cons] = kwh = el_cons

    if eln_rate is not None:
        rate = to_decimal(elements["BPRI"]) / Decimal("100000")
        breakdown[eln_rate] = [rate]

    start_date = to_date(elements["CSDT"][0])
    headers["bill_start_date"] = start_date

    finish_date = to_date(elements["CEDT"][0]) - HH
    headers["bill_finish_date"] = finish_date

    if "CTOT" in elements:
        net = Decimal("0.00") + to_decimal(elements["CTOT"]) / Decimal("100")
    else:
        net = Decimal("0.00")

    breakdown[eln_gbp] = net
    breakdown["raw-lines"] = [headers["line"]]

    try:
        reads = headers["reads"]
        headers["reads"] = []
    except KeyError:
        reads = []

    bill = {
        "bill_type_code": headers["bill_type_code"],
        "reference": headers["reference"] + "_" + eln_gbp[:-4],
        "issue_date": headers["issue_date"],
        "start_date": start_date,
        "finish_date": finish_date,
        "kwh": kwh if eln_gbp == "ro-gbp" else Decimal("0"),
        "net": net,
        "vat": Decimal("0.00"),
        "gross": net,
        "breakdown": breakdown,
        "reads": reads,
    }
    headers["bills"].append(bill)


def _process_CCD3(elements, headers):
    breakdown = defaultdict(int)

    element_code = elements["TMOD"][0]
    headers["element_code"] = element_code
    try:
        eln_gbp, eln_rate, eln_cons = TMOD_MAP[element_code]
    except KeyError:
        raise BadRequest(f"Can't find the element code {element_code} in the TMOD_MAP.")

    cons = elements["CONS"]
    if eln_cons is not None and len(cons[0]) > 0:
        el_cons = to_decimal(cons) / Decimal("1000")
        breakdown[eln_cons] = kwh = el_cons
    else:
        kwh = Decimal("0")

    bpri = elements["BPRI"]
    if len(bpri[0]) > 0:
        rate = to_decimal(bpri) / Decimal("100000")
        breakdown[eln_rate] = [rate]

    start_date = to_date(elements["CSDT"][0])
    headers["bill_start_date"] = start_date

    finish_date = to_date(elements["CEDT"][0]) - HH
    headers["bill_finish_date"] = finish_date

    if "CTOT" in elements:
        net = Decimal("0.00") + to_decimal(elements["CTOT"]) / Decimal("100")
    else:
        net = Decimal("0.00")

    breakdown[eln_gbp] = net
    breakdown["raw-lines"] = [headers["line"]]

    try:
        reads = headers["reads"]
        headers["reads"] = []
    except KeyError:
        reads = []

    bill = {
        "bill_type_code": headers["bill_type_code"],
        "issue_date": headers["issue_date"],
        "reference": headers["reference"] + "_" + eln_gbp[:-4],
        "start_date": start_date,
        "finish_date": finish_date,
        "net": net,
        "kwh": kwh if eln_gbp == "ro-gbp" else Decimal("0"),
        "vat": Decimal("0.00"),
        "gross": net,
        "breakdown": breakdown,
        "reads": reads,
    }

    headers["bills"].append(bill)


def _process_CCD4(elements, headers):
    breakdown = defaultdict(int)

    element_code = elements["TMOD"][0]
    headers["element_code"] = element_code
    try:
        eln_gbp, eln_rate, eln_cons = TMOD_MAP[element_code]
    except KeyError:
        raise BadRequest(f"Can't find the element code {element_code} in the TMOD_MAP.")

    cons = elements["CONS"]
    if eln_cons is not None and len(cons[0]) > 0:
        el_cons = to_decimal(cons, "1000")
        breakdown[eln_cons] = kwh = el_cons

    if eln_rate is not None:
        rate = to_decimal(elements["BPRI"], "100000")
        breakdown[eln_rate] = [rate]

    start_date = to_date(elements["CSDT"][0])
    headers["bill_start_date"] = start_date

    finish_date = to_date(elements["CEDT"][0]) - HH
    headers["bill_finish_date"] = finish_date

    if "CTOT" in elements:
        net = Decimal("0.00") + to_decimal(elements["CTOT"], "100")
    else:
        net = Decimal("0.00")

    breakdown[eln_gbp] = net
    breakdown["raw-lines"] = [headers["line"]]

    try:
        reads = headers["reads"]
        del headers["reads"][:]
    except KeyError:
        reads = []

    bill = {
        "kwh": kwh if eln_gbp == "ro-gbp" else Decimal("0.00"),
        "reference": headers["reference"] + "_" + eln_gbp[:-4],
        "issue_date": headers["issue_date"],
        "start_date": start_date,
        "finish_date": finish_date,
        "net": net,
        "vat": Decimal("0.00"),
        "gross": net,
        "breakdown": breakdown,
        "reads": reads,
        "bill_type_code": headers["bill_type_code"],
    }
    headers["bills"].append(bill)


def _process_CDT(elements, headers):
    customer_id = elements["CIDN"][0]
    headers["customer_number"] = customer_id


def _process_CLO(elements, headers):
    cloc = elements["CLOC"]
    headers["account"] = cloc[1]


def _process_END(elements, headers):
    pass


def _process_MAN(elements, headers):
    madn = elements["MADN"]

    headers["mpan_core"] = parse_mpan_core("".join(madn[0:3]))


def _process_MHD(elements, headers):
    message_type = elements["TYPE"][0]
    if message_type == "UTLBIL":
        keep_keys = {"customer_number"}
        keep = {k: headers[k] for k in keep_keys}
        headers.clear()
        headers.update(keep)
        headers["bills"] = []


def _process_MTR(elements, headers):
    pass


def _process_VAT(elements, headers):
    vat = Decimal("0.00") + to_decimal(elements["UVTT"]) / Decimal("100")
    vat_percentage = to_decimal(elements["VATP"]) / Decimal("1000")
    vat_net = Decimal("0.00") + to_decimal(elements["UVLA"]) / Decimal("100")

    bill = {
        "bill_type_code": headers["bill_type_code"],
        "account": headers["account"],
        "mpan_core": headers["mpan_core"],
        "reference": headers["reference"] + "_vat",
        "issue_date": headers["issue_date"],
        "start_date": headers["bill_start_date"],
        "finish_date": headers["bill_finish_date"],
        "kwh": Decimal("0.00"),
        "net": Decimal("0.00"),
        "vat": vat,
        "gross": vat,
        "breakdown": {
            "raw-lines": [headers["line"]],
            "vat": {vat_percentage: {"vat": vat, "net": vat_net}},
        },
        "reads": [],
    }
    headers["bills"].append(bill)


def _process_NOOP(elements, headers):
    pass


CODE_FUNCS = {
    "BCD": _process_BCD,
    "BTL": _process_BTL,
    "CCD1": _process_CCD1,
    "CCD2": _process_CCD2,
    "CCD3": _process_CCD3,
    "CCD4": _process_CCD4,
    "CDT": _process_CDT,
    "CLO": _process_CLO,
    "DNA": _process_NOOP,
    "END": _process_END,
    "FIL": _process_NOOP,
    "MAN": _process_MAN,
    "MHD": _process_MHD,
    "MTR": _process_MTR,
    "SDT": _process_NOOP,
    "STX": _process_NOOP,
    "TYP": _process_NOOP,
    "TTL": _process_NOOP,
    "VAT": _process_VAT,
    "VTS": _process_NOOP,
}


def _customer_mods(headers, bill):
    if headers["customer_number"] == "WESSEXWAT":
        if (
            headers["element_code"] == "307660"
            and "ro-gbp" in bill["breakdown"]
            and bill["issue_date"] == to_utc(ct_datetime(2023, 4, 14))
            and bill["start_date"] == to_utc(ct_datetime(2023, 3, 1))
            and bill["finish_date"] == to_utc(ct_datetime(2023, 3, 31, 23, 30))
        ):
            bill["start_date"] = to_utc(ct_datetime(2021, 4, 1))
            bill["finish_date"] = to_utc(ct_datetime(2022, 3, 31, 23, 30))

    return bill


class Parser:
    def __init__(self, f):
        self.edi_str = str(f.read(), "utf-8", errors="ignore")
        self.line_number = None

    def make_raw_bills(self):
        bills = []
        headers = {"bills": []}
        for self.line_number, line, seg_name, elements in parse_edi(self.edi_str):
            headers["line"] = line
            try:
                func = CODE_FUNCS[seg_name]
            except KeyError:
                raise BadRequest(f"Code {seg_name} not recognized.")

            try:
                bills_chunk = func(elements, headers)
            except BadRequest as e:
                raise BadRequest(
                    f"{e.description} on line {self.line_number} line {line} "
                    f"seg_name {seg_name} elements {elements}"
                )
            except BaseException as e:
                raise BadRequest(
                    f"{e} on line {self.line_number} line {line} "
                    f"seg_name {seg_name} elements {elements}"
                ) from e

            if bills_chunk is not None:
                bills.extend(bills_chunk)

        return bills
