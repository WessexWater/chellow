from collections import defaultdict
from decimal import Decimal

from dateutil.relativedelta import relativedelta

from chellow.edi_lib import parse_edi, to_date, to_decimal
from chellow.utils import HH


READ_TYPE_MAP = {"00": "A", "01": "E"}

TCOD_MAP = {
    "Unidentified Gas": {"PPK": "ug"},
    "Commodity": {"PPK": "commodity"},
    "Transportation": {"PPD": "transportation_fixed", "PPK": "transportation_variable"},
    "Gas Flexi": {"PPK": "commodity"},
    "Flex - Gas Flexi (New)": {"PPK": "commodity"},
    "Meter Reading": {"PPD": "meter_read"},
    "Meter Reading Credit Oct 19": {"FIX": "meter_read"},
    "Meter Rental": {"PPD": "metering"},
    "CCL": {"PPK": "ccl"},
    "Consumption Based Administration": {"PPK": "admin_variable"},
    "Swing": {"PPK": "swing"},
}

UNIT_MAP = {"M3": "M3", "HH": "HCUF"}


class Parser:
    def __init__(self, file_bytes):
        self.edi_str = str(file_bytes, "utf-8", errors="ignore")
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        message_type = breakdown = raw_lines = None
        for self.line_number, line, code, elements in parse_edi(self.edi_str):
            if code == "ADJ":
                adjf = elements["ADJF"]
                if adjf[0] == "CV":
                    cv = Decimal(adjf[1]) / Decimal(100000)

            if code == "BCD":
                ivdt = elements["IVDT"]
                issue_date = to_date(ivdt[0])

                invn = elements["INVN"]
                reference = invn[0]

                btcd = elements["BTCD"]
                bill_type_code = btcd[0]

                sumo = elements["SUMO"]
                start_date = to_date(sumo[0])
                finish_date = to_date(sumo[1]) + relativedelta(days=1) - HH

            elif code == "MHD":
                typ = elements["TYPE"]
                message_type = typ[0]
                if message_type == "UTLBIL":
                    issue_date = None
                    start_date = None
                    finish_date = None
                    reference = None
                    net = Decimal("0.00")
                    vat = Decimal("0.00")
                    gross = Decimal("0.00")
                    kwh = Decimal(0)
                    reads = []
                    bill_type_code = None
                    mprn = None
                    raw_lines = []
                    breakdown = defaultdict(int, {"units_consumed": Decimal(0)})
                    cv = None
            elif code == "CCD":
                ccde = elements["CCDE"]
                consumption_charge_indicator = ccde[0]

                if consumption_charge_indicator == "1":

                    mtnr = elements["MTNR"]
                    msn = mtnr[0]

                    mloc = elements["MLOC"]

                    # Bug in EDI where MPRN missing in second CCD 1
                    if mprn is None:
                        mprn = mloc[0]

                    prdt = elements["PRDT"]
                    pvdt = elements["PVDT"]

                    pres_read_date = to_date(prdt[0])
                    prev_read_date = to_date(pvdt[0])

                    prrd = elements["PRRD"]
                    pres_read_value = Decimal(prrd[0])
                    pres_read_type = READ_TYPE_MAP[prrd[1]]
                    prev_read_value = Decimal(prrd[2])
                    prev_read_type = READ_TYPE_MAP[prrd[3]]

                    conb = elements["CONB"]
                    unit = UNIT_MAP[conb[1]]
                    breakdown["units_consumed"] += to_decimal(conb) / Decimal("1000")

                    adjf = elements["ADJF"]
                    correction_factor = Decimal(adjf[1]) / Decimal(100000)

                    nuct = elements["NUCT"]

                    kwh += to_decimal(nuct) / Decimal("1000")

                    reads.append(
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

                elif consumption_charge_indicator == "2":
                    ccde_supplier_code = ccde[2]
                    tcod = elements["TCOD"]

                    tpref = TCOD_MAP[tcod[1]][ccde_supplier_code]

                    mtnr = elements["MTNR"]
                    mloc = elements["MLOC"]
                    prdt = elements["PRDT"]
                    pvdt = elements["PVDT"]
                    prrd = elements["PRRD"]
                    conb = elements["CONB"]
                    adjf = elements["ADJF"]

                    bpri = elements["BPRI"]
                    rate_key = tpref + "_rate"
                    if rate_key not in breakdown:
                        breakdown[rate_key] = set()
                    rate = Decimal(bpri[0]) / Decimal("10000000")
                    breakdown[rate_key].add(rate)

                    nuct = elements["NUCT"]

                    try:
                        ctot = elements["CTOT"]
                        breakdown[tpref + "_gbp"] += to_decimal(ctot) / Decimal("100")

                        if ccde_supplier_code == "PPK":
                            key = tpref + "_kwh"
                        elif ccde_supplier_code == "PPD":
                            key = tpref + "_days"

                        breakdown[key] += to_decimal(nuct) / Decimal("1000")
                    except KeyError:
                        pass

                elif consumption_charge_indicator == "3":
                    ccde_supplier_code = ccde[2]
                    tcod = elements["TCOD"]

                    tpref = TCOD_MAP[tcod[1]][ccde_supplier_code]

                    mtnr = elements["MTNR"]
                    mloc = elements["MLOC"]
                    prdt = elements["PRDT"]
                    pvdt = elements["PVDT"]
                    prrd = elements["PRRD"]
                    conb = elements["CONB"]
                    adjf = elements["ADJF"]
                    bpri = elements["BPRI"]
                    rate_key = tpref + "_rate"
                    if rate_key not in breakdown:
                        breakdown[rate_key] = set()
                    rate = Decimal(bpri[0]) / Decimal("10000000")
                    breakdown[rate_key].add(rate)

                    nuct = elements["NUCT"]

                    try:
                        ctot = elements["CTOT"]
                        breakdown[tpref + "_gbp"] += to_decimal(ctot) / Decimal("100")

                        if ccde_supplier_code == "PPK":
                            key = tpref + "_kwh"
                        elif ccde_supplier_code == "PPD":
                            key = tpref + "_days"

                        breakdown[key] += to_decimal(nuct) / Decimal("1000")
                    except KeyError:
                        pass

                elif consumption_charge_indicator == "4":
                    ccde_supplier_code = ccde[2]
                    tcod = elements["TCOD"]

                    tpref = TCOD_MAP[tcod[1]][ccde_supplier_code]

                    mtnr = elements["MTNR"]
                    mloc = elements["MLOC"]
                    prdt = elements["PRDT"]
                    pvdt = elements["PVDT"]
                    prrd = elements["PRRD"]
                    conb = elements["CONB"]
                    adjf = elements["ADJF"]
                    bpri = elements["BPRI"]
                    rate_key = tpref + "_rate"
                    if rate_key not in breakdown:
                        breakdown[rate_key] = set()
                    rate = Decimal(bpri[0]) / Decimal("10000000")
                    breakdown[rate_key].add(rate)

                    nuct = elements["NUCT"]

                    try:
                        ctot = elements["CTOT"]
                        breakdown[tpref + "_gbp"] += to_decimal(ctot) / Decimal("100")

                        if ccde_supplier_code == "PPK":
                            key = tpref + "_kwh"
                        elif ccde_supplier_code == "PPD":
                            key = tpref + "_days"

                        breakdown[key] += to_decimal(nuct) / Decimal("1000")
                    except KeyError:
                        pass

            elif code == "MTR":
                if message_type == "UTLBIL":
                    for k, v in tuple(breakdown.items()):
                        if isinstance(v, set):
                            breakdown[k] = sorted(v)

                    for read in reads:
                        read["calorific_value"] = cv

                    raw_bills.append(
                        {
                            "raw_lines": "\n".join(raw_lines),
                            "mprn": mprn,
                            "reference": reference,
                            "account": mprn,
                            "reads": reads,
                            "kwh": kwh,
                            "breakdown": breakdown,
                            "net_gbp": net,
                            "vat_gbp": vat,
                            "gross_gbp": gross,
                            "bill_type_code": bill_type_code,
                            "start_date": start_date,
                            "finish_date": finish_date,
                            "issue_date": issue_date,
                        }
                    )

            elif code == "VAT":
                vatp = elements["VATP"]
                if "vat_rate" not in breakdown:
                    breakdown["vat_rate"] = set()
                breakdown["vat_rate"].add(to_decimal(vatp) / Decimal(100000))

                uvla = elements["UVLA"]
                net += to_decimal(uvla) / Decimal("100")
                uvtt = elements["UVTT"]
                vat += to_decimal(uvtt) / Decimal("100")
                ucsi = elements["UCSI"]
                gross += to_decimal(ucsi) / Decimal("100")

            if raw_lines is not None:
                raw_lines.append(line)

        return raw_bills
