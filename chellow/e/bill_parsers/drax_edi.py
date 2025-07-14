from collections import defaultdict
from decimal import Decimal


from werkzeug.exceptions import BadRequest

from chellow.edi_lib import parse_edi, to_date, to_decimal, to_finish_date
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

ELEMENT_MAP = {
    "AAH": {
        "AAHEDC": {
            "139039": ("aahedc-gbp", "aahedc-rate", "aahedc-kwh"),
        },
    },
    "ADH": {
        "ADHOC": {
            "020330": ("eii-gbp", None, None),
            "637050": ("meter-rental-gbp", "meter-rental-rate", "meter-rental-days"),
        },
    },
    "BUS": {
        "BSUOS": {
            "269100": ("bsuos-gbp", "bsuos-rate", "bsuos-kwh"),
        },
    },
    "CCL": {
        "CCL": {
            "422733": ("ccl-gbp", "ccl-rate", "ccl-kwh"),
        },
    },
    "CFD": {
        "CFD001": {
            "273237": (
                "cfd-operational-gbp",
                "cfd-operational-rate",
                "cfd-operational-kwh",
            ),
            "954379": ("cfd-interim-gbp", "cfd-interim-rate", "cfd-interim-kwh"),
            "538249": (
                "cm-settlement-levy-gbp",
                "cm-settlement-levy-rate",
                "cm-settlement-levy-kwh",
            ),
            "568307": ("capacity-gbp", "capacity-rate", "capacity-kwh"),
        },
    },
    "DCA": {
        "DCDA": {
            "095469": ("meter-rental-gbp", "meter-rental-rate", "meter-rental-days"),
        },
    },
    "DUS": {
        "DUS001": {
            "794486": (
                "duos-availability-gbp",
                "duos-availability-rate",
                "duos-availability-kva",
            ),
            "644819": ("duos-fixed-gbp", "duos-fixed-rate", "duos-fixed-days"),
            "797790": (
                "duos-reactive-gbp",
                "duos-reactive-rate",
                "duos-reactive-kvarh",
            ),
            "806318": ("duos-green-gbp", "duos-green-rate", "duos-green-kwh"),
            "716514": ("duos-amber-gbp", "duos-amber-rate", "duos-amber-kwh"),
            "769979": ("duos-red-gbp", "duos-red-rate", "duos-red-kwh"),
            "709522": (
                "duos-excess-availability-gbp",
                "duos-excess-availability-rate",
                "duos-excess-availability-kva",
            ),
            "209269": ("tnuos-gbp", "tnuos-rate", "tnuos-days"),
        },
        "DUS002": {
            "797790": (
                "duos-reactive-gbp",
                "duos-reactive-rate",
                "duos-reactive-kvarh",
            ),
            "806318": ("duos-green-gbp", "duos-green-rate", "duos-green-kwh"),
            "716514": ("duos-amber-gbp", "duos-amber-rate", "duos-amber-kwh"),
            "709522": (
                "duos-excess-availability-gbp",
                "duos-excess-availability-rate",
                "duos-excess-availability-kva",
            ),
            "769979": ("duos-red-gbp", "duos-red-rate", "duos-red-kwh"),
            "644819": ("duos-fixed-gbp", "duos-fixed-rate", "duos-fixed-days"),
            "794486": (
                "duos-availability-gbp",
                "duos-availability-rate",
                "duos-availability-kva",
            ),
            "209269": ("tnuos-gbp", "tnuos-rate", "tnuos-days"),
            "065950": ("eii-gbp", "eii-rate", "eii-kwh"),
        },
        "DUSDIS": {
            "122568": ("nrg-gsp-losses-gbp", "nrg-rate", "nrg-gsp-losses-kwh"),
        },
        "DUSTRN": {
            "122568": ("nrg-nbp-losses-gbp", "nrg-rate", "nrg-nbp-losses-kwh"),
        },
    },
    "ELX": {
        "ELEXON": {
            "489920": ("elexon-gbp", "elexon-rate", "elexon-nbp-kwh"),
        },
    },
    "FIT": {
        "FIT_LV": {
            "704107": ("fit-gbp", "fit-rate", "fit-kwh"),
        },
    },
    "NRG": {
        "HH0002": {
            "033667": ("management-gbp", "management-rate", "management-kwh"),
            "091890": ("shape-gbp", "shape-rate", "shape-kwh"),
            "122568": ("nrg-msp-gbp", "nrg-rate", "nrg-msp-kwh"),
        },
    },
    "REN": {
        "REN001": {
            "229128": ("ro-gbp", "ro-rate", "ro-kwh"),
        },
        "REN002": {
            "019090": ("rego-gbp", "rego-rate", "rego-kwh"),
        },
    },
    "TUS": {
        "TNUOS": {
            "012069": ("triad-gbp", "triad-rate", "triad-kw"),
        },
    },
    "064305": ("fit-gbp", None, None),
    "590346": ("cfd-operational-gbp", None, None),
    "439724": ("eii-gbp", None, None),
    "247610": ("eii-gbp", None, None),
    "930504": ("eii-gbp", None, None),
    "331201": ("eii-gbp", None, None),
    "307253": ("eii-gbp", "eii-rate", "eii-kwh"),
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
    sumo = elements["SUMO"]
    headers["start_date"] = to_date(sumo[0])
    headers["finish_date"] = to_finish_date(sumo[1])

    headers["issue_date"] = issue_date
    headers["bill_type_code"] = bill_type_code
    headers["reference"] = reference


def _process_BTL(elements, headers):
    uvlt = elements["UVLT"]
    utva = elements["UTVA"]
    tbtl = elements["TBTL"]

    return {
        "mpan_core": headers["mpan_core"],
        "account": headers["account"],
        "bill_type_code": headers["bill_type_code"],
        "reference": headers["reference"],
        "issue_date": headers["issue_date"],
        "start_date": headers["start_date"],
        "finish_date": headers["finish_date"],
        "kwh": headers["kwh"],
        "net": Decimal("0.00") + to_decimal(uvlt) / Decimal("100"),
        "vat": Decimal("0.00") + to_decimal(utva) / Decimal("100"),
        "gross": Decimal("0.00") + to_decimal(tbtl) / Decimal("100"),
        "breakdown": headers["breakdown"],
        "reads": headers["reads"],
    }


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
        eln_gbp, eln_rate, eln_cons = ELEMENT_MAP[element_code]
    except KeyError:
        raise BadRequest(
            f"Can't find the element code {element_code} in the ELEMENT_MAP."
        )

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
    breakdown = headers["breakdown"]

    supplier_code = elements["CCDE"][2]
    tariff_code = elements["TCOD"][0]
    mod_code = elements["TMOD"][0]
    try:
        eln_gbp, eln_rate, eln_cons = ELEMENT_MAP[supplier_code][tariff_code][mod_code]
    except KeyError:
        raise BadRequest(
            f"Can't find the element key {supplier_code} -> {tariff_code} -> "
            f"{mod_code} in the ELEMENT_MAP."
        )

    cons = elements["CONS"]
    kwh = Decimal("0")
    if len(cons[0]) > 0:
        el_cons = to_decimal(cons) / Decimal("1000")
        kwh = el_cons
        breakdown[eln_cons] += kwh

    bpri = elements["BPRI"]
    if len(bpri[0]) > 0:
        rate = to_decimal(bpri) / Decimal("100000")
        if eln_rate in breakdown:
            breakdown[eln_rate].add(rate)
        else:
            breakdown[eln_rate] = {rate}

    if "CTOT" in elements:
        net = Decimal("0.00") + to_decimal(elements["CTOT"]) / Decimal("100")
    else:
        net = Decimal("0.00")

    breakdown[eln_gbp] += net

    if eln_gbp == "nrg-msp-gbp":
        headers["kwh"] += kwh


def _process_CCD4(elements, headers):
    breakdown = headers["breakdown"]

    element_code = elements["TMOD"][0]
    headers["element_code"] = element_code
    try:
        eln_gbp, eln_rate, eln_cons = ELEMENT_MAP[element_code]
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
        last_line = headers["lines"][-1]
        keep_keys = {"customer_number"}
        keep = {k: headers[k] for k in keep_keys}
        headers.clear()
        headers.update(keep)
        headers["lines"] = [last_line]
        headers["breakdown"] = defaultdict(
            int, {"vat": {}, "raw-lines": headers["lines"]}
        )
        headers["kwh"] = Decimal(0)
        headers["reads"] = []


def _process_MTR(elements, headers):
    headers["lines"] = []


def _process_VAT(elements, headers):
    vat = Decimal("0.00") + to_decimal(elements["UVTT"]) / Decimal("100")
    vat_percentage = to_decimal(elements["VATP"]) / Decimal("1000")
    vat_net = Decimal("0.00") + to_decimal(elements["UVLA"]) / Decimal("100")

    headers["breakdown"]["vat"][vat_percentage] = {"vat": vat, "net": vat_net}


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


class Parser:
    def __init__(self, f):
        self.edi_str = str(f.read(), "utf-8", errors="ignore")
        self.line_number = None

    def make_raw_bills(self):
        bills = []
        headers = {"lines": []}
        for self.line_number, line, seg_name, elements in parse_edi(self.edi_str):
            headers["lines"].append(line)
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
            except BaseException as e:
                raise BadRequest(
                    f"{e} on line {self.line_number} line {line} "
                    f"seg_name {seg_name} elements {elements}"
                ) from e

            if bill is not None:
                bills.append(bill)

        return bills
