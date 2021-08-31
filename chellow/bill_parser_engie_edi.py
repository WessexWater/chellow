from collections import defaultdict
from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation
from io import StringIO

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest

from chellow.edi_lib import EdiParser, SEGMENTS
from chellow.utils import HH, to_ct, to_utc


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


def _to_date(component):
    return to_utc(to_ct(Datetime.strptime(component, "%y%m%d")))


def _to_decimal(components, divisor=None):
    comp_0 = components[0]

    try:
        result = Decimal(comp_0)
    except InvalidOperation as e:
        raise BadRequest(
            "Can't parse '"
            + str(comp_0)
            + "' of "
            + str(components)
            + " as a decimal:"
            + str(e)
        )

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
        headers = {}
        for self.line_number, code in enumerate(self.parser):
            elements = _find_elements(code, self.parser.elements)
            line = self.parser.line
            try:
                bill = _process_segment(code, elements, line, headers)
            except BadRequest as e:
                raise BadRequest("Can't parse the line: " + line + " :" + e.description)
            if bill is not None:
                raw_bills.append(bill)
        return raw_bills


def _process_segment(code, elements, line, headers):
    if code == "BCD":
        issue_date = _to_date(elements["IVDT"][0])
        reference = elements["INVN"][0]
        bill_type_code = elements["BTCD"][0]

        sumo = elements["SUMO"]
        start_date = _to_date(sumo[0])
        finish_date = _to_date(sumo[1]) + relativedelta(days=1) - HH

        headers["issue_date"] = issue_date
        headers["bill_type_code"] = bill_type_code
        headers["reference"] = reference

    elif code == "MHD":
        message_type = elements["TYPE"][0]
        if message_type == "UTLBIL":
            pass

    elif code == "CCD":
        consumption_charge_indicator = elements["CCDE"][0]

        if consumption_charge_indicator == "1":
            pres_read_date = _to_date(elements["PRDT"][0]) + relativedelta(days=1) - HH

            prev_read_date = _to_date(elements["PVDT"][0]) + relativedelta(days=1) - HH

            m = elements["MLOC"][0]
            mpan = " ".join(
                (m[13:15], m[15:18], m[18:], m[:2], m[2:6], m[6:10], m[10:13])
            )

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
                kwh = _to_decimal(elements["CONS"], "1000")

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

        elif consumption_charge_indicator == "2":
            breakdown = defaultdict(int, {"raw-lines": line})

            element_code = elements["TCOD"][0]
            try:
                eln_gbp, eln_rate, eln_cons = TCOD_MAP[element_code]
            except KeyError:
                raise BadRequest(
                    "Can't find the element code " + element_code + " in the TCOD_MAP."
                )

            m = elements["MLOC"][0]
            mpan_core = " ".join((m[:2], m[2:6], m[6:10], m[10:]))

            cons = elements["CONS"]
            kwh = Decimal("0")
            if eln_cons is not None and len(cons[0]) > 0:
                el_cons = _to_decimal(cons, "1000")
                breakdown[eln_cons] = kwh = el_cons

            if eln_rate is not None:
                rate = _to_decimal(elements["BPRI"], "100000")
                breakdown[eln_rate] = [rate]

            start_date = _to_date(elements["CSDT"][0])
            headers["bill_start_date"] = start_date

            finish_date = _to_date(elements["CEDT"][0]) - HH
            headers["bill_finish_date"] = finish_date

            if "CTOT" in elements:
                net = Decimal("0.00") + _to_decimal(elements["CTOT"], "100")
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

        elif consumption_charge_indicator == "3":
            breakdown = defaultdict(int, {"raw-lines": line})

            element_code = elements["TCOD"][0]
            try:
                eln_gbp, eln_rate, eln_cons = TCOD_MAP[element_code]
            except KeyError:
                raise BadRequest(
                    "Can't find the element code " + element_code + " in the TCOD_MAP."
                )

            m = elements["MLOC"][0]
            mpan_core = " ".join((m[:2], m[2:6], m[6:10], m[10:]))

            cons = elements["CONS"]
            if eln_cons is not None and len(cons[0]) > 0:
                el_cons = _to_decimal(cons, "1000")
                breakdown[eln_cons] = kwh = el_cons
            else:
                kwh = Decimal("0")

            if eln_rate is not None:
                rate = _to_decimal(elements["BPRI"], "100000")
                breakdown[eln_rate] = [rate]

            start_date = _to_date(elements["CSDT"][0])
            headers["bill_start_date"] = start_date

            finish_date = _to_date(elements["CEDT"][0]) - HH
            headers["bill_finish_date"] = finish_date

            if "CTOT" in elements:
                net = Decimal("0.00") + _to_decimal(elements["CTOT"], "100")
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

        elif consumption_charge_indicator == "4":
            breakdown = defaultdict(int, {"raw-lines": line})

            element_code = elements["TCOD"][0]
            try:
                eln_gbp, eln_rate, eln_cons = TCOD_MAP[element_code]
            except KeyError:
                raise BadRequest(
                    "Can't find the element code " + element_code + " in the TCOD_MAP."
                )

            m = elements["MLOC"][0]
            mpan_core = " ".join((m[:2], m[2:6], m[6:10], m[10:]))

            cons = elements["CONS"]
            if eln_cons is not None and len(cons[0]) > 0:
                el_cons = _to_decimal(cons, "1000")
                breakdown[eln_cons] = kwh = el_cons

            if eln_rate is not None:
                rate = _to_decimal(elements["BPRI"], "100000")
                breakdown[eln_rate] = [rate]

            start_date = _to_date(elements["CSDT"][0])
            headers["bill_start_date"] = start_date

            finish_date = _to_date(elements["CEDT"][0]) - HH
            headers["bill_finish_date"] = finish_date

            if "CTOT" in elements:
                net = Decimal("0.00") + _to_decimal(elements["CTOT"], "100")
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

    elif code == "MTR":
        headers.clear()

    elif code == "MAN":
        pass

    elif code == "VAT":
        vat = Decimal("0.00") + _to_decimal(elements["UVTT"], "100")

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


def _get_element(elements, index, line):
    try:
        return elements[index]
    except IndexError:
        raise BadRequest(
            "The index "
            + str(index)
            + " is past the end of the elements "
            + str(elements)
            + " and line "
            + line
            + "."
        )
