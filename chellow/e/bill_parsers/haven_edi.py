from collections import namedtuple
from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest

from chellow.edi_lib import parse_edi, to_date, to_gbp
from chellow.models import Session, Ssc, Supply
from chellow.utils import HH, parse_mpan_core, to_ct, to_utc


READ_TYPE_MAP = {
    "00": "N",
    "01": "Q",
    "02": "E",
    "03": "F",
    "04": "C",
    "05": "M",
    "06": "I",
}

SSC_MAP = {
    "0008": {
        "Other": "00159",
    },
    "0065": {
        "Other": "00010",
    },
    "0036": {
        "Other": "00151",
    },
    "0037": {
        "Other": "00153",
    },
    "0151": {
        "Day": "00043",
        "Night": "00210",
    },
    "0154": {
        "Day": "00039",
        "Night": "00221",
    },
    "0174": {"Day": "01071", "Night": "01072"},
    "0179": {"Day": "01139", "Night": "01140"},
    "0184": {"Day": "01149", "Night": "01150"},
    "0186": {"Day": "01153", "Night": "01154"},
    "0242": {"Day": "00044", "Night": "00208"},
    "0244": {"Day": "00040", "Night": "00206"},
    "0246": {
        "Night": "00160",
        "Other": "00277",
        "Weekday": "00276",
    },
    # 0246
    "22 0002 1401 756": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "0252": {
        "Other": "00212",
    },
    "0265": {
        "Other": "00190",
    },
    "0319": {
        "Other": "00071",
        "Weekday": "00183",
    },
    "0320": {
        "Other": "00072",
        "Weekday": "00184",
    },
    "0322": {
        "Weekday": "01073",
        "Other": "01074",
    },
    "0326": {
        "Night": "00210",
        "Other": "00187",
        "Weekday": "00184",
        "Day": "00184",
    },
    "0393": {
        "Day": "00001",
        "Energy Charges": "00001",
    },
    "0428": {
        "Energy Charges": "00258",
        "Energy Charges 2": "00259",
        "Day": "00259",
    },
}


# None denotes a TPR-based charge

TMOD_MAP = {
    "700285": ("standing", "rate", "days"),
    "422733": ("ccl", "rate", "kwh"),
    "066540": ("ccl", "rate", "kwh"),
    "453043": None,
    "493988": ("reconciliation", None, None),
    "068476": None,
    "265091": None,
    "517180": None,
    "547856": None,
}


BillElement = namedtuple("BillElement", ["gbp", "rate", "cons", "titles", "desc"])


def _process_BCD(elements, headers):
    headers["issue_date"] = to_date(elements["IVDT"][0])
    headers["reference"] = elements["INVN"][0]
    headers["bill_type_code"] = elements["BTCD"][0]

    sumo = elements["SUMO"]
    headers["start_date"] = to_date(sumo[0])
    headers["finish_date"] = to_date(sumo[1]) + relativedelta(days=1) - HH


def _to_date(component):
    return to_utc(to_ct(Datetime.strptime(component, "%y%m%d")))


def _to_decimal(components, divisor=None):
    comp_0 = components[0]
    if comp_0 == "":
        return None

    try:
        result = Decimal(comp_0)
    except InvalidOperation as e:
        raise BadRequest(f"Can't parse '{comp_0}' of {components} as a decimal: {e}")

    if len(components) > 1 and components[-1] == "R":
        result *= Decimal("-1")

    if divisor is not None:
        result /= Decimal(divisor)

    return result


def _process_NOOP(elements, headers):
    pass


def _process_BTL(elements, headers):
    sess = headers["sess"]
    try:
        mpan_core = headers["mpan_core"]
    except KeyError:
        raise BadRequest("The mpan_core can't be found for this bill.")

    start_date = headers["start_date"]
    reads = headers["reads"]
    supply = Supply.get_by_mpan_core(sess, mpan_core)
    era = supply.find_era_at(sess, start_date)
    if era is None:
        era = supply.find_last_era(sess)

    if era is None:
        imp_mpan_core = ""
        ssc = Ssc.get_by_code(sess, "0393")
    else:
        imp_mpan_core = era.imp_mpan_core
        ssc = Ssc.get_by_code(sess, "0393", start_date) if era.ssc is None else era.ssc

    try:
        ssc_lookup = imp_mpan_core
        tpr_map = SSC_MAP[ssc_lookup]
    except KeyError:
        ssc_lookup = ssc.code
        try:
            tpr_map = SSC_MAP[ssc_lookup]
        except KeyError:
            raise BadRequest(f"The SSC {ssc_lookup} isn't in the SSC_MAP.")

    for read in reads:
        desc = read["tpr_code"]
        try:
            read["tpr_code"] = tpr_map[desc]
        except KeyError:
            raise BadRequest(
                f"The description {desc} isn't in the SSC_MAP for the SSC {ssc_lookup}."
            )

    elems = []
    for el in headers["bill_elements"]:
        if el.titles is None:
            try:
                tpr = tpr_map[el.desc]
            except KeyError:
                raise BadRequest(
                    f"The billing element description {el.desc} isn't in the "
                    f"SSC_MAP for the SSC {ssc_lookup}."
                )

            elname, elrate, elcons = f"{tpr}", "rate", "kwh"
        else:
            elname, elrate, elcons = el.titles

        bd = {}
        if elrate is not None and el.rate is not None:
            bd[elrate] = {el.rate}
        if elcons is not None and el.cons is not None:
            bd[elcons] = el.cons

        if el.gbp is not None:
            elems.append(
                {
                    "name": elname,
                    "net": el.gbp,
                    "breakdown": bd,
                    "start_date": headers["start_date"],
                    "finish_date": headers["finish_date"],
                }
            )

    bill = {
        "net": to_gbp(elements["UVLT"]),
        "vat": to_gbp(elements["UTVA"]),
        "gross": to_gbp(elements["TBTL"]),
        "elements": elems,
        "mpan_core": headers["mpan_core"],
        "reads": headers["reads"],
        "start_date": headers["start_date"],
        "finish_date": headers["finish_date"],
        "issue_date": headers["issue_date"],
        "breakdown": headers["breakdown"],
        "reference": headers["reference"],
        "kwh": headers["kwh"],
        "bill_type_code": headers["bill_type_code"],
        "account": headers["account"],
    }

    if len(headers["errors"]) > 0:
        bill["error"] = " ".join(headers["errors"])
    return bill


def _process_CLO(elements, headers):
    cloc = elements["CLOC"]
    headers["account"] = cloc[1]
    # headers['msn'] = cloc[2] if len(cloc) > 2 else ''


def _process_MAN(elements, headers):
    madn = elements["MADN"]
    dno = madn[0]
    unique = madn[1]
    check_digit = madn[2]
    # pc = madn[3]
    # mtc = madn[4]
    # llfc = madn[5]

    headers["mpan_core"] = parse_mpan_core("".join([dno, unique, check_digit]))


def _process_MTR(elements, headers):
    pass


def _process_MHD(elements, headers):
    message_type = elements["TYPE"][0]
    sess = headers["sess"]
    if message_type == "UTLBIL":
        headers.clear()
        headers["kwh"] = Decimal("0")
        headers["reads"] = []
        headers["breakdown"] = {"raw-lines": []}
        headers["bill_elements"] = []
        headers["errors"] = []
        headers["sess"] = sess
    headers["message_type"] = message_type


def _process_CCD4(elements, headers):
    tmod_1 = elements["TMOD"][0]
    try:
        eln_gbp, eln_rate, eln_cons = TMOD_MAP[tmod_1]
    except KeyError:
        raise BadRequest(
            f"Can't find the Tariff Modifer Code 1 {tmod_1} in the TMOD_MAP."
        )

    """
    m = elements['MLOC'][0]
    mpan_core = ' '.join((m[:2], m[2:6], m[6:10], m[10:]))
    """
    breakdown = headers["breakdown"]

    cons = elements["CONS"]
    if eln_cons is not None and len(cons[0]) > 0:
        el_cons = _to_decimal(cons, "1000")
        breakdown[eln_cons] = el_cons

    if eln_rate is not None:
        rate = _to_decimal(elements["BPRI"], "100000")
        try:
            rates = breakdown[eln_rate]
        except KeyError:
            rates = breakdown[eln_rate] = set()

        rates.append(rate)

    """
    start_date = _to_date(elements['CSDT'][0])
    finish_date = _to_date(elements['CEDT'][0]) - HH
    """

    if "CTOT" in elements:
        net = Decimal("0.00") + _to_decimal(elements["CTOT"], "100")
    else:
        net = Decimal("0.00")

    breakdown[eln_gbp] = net


def _process_CCD1(elements, headers):
    pres_read_date = _to_date(elements["PRDT"][0]) + relativedelta(days=1) - HH

    prev_read_date = _to_date(elements["PVDT"][0]) + relativedelta(days=1) - HH

    m = elements["MLOC"][0]
    mpan = " ".join((m[13:15], m[15:18], m[18:], m[:2], m[2:6], m[6:10], m[10:13]))

    prrd = elements["PRRD"]
    try:
        pres_read_type = READ_TYPE_MAP[prrd[1]]
    except KeyError as e:
        raise BadRequest(f"The present register read type isn't recognized {e}")

    try:
        prev_read_type = READ_TYPE_MAP[prrd[3]]
    except KeyError as e:
        raise BadRequest(f"The previous register read type isn't recognized {e}")

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
        if tpr_code == "":
            tpr_code = elements["TCOD"][1]

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
    tmod_1 = elements["TMOD"][0]
    try:
        titles = TMOD_MAP[tmod_1]
    except KeyError:
        raise BadRequest(
            f"Can't find the Tariff Modifier Code 1 {tmod_1} in the TMOD_MAP."
        )

    """
    m = elements['MLOC'][0]
    mpan_core = ' '.join((m[:2], m[2:6], m[6:10], m[10:]))
    """

    if tmod_1 == "700285":  # standing charge
        start_date = _to_date(elements["CSDT"][0])
        finish_date = _to_date(elements["CEDT"][0])
        elcons = Decimal((finish_date - start_date).days + 1)
    else:
        cons = elements["CONS"]
        if len(cons[0]) > 0:
            elcons = _to_decimal(cons, "1000")

    rate = _to_decimal(elements["BPRI"], "100000")

    if "CTOT" in elements:
        gbp = Decimal("0.00") + _to_decimal(elements["CTOT"], "100")
    else:
        gbp = Decimal("0.00")

    headers["bill_elements"].append(
        BillElement(gbp=gbp, titles=titles, rate=rate, cons=elcons, desc=None)
    )


def _process_CCD3(elements, headers):
    tcod = elements["TCOD"]

    tmod_1 = elements["TMOD"][0]
    try:
        titles = TMOD_MAP[tmod_1]
    except KeyError:
        raise BadRequest(
            f"Can't find the Tariff Code Modifier 1 {tmod_1} in the TMOD_MAP."
        )

    if len(tcod) == 2:
        desc = tcod[1]
    else:
        desc = None

    """
    m = elements['MLOC'][0]
    mpan_core = ' '.join((m[:2], m[2:6], m[6:10], m[10:]))
    """
    if tmod_1 == "700285":  # standing charge
        start_date = _to_date(elements["CSDT"][0])
        finish_date = _to_date(elements["CEDT"][0])
        consumption = Decimal((finish_date - start_date).days + 1)
    else:
        cons = elements["CONS"]
        if len(cons[0]) > 0:
            consumption = _to_decimal(cons, "1000")
        else:
            consumption = Decimal("0")

    if titles is None:
        headers["kwh"] += consumption

    rate = _to_decimal(elements["BPRI"], "100000")

    gbp = Decimal("0.00")
    if "CTOT" in elements:
        gbp += _to_decimal(elements["CTOT"], "100")

    headers["bill_elements"].append(
        BillElement(gbp=gbp, rate=rate, cons=consumption, titles=titles, desc=desc)
    )


def _process_VAT(elements, header):
    pass


CODE_FUNCS = {
    "BCD": _process_BCD,
    "BTL": _process_BTL,
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


def _process_segment(headers, line_number, line, seg_name, elements):
    try:
        func = CODE_FUNCS[seg_name]
    except KeyError:
        raise BadRequest(f"Code {seg_name} not recognized.")

    try:
        bill = func(elements, headers)
    except BadRequest as e:
        raise BadRequest(
            f"{e.description} on line {line_number} line {line} "
            f"seg_name {seg_name} elements {elements}"
        )
    except BaseException as e:
        raise BadRequest(
            f"Problem on line {line_number} line {line} "
            f"seg_name {seg_name} elements {elements}"
        ) from e

    if "breakdown" in headers:
        headers["breakdown"]["raw-lines"].append(line)

    return bill


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
                bill = _process_segment(
                    headers, self.line_number, line, seg_name, elements
                )
                if bill is not None:
                    bills.append(bill)

        return bills
