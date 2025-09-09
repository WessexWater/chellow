from decimal import Decimal


from werkzeug.exceptions import BadRequest

from chellow.edi_lib import (
    parse_edi,
    to_date,
    to_decimal,
    to_finish_date,
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


TCOD_MAP = {
    "140114": ("reconciliation", None, None),
    "255204": ("meter-rental", "rate", "days"),
    "345065": ("op-weekend", "rate", "kwh"),
    "350293": ("capacity", "rate", "kwh"),
    "425779": ("ro", "rate", "kwh"),
    "534342": ("reconciliation", None, None),
    "583174": ("meter-rental", "rate", "days"),
    "584867": ("aahedc", "rate", "kwh"),
    "946827": ("meter-rental", "rate", "days"),
    "989534": ("bsuos", "rate", "kwh"),
    "117220": ("capacity", "rate", "kwh"),
    "579387": ("capacity", "rate", "kwh"),
    "558147": ("capacity", "rate", "kwh"),
    "030025": ("ccl", "rate", "kwh"),
    "066540": ("ccl", "rate", "kwh"),
    "154164": ("cfd-fit", "rate", "kwh"),
    "281170": ("cfd-fit", "rate", "fit-kwh"),
    "342094": ("cfd-fit", "rate", "kwh"),
    "378809": ("cfd-fit", "rate", "kwh"),
    "574015": ("cfd-fit", "rate", "kwh"),
    "810016": ("cfd-fit", "rate", "kwh"),
    "839829": ("cfd-fit", "rate", "kwh"),
    "649282": ("cfd-fit", "rate", "kwh"),
    "068476": ("day", "rate", "kwh"),
    "133186": ("nrg", "rate", "kwh"),
    "400434": ("day", "rate", "kwh"),
    "219182": ("duos-availability", "rate", "kva"),
    "144424": ("duos-excess-availability", "rate", "kva"),
    "301541": ("duos-fixed", None, None),
    "099335": ("duos-fixed", None, None),
    "873562": ("duos-fixed", None, None),
    "986159": ("duos-fixed", "rate", "days"),
    "838286": ("duos-reactive", "rate", "kvarh"),
    "242643": ("duos-fixed", "rate", "days"),
    "257304": ("duos-amber", "rate", "kwh"),
    "661440": ("duos-amber", "rate", "kwh"),
    "257305": ("duos-green", "rate", "kwh"),
    "661441": ("duos-green", "rate", "kwh"),
    "257303": ("duos-red", "rate", "kwh"),
    "661439": ("duos-red", "rate", "kwh"),
    "504364": ("ebrs", None, "kwh"),
    "563023": ("ebrs", None, "kwh"),
    "823408": ("ebrs", None, "kwh"),
    "871593": ("ebrs", "rate", "kwh"),
    "873894": ("ebrs", "rate", "kwh"),
    "309707": ("fit", "rate", "kwh"),
    "310129": ("meter-rental", None, None),
    "452415": ("meter-rental", None, None),
    "371265": ("meter-rental", None, None),
    "544936": ("meter-rental", "rate", "days"),
    "265091": ("night", "rate", "kwh"),
    "483457": ("peak", "rate", "kwh"),
    "975901": ("peak-shoulder", "rate", "kwh"),
    "994483": ("reconciliation", None, None),
    "637176": ("reconciliation", None, None),
    "913821": ("reconciliation", None, None),
    "307660": ("ro", "rate", "kwh"),
    "364252": ("ro", "rate", "kwh"),
    "378246": ("ro", "rate", "kwh"),
    "708848": ("ro", None, None),
    "632209": ("summer-night", "rate", "kwh"),
    "663682": ("summer-weekday", "rate", "kwh"),
    "299992": ("summer-weekend", "rate", "kwh"),
    "211000": ("tnuos", "rate", "days"),
    "790618": ("tnuos", None, None),
    "447769": ("triad", "rate", "kw"),
    "647721": ("triad", "rate", "kw"),
    "276631": ("triad", "rate", "kw"),
    "220894": ("winter-night", "rate", "kwh"),
    "264929": ("winter-weekday", "rate", "kwh"),
    "638187": ("winter-weekend", "rate", "kwh"),
    "700285": ("standing", "rate", "days"),
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

    headers["issue_date"] = issue_date
    headers["start_date"] = to_date(sumo[0])
    headers["finish_date"] = to_date(sumo[1]) - HH
    headers["bill_type_code"] = bill_type_code
    headers["reference"] = reference
    headers["elements"] = []
    headers["reads"] = []
    headers["breakdown"] = {}
    headers["kwh"] = Decimal("0")


def _process_BTL(elements, headers):
    uvlt = elements["UVLT"]
    utva = elements["UTVA"]
    tbtl = elements["TBTL"]

    return {
        "bill_type_code": headers["bill_type_code"],
        "reference": headers["reference"],
        "issue_date": headers["issue_date"],
        "mpan_core": headers["mpan_core"],
        "account": headers["account"],
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
    breakdown = {}

    element_code = elements["TCOD"][0]
    try:
        eln_name, eln_rate, eln_cons = TCOD_MAP[element_code]
    except KeyError:
        raise BadRequest(f"Can't find the element code {element_code} in the TCOD_MAP.")

    cons = elements["CONS"]
    if eln_cons is not None and len(cons[0]) > 0:
        el_cons = to_decimal(cons) / Decimal("1000")
        if eln_name == "duos-availability":
            breakdown[eln_cons] = {el_cons}
        else:
            breakdown[eln_cons] = el_cons
            if eln_name == "ro":
                headers["kwh"] += el_cons

    if eln_rate is not None:
        rate = to_decimal(elements["BPRI"]) / Decimal("100000")
        breakdown[eln_rate] = {rate}

    net = Decimal("0.00")
    if "CTOT" in elements:
        net += to_decimal(elements["CTOT"]) / Decimal("100")

    headers["elements"].append(
        {
            "name": eln_name,
            "start_date": to_date(elements["CSDT"][0]),
            "finish_date": to_date(elements["CEDT"][0]) - HH,
            "net": net,
            "breakdown": breakdown,
        }
    )


def _process_CCD3(elements, headers):
    breakdown = {}

    element_code = elements["TCOD"][0]
    try:
        eln_name, eln_rate, eln_cons = TCOD_MAP[element_code]
    except KeyError:
        raise BadRequest(f"Can't find the element code {element_code} in the TCOD_MAP.")

    cons = elements["CONS"]
    if eln_cons is not None and len(cons[0]) > 0:
        el_cons = to_decimal(cons) / Decimal("1000")
        breakdown[eln_cons] = el_cons
        if eln_name == "ro":
            headers["kwh"] += el_cons

    if eln_rate is not None:
        rate = to_decimal(elements["BPRI"]) / Decimal("100000")
        breakdown[eln_rate] = {rate}

    net = Decimal("0.00")
    if "CTOT" in elements:
        net += to_decimal(elements["CTOT"]) / Decimal("100")

    headers["elements"].append(
        {
            "name": eln_name,
            "start_date": to_date(elements["CSDT"][0]),
            "finish_date": to_date(elements["CEDT"][0]) - HH,
            "net": net,
            "breakdown": breakdown,
        }
    )


def _process_CCD4(elements, headers):
    breakdown = {}

    element_code = elements["TCOD"][0]

    try:
        eln_name, eln_rate, eln_cons = TCOD_MAP[element_code]
    except KeyError:
        raise BadRequest(f"Can't find the element code {element_code} in the TCOD_MAP.")

    cons = elements["CONS"]
    if eln_cons is not None and len(cons[0]) > 0:
        el_cons = to_decimal(cons, "1000")
        breakdown[eln_cons] = el_cons
        if eln_name == "ro":
            headers["kwh"] += el_cons

    if eln_rate is not None:
        rate = to_decimal(elements["BPRI"], "100000")
        breakdown[eln_rate] = [rate]

    net = Decimal("0.00")
    if "CTOT" in elements:
        net += to_decimal(elements["CTOT"], "100")

    headers["elements"].append(
        {
            "name": eln_name,
            "start_date": to_date(elements["CSDT"][0]),
            "finish_date": to_date(elements["CEDT"][0]) - HH,
            "net": net,
            "breakdown": breakdown,
        }
    )


def _process_CDT(elements, headers):
    customer_id = elements["CIDN"][0]
    headers["customer_number"] = customer_id


def _process_CLO(elements, headers):
    cloc = elements["CLOC"]
    headers["account"] = cloc[2]


def _process_END(elements, headers):
    pass


def _process_MAN(elements, headers):
    madn = elements["MADN"]
    headers["mpan_core"] = parse_mpan_core("".join(madn[:3]))


def _process_MHD(elements, headers):
    message_type = elements["TYPE"][0]
    if message_type == "UTLBIL":
        keep_keys = {"customer_number"}
        keep = {k: headers[k] for k in keep_keys}
        headers.clear()
        headers.update(keep)


def _process_MTR(elements, headers):
    pass


def _process_VAT(elements, headers):
    vat = Decimal("0.00") + to_decimal(elements["UVTT"]) / Decimal("100")
    vat_percentage = to_decimal(elements["VATP"]) / Decimal("1000")
    vat_net = Decimal("0.00") + to_decimal(elements["UVLA"]) / Decimal("100")

    breakdown = headers["breakdown"]

    try:
        vat_bd = breakdown["vat"]
    except KeyError:
        vat_bd = breakdown["vat"] = {}

    vat_bd[vat_percentage] = {"vat": vat, "net": vat_net}


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
        headers = {}
        bill = None
        lines = []
        for self.line_number, line, seg_name, elements in parse_edi(self.edi_str):
            if seg_name == "MHD":
                lines = []
            lines.append(line)

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
                bill["breakdown"]["raw-lines"] = lines
                bills.append(bill)
            if seg_name == "MTR":
                lines = []

        return bills
