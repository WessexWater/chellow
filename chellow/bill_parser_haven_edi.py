from collections import namedtuple
from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest

from chellow.edi_lib import EdiParser, SEGMENTS
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
    },
}


# None denotes a TPR-based charge

TMOD_MAP = {
    "700285": ("standing-gbp", "standing-rate", "standing-days"),
    "422733": ("ccl-gbp", "ccl-rate", "ccl-kwh"),
    "066540": ("ccl-gbp", "ccl-rate", "ccl-kwh"),
    "453043": None,
    "068476": None,
    "265091": None,
    "517180": None,
    "547856": None,
}


BillElement = namedtuple("BillElement", ["gbp", "rate", "cons", "titles", "desc"])


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


def _find_elements(code, elements):
    segment_name = code + elements[1][0] if code == "CCD" else code
    elem_codes = [m["code"] for m in SEGMENTS[segment_name]["elements"]]
    return dict(zip(elem_codes, elements))


class Parser:
    def __init__(self, f):
        self.parser = EdiParser(StringIO(str(f.read(), "utf-8", errors="ignore")))
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        sess = Session()
        headers = {"sess": sess, "errors": []}
        try:
            for self.line_number, code in enumerate(self.parser):
                elements = _find_elements(code, self.parser.elements)
                line = self.parser.line
                bill = _process_segment(code, elements, line, headers, self.line_number)
                if bill is not None:
                    raw_bills.append(bill)
        finally:
            if sess is not None:
                sess.close()

        return raw_bills


def _process_segment(code, elements, line, headers, line_number):
    try:
        if "breakdown" in headers:
            headers["breakdown"]["raw-lines"].append(line)

        if code == "BCD":
            headers["issue_date"] = _to_date(elements["IVDT"][0])
            headers["reference"] = elements["INVN"][0]
            headers["bill_type_code"] = elements["BTCD"][0]

            sumo = elements["SUMO"]
            headers["start_date"] = _to_date(sumo[0])
            headers["finish_date"] = _to_date(sumo[1]) + relativedelta(days=1) - HH

        elif code == "BTL":
            _process_BTL(elements, headers)

        elif code == "MHD":
            _process_MHD(elements, headers)

        elif code == "CCD":
            _process_CCD(elements, headers)

        elif code == "CLO":
            _process_CLO(elements, headers)

        elif code == "MTR":
            _process_MTR(elements, headers)

        elif code == "MAN":
            _process_MAN(elements, headers)

    except BadRequest as e:
        print("error", e)
        headers["errors"].append(
            f"Can't parse the line number {line_number} {line}: {e.description}"
        )

    if code == "MTR":
        bill = {}

        if "message_type" in headers and headers["message_type"] == "UTLBIL":
            print("doing message type")
            print("headers", headers)
            for k in (
                "kwh",
                "reference",
                "mpan_core",
                "issue_date",
                "account",
                "start_date",
                "finish_date",
                "net",
                "vat",
                "gross",
                "breakdown",
                "bill_type_code",
                "reads",
            ):
                if k in headers:
                    bill[k] = headers[k]
                else:
                    headers["errors"].append(
                        f"The key {k} is missing from the headers at line number "
                        f"{line_number}."
                    )

            if len(headers["errors"]) > 0:
                bill["error"] = " ".join(headers["errors"])
            return bill

        elif len(headers["errors"]) > 0:
            bill["error"] = " ".join(headers["errors"])
            return bill


def _process_BTL(elements, headers):
    headers["net"] = Decimal("0.00") + _to_decimal(elements["UVLT"], "100")
    headers["vat"] = Decimal("0.00") + _to_decimal(elements["UTVA"], "100")
    headers["gross"] = Decimal("0.00") + _to_decimal(elements["TBTL"], "100")


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
    if headers["message_type"] != "UTLBIL":
        return

    sess = headers["sess"]
    try:
        mpan_core = headers["mpan_core"]
    except KeyError:
        raise BadRequest("The mpan_core can't be found for this bill.")

    start_date = headers["start_date"]
    reads = headers["reads"]
    supply = Supply.get_by_mpan_core(sess, mpan_core)
    era = supply.find_era_at(sess, start_date)
    bill_elements = []
    if era is None:
        era = supply.find_last_era(sess)

    if era is None:
        imp_mpan_core = ""
        ssc = Ssc.get_by_code(sess, "0393")
    else:
        imp_mpan_core = era.imp_mpan_core
        ssc = Ssc.get_by_code(sess, "0393") if era.ssc is None else era.ssc

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

    for el in headers["bill_elements"]:
        if el.desc == "Energy Charges":
            # If it's an unmetered supply there is only one charge
            # line in the EDI, no mater how many TPRs there are.
            # Therefore we split the charge evenly between the
            # TPRs.
            mrs = ssc.measurement_requirements
            num_mrs = len(mrs)
            gbp = el.gbp / num_mrs
            cons = el.cons / num_mrs
            for mr in mrs:
                tpr_code = mr.tpr.code
                titles = f"{tpr_code}-gbp", f"{tpr_code}-rate", f"{tpr_code}-kwh"
                bill_elements.append(
                    BillElement(
                        gbp=gbp, rate=el.rate, cons=cons, titles=titles, desc=None
                    )
                )
        else:
            if el.titles is None:
                try:
                    tpr = tpr_map[el.desc]
                except KeyError:
                    raise BadRequest(
                        f"The billing element description {el.desc} isn't in the "
                        f"SSC_MAP for the SSC {ssc_lookup}."
                    )

                titles = f"{tpr}-gbp", f"{tpr}-rate", f"{tpr}-kwh"
            else:
                titles = el.titles

            bill_elements.append(
                BillElement(
                    gbp=el.gbp, titles=titles, rate=el.rate, cons=el.cons, desc=None
                )
            )

    breakdown = headers["breakdown"]
    for bill_el in bill_elements:
        eln_gbp, eln_rate, eln_cons = bill_el.titles

        try:
            breakdown[eln_gbp] += bill_el.gbp
        except KeyError:
            breakdown[eln_gbp] = bill_el.gbp

        rate = bill_el.rate
        if eln_rate is not None and rate is not None:
            try:
                rates = breakdown[eln_rate]
            except KeyError:
                rates = breakdown[eln_rate] = set()

            rates.add(rate)

        cons = bill_el.cons
        if eln_cons is not None and cons is not None:
            try:
                breakdown[eln_cons] += cons
            except KeyError:
                breakdown[eln_cons] = cons


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


def _process_CCD(elements, headers):
    ccde = elements["CCDE"]
    consumption_charge_indicator = ccde[0]

    if consumption_charge_indicator == "1":
        _process_CCD_1(elements, headers)

    elif consumption_charge_indicator == "2":
        _process_CCD_2(elements, headers)

    elif consumption_charge_indicator == "3":
        _process_CCD_3(elements, headers)

    elif consumption_charge_indicator == "4":
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


def _process_CCD_1(elements, headers):
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


def _process_CCD_2(elements, headers):
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


def _process_CCD_3(elements, headers):
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
