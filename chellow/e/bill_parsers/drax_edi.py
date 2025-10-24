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
            "139039": ("aahedc", "rate", "kwh"),
        },
    },
    "ADH": {
        "ADHOC": {
            "020330": ("eii", None, None),
            "064305": ("fit", None, None),
            "590346": ("cfd-operational", None, None),
            "493988": ("reconciliation", None, None),
            "637050": ("meter-rental", "rate", "days"),
        },
    },
    "BUS": {
        "BSUOS": {
            "269100": ("bsuos", "rate", "kwh"),
        },
    },
    "CCL": {
        "CCL": {
            "422733": ("ccl", "rate", "kwh"),
        },
    },
    "CFD": {
        "CFD001": {
            "273237": ("cfd-operational", "rate", "kwh"),
            "954379": ("cfd-interim", "rate", "kwh"),
            "538249": ("cm-settlement-levy", "rate", "kwh"),
            "568307": ("capacity", "rate", "kwh"),
        },
    },
    "DCA": {
        "DCDA": {
            "095469": ("meter-rental", "rate", "days"),
        },
    },
    "DUS": {
        "DUS001": {
            "794486": ("duos-availability", "rate", "kva"),
            "644819": ("duos-fixed", "rate", "days"),
            "797790": ("duos-reactive", "rate", "kvarh"),
            "806318": ("duos-green", "rate", "kwh"),
            "716514": ("duos-amber", "rate", "kwh"),
            "769979": ("duos-red", "rate", "kwh"),
            "709522": ("duos-excess-availability", "rate", "kva"),
            "209269": ("tnuos", "rate", "days"),
        },
        "DUS002": {
            "185913": ("duos-yellow", "rate", "kwh"),
            "517270": ("duos-black", "rate", "kwh"),
            "797790": ("duos-reactive", "rate", "kvarh"),
            "806318": ("duos-green", "rate", "kwh"),
            "716514": ("duos-amber", "rate", "kwh"),
            "709522": ("duos-excess-availability", "rate", "kva"),
            "769979": ("duos-red", "rate", "kwh"),
            "644819": ("duos-fixed", "rate", "days"),
            "794486": ("duos-availability", "rate", "kva"),
            "209269": ("tnuos", "rate", "days"),
            "065950": ("eii", "rate", "kwh"),
        },
        "DUSDIS": {
            "122568": ("nrg-gsp-losses", "rate", "kwh"),
        },
        "DUSTRN": {
            "122568": ("nrg-nbp-losses", "rate", "kwh"),
        },
    },
    "ELX": {
        "ELEXON": {
            "489920": ("elexon", "rate", "kwh"),
        },
    },
    "FIT": {
        "FIT_LV": {
            "704107": ("fit", "rate", "kwh"),
        },
    },
    "NRG": {
        "HH0002": {
            "033667": ("management", "rate", "kwh"),
            "091890": ("shape", "rate", "kwh"),
            "122568": ("nrg-msp", "rate", "kwh"),
        },
        "R10001": {
            "700285": ("standing", "rate", "days"),
        },
    },
    "REN": {
        "REN001": {
            "229128": ("ro", "rate", "kwh"),
        },
        "REN002": {
            "019090": ("rego", "rate", "kwh"),
        },
    },
    "TUS": {
        "TNUOS": {
            "012069": ("triad", "rate", "kw"),
        },
    },
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
    headers["elements"] = []


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
        "elements": headers["elements"],
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
    elem_bd = {}

    supplier_code = elements["CCDE"][2]
    tariff_code = elements["TCOD"][0]
    mod_code = elements["TMOD"][0]
    try:
        eln_name, eln_rate, eln_cons = ELEMENT_MAP[supplier_code][tariff_code][mod_code]
    except KeyError:
        raise BadRequest(
            f"Can't find the element key {supplier_code} -> {tariff_code} -> "
            f"{mod_code} in the ELEMENT_MAP."
        )

    cons = elements["CONS"]
    if len(cons[0]) > 0:
        el_cons = to_decimal(cons) / Decimal("1000")
        elem_bd[eln_cons] = el_cons
        if eln_name == "nrg-msp":
            headers["kwh"] += el_cons

    bpri = elements["BPRI"]
    if len(bpri[0]) > 0:
        rate = to_decimal(bpri) / Decimal("100000")
        elem_bd[eln_rate] = {rate}

    net = Decimal("0.00")
    if "CTOT" in elements:
        net += to_decimal(elements["CTOT"]) / Decimal("100")

    csdt = elements["CSDT"]
    start_date = to_date(csdt[0])
    cedt = elements["CEDT"]
    finish_date = to_finish_date(cedt[0])

    headers["elements"].append(
        {
            "name": eln_name,
            "start_date": start_date,
            "finish_date": finish_date,
            "net": net,
            "breakdown": elem_bd,
        }
    )


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
    breakdown = headers["breakdown"]
    vat = Decimal("0.00") + to_decimal(elements["UVTT"]) / Decimal("100")
    vat_percentage = to_decimal(elements["VATP"]) / Decimal("1000")

    if "vat_rate" in breakdown:
        vat_rate = breakdown["vat-rate"]
    else:
        vat_rate = breakdown["vat-rate"] = set()
    vat_rate.add(vat_percentage / Decimal("100"))
    vat_net = Decimal("0.00") + to_decimal(elements["UVLA"]) / Decimal("100")

    breakdown["vat"][vat_percentage] = {"vat": vat, "net": vat_net}


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
