from collections import defaultdict
from decimal import Decimal


from werkzeug.exceptions import BadRequest

from chellow.edi_lib import parse_edi, to_date, to_decimal, to_finish_date
from chellow.utils import HH


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
    "030025": ("ccl-gbp", "ccl-rate", "ccl-kwh"),
    "345065": ("summer-weekend-gbp", "summer-weekend-rate", "summer-weekend-kwh"),
    "350293": ("capacity-gbp", "capacity-rate", "capacity-kwh"),
    "425779": ("ro-gbp", "ro-rate", "ro-kwh"),
    "534342": ("reconciliation-gbp", None, None),
    "584867": ("aahedc-gbp", "aahedc-rate", "aahedc-kwh"),
    "989534": ("bsuos-gbp", "bsuos-rate", "bsuos-kwh"),
    "117220": ("capacity-gbp", "capacity-rate", "capacity-kwh"),
    "579387": ("capacity-gbp", "capacity-rate", "capacity-kwh"),
    "558147": ("capacity-gbp", "capacity-rate", "capacity-kwh"),
    "066540": ("ccl-gbp", "ccl-rate", "ccl-kwh"),
    "154164": ("cfd-fit-gbp", "cfd-fit-rate", "cfd-fit-kwh"),
    "281170": ("cfd-fit-gbp", "cfd-fit-rate", "cfd-fit-kwh"),
    "342094": ("cfd-fit-gbp", "cfd-fit-rate", "cfd-fit-kwh"),
    "378809": ("cfd-fit-gbp", "cfd-fit-rate", "cfd-fit-kwh"),
    "574015": ("cfd-fit-gbp", "cfd-fit-rate", "cfd-fit-kwh"),
    "810016": ("cfd-fit-gbp", "cfd-fit-rate", "cfd-fit-kwh"),
    "839829": ("cfd-fit-gbp", "cfd-fit-rate", "cfd-fit-kwh"),
    "068476": ("day-gbp", "day-rate", "day-kwh"),
    "219182": (
        "duos-availability-gbp",
        "duos-availability-rate",
        "duos-availability-kva",
    ),
    "144424": (
        "duos-excess-availability-gbp",
        "duos-excess-availability-rate",
        "duos-excess-availability-kva",
    ),
    "986159": ("duos-fixed-gbp", "duos-fixed-rate", "duos-fixed-days"),
    "838286": ("duos-reactive-gbp", "duos-reactive-rate", "duos-reactive-kvarh"),
    "242643": ("duos-fixed-gbp", "duos-fixed-rate", "duos-fixed-days"),
    "257304": ("duos-amber-gbp", "duos-amber-rate", "duos-amber-kwh"),
    "661440": ("duos-amber-gbp", "duos-amber-rate", "duos-red-kwh"),
    "257305": ("duos-green-gbp", "duos-green-rate", "duos-green-kwh"),
    "257303": ("duos-red-gbp", "duos-red-rate", "duos-red-kwh"),
    "661439": ("duos-red-gbp", "duos-red-rate", "duos-red-kwh"),
    "661441": ("duos-red-gbp", "duos-red-rate", "duos-red-kwh"),
    "563023": ("ebrs-gbp", None, "ebrs-kwh"),
    "309707": ("fit-gbp", "fit-rate", "fit-kwh"),
    "994483": ("reconciliation-gbp", None, None),
    "544936": ("meter-rental-gbp", "meter-rental-rate", "meter-rental-days"),
    "265091": ("night-gbp", "night-rate", "night-kwh"),
    "483457": ("peak-gbp", "peak-rate", "peak-kwh"),
    "975901": ("peak-shoulder-gbp", "peak-shoulder-rate", "peak-shoulder-kwh"),
    "364252": ("ro-gbp", "ro-rate", "ro-kwh"),
    "378246": ("ro-gbp", "ro-rate", "ro-kwh"),
    "632209": ("summer-night-gbp", "summer-night-rate", "summer-night-kwh"),
    "663682": ("summer-weekday-gbp", "summer-weekday-rate", "summer-weekday-kwh"),
    "299992": ("summer-weekend-gbp", "summer-weekend-rate", "summer-weekend-kwh"),
    "447769": ("triad-gbp", "triad-rate", "triad-kw"),
    "647721": ("triad-gbp", "triad-rate", "triad-kw"),
    "276631": ("triad-gbp", "triad-rate", "triad-kw"),
    "220894": ("winter-night-gbp", "winter-night-rate", "winter-night-kwh"),
    "264929": ("winter-weekday-gbp", "winter-weekday-rate", "winter-weekday-kwh"),
    "638187": ("winter-weekend-gbp", "winter-weekend-rate", "winter-weekend-kwh"),
    "700285": ("duo-fixed-gbp", "duos-fixed-rate", "duos-fixed-days"),
}


def _process_BCD(elements, headers):
    issue_date = to_date(elements["IVDT"][0])
    reference = elements["INVN"][0]
    bill_type_code = elements["BTCD"][0]

    headers["issue_date"] = issue_date
    headers["bill_type_code"] = bill_type_code
    headers["reference"] = reference


def _process_CCD1(elements, headers):
    pres_read_date = to_finish_date(elements["PRDT"][0])

    prev_read_date = to_finish_date(elements["PVDT"][0])

    m = elements["MLOC"][0]
    mpan = " ".join((m[13:15], m[15:18], m[18:], m[:2], m[2:6], m[6:10], m[10:13]))

    prrd = elements["PRRD"]
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

    element_code = elements["TCOD"][0]
    try:
        eln_gbp, eln_rate, eln_cons = TCOD_MAP[element_code]
    except KeyError:
        raise BadRequest(f"Can't find the element code {element_code} in the TCOD_MAP.")

    m = elements["MLOC"][0]
    mpan_core = " ".join((m[:2], m[2:6], m[6:10], m[10:]))

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

    headers["mpan_core"] = mpan_core

    try:
        reads = headers["reads"]
        del headers["reads"][:]
    except KeyError:
        reads = []

    return {
        "bill_type_code": headers["bill_type_code"],
        "reference": headers["reference"] + "_" + eln_gbp[:-4],
        "issue_date": headers["issue_date"],
        "mpan_core": mpan_core,
        "account": mpan_core,
        "start_date": start_date,
        "finish_date": finish_date,
        "kwh": kwh if eln_gbp == "ro-gbp" else Decimal("0"),
        "net": net,
        "vat": Decimal("0.00"),
        "gross": net,
        "breakdown": breakdown,
        "reads": reads,
    }


def _process_CCD3(elements, headers):
    breakdown = defaultdict(int)

    element_code = elements["TCOD"][0]
    try:
        eln_gbp, eln_rate, eln_cons = TCOD_MAP[element_code]
    except KeyError:
        raise BadRequest(f"Can't find the element code {element_code} in the TCOD_MAP.")

    m = elements["MLOC"][0]
    mpan_core = " ".join((m[:2], m[2:6], m[6:10], m[10:]))

    cons = elements["CONS"]
    if eln_cons is not None and len(cons[0]) > 0:
        el_cons = to_decimal(cons) / Decimal("1000")
        breakdown[eln_cons] = kwh = el_cons
    else:
        kwh = Decimal("0")

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

    headers["mpan_core"] = mpan_core

    try:
        reads = headers["reads"]
        del headers["reads"][:]
    except KeyError:
        reads = []

    return {
        "bill_type_code": headers["bill_type_code"],
        "issue_date": headers["issue_date"],
        "reference": headers["reference"],
        "mpan_core": mpan_core,
        "account": mpan_core,
        "start_date": start_date,
        "finish_date": finish_date,
        "net": net,
        "kwh": kwh if eln_gbp == "ro-gbp" else Decimal("0"),
        "vat": Decimal("0.00"),
        "gross": net,
        "breakdown": breakdown,
        "reads": reads,
    }


def _process_CCD4(elements, headers):
    breakdown = defaultdict(int)

    element_code = elements["TCOD"][0]
    try:
        eln_gbp, eln_rate, eln_cons = TCOD_MAP[element_code]
    except KeyError:
        raise BadRequest(f"Can't find the element code {element_code} in the TCOD_MAP.")

    m = elements["MLOC"][0]
    mpan_core = " ".join((m[:2], m[2:6], m[6:10], m[10:]))

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

    headers["mpan_core"] = mpan_core

    try:
        reads = headers["reads"]
        del headers["reads"][:]
    except KeyError:
        reads = []

    return {
        "kwh": kwh if eln_gbp == "ro-gbp" else Decimal("0.00"),
        "reference": headers["reference"] + "_" + eln_gbp[:-4],
        "issue_date": headers["issue_date"],
        "mpan_core": mpan_core,
        "account": mpan_core,
        "start_date": start_date,
        "finish_date": finish_date,
        "net": net,
        "vat": Decimal("0.00"),
        "gross": net,
        "breakdown": breakdown,
        "reads": reads,
        "bill_type_code": headers["bill_type_code"],
    }


def _process_MHD(elements, headers):
    message_type = elements["TYPE"][0]
    if message_type == "UTLBIL":
        pass


def _process_MTR(elements, headers):
    headers.clear()


def _process_VAT(elements, headers):
    vat = Decimal("0.00") + to_decimal(elements["UVTT"]) / Decimal("100")

    return {
        "bill_type_code": headers["bill_type_code"],
        "account": headers["mpan_core"],
        "mpan_core": headers["mpan_core"],
        "reference": headers["reference"] + "_vat",
        "issue_date": headers["issue_date"],
        "start_date": headers["bill_start_date"],
        "finish_date": headers["bill_finish_date"],
        "kwh": Decimal("0.00"),
        "net": Decimal("0.00"),
        "vat": vat,
        "gross": vat,
        "breakdown": {},
        "reads": [],
    }


def _process_NOOP(elements, headers):
    pass


CODE_FUNCS = {
    "BCD": _process_BCD,
    "BTL": _process_NOOP,
    "CCD1": _process_CCD1,
    "CCD2": _process_CCD2,
    "CCD3": _process_CCD3,
    "CCD4": _process_CCD4,
    "CDT": _process_NOOP,
    "CLO": _process_NOOP,
    "DNA": _process_NOOP,
    "END": _process_NOOP,
    "FIL": _process_NOOP,
    "MAN": _process_NOOP,
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
