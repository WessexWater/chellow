from collections import defaultdict
from decimal import Decimal

from werkzeug.exceptions import BadRequest

from chellow.edi_lib import (
    parse_edi,
    to_ct_date,
    to_date,
    to_decimal,
    to_finish_date,
    to_gbp,
)
from chellow.models import Era, Session
from chellow.utils import HH, ct_datetime, parse_mpan_core, to_utc


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

tmod_map = {
    "0001": "00001",
    "3U93": "00001",
    "URQ1": "00001",
    "Z012": "00001",
    "246N": "00160",
    "0210": "00210",
    "W246": "00276",
    "0043": "00043",
    "DAQ2": "01071",
    "NIQ2": "01072",
    "NQ22": "00210",
    "DQ22": "00043",
    "D7P2": "00043",
    "N7P2": "00210",
    "MDC1": "kW",
    "URC1": "00001",
    "0206": "00206",
    "0040": "00040",
    "1140": "01140",
    "1139": "01139",
    "A154": "01154",
    "A153": "01153",
    "0039": "00039",
    "0221": "00221",
    "210E": "00210",
    "1150": "01150",
    "1149": "01149",
    "0153": "00153",
    "WQ42": "00184",
    "NQ42": "00210",
    "EQ42": "00187",
    "WDQ3": "01073",
    "EWQ3": "01074",
    "WDQ4": "01075",
    "EWQ4": "01076",
    "NIQ4": "01077",
    "EQ32": "00072",
    "NQ32": "00184",
    "0276": "00276",
    "0277": "00277",
    "0160": "00160",
    "1152": "01152",
    "1151": "01151",
    "1142": "01142",
    "1141": "01141",
    "0249": "00249",
    "0252": "00252",
    "0240": "00240",
    "0244": "00244",
    "0092": "00092",
    "210A": "00210",
    "MAC2": "kW",
    "DAC2": "00040",
    "NAC2": "00206",
    "NDC2": "00040",
    "NNC2": "00206",
    "MNC2": "kW",
    "148A": "00148",
    "221B": "00221",
    "080A": "00080",
    "P1M3": "00248",
    "P2M3": "00251",
    "W1M3": "00239",
    "W2M3": "00073",
    "OTM3": "00093",
    "NIM3": "00208",
    "MDM3": "kW",
    "URQD": "00001",
    "OPE3": "01088",
    "OEC2": "00190",
    "184A": "00184",
    "210J": "00210",
    "187A": "00187",
    "0183": "00183",
    "0071": "00071",
    "DAE7": "00043",
    "NIE7": "00210",
    "OPAC": "00010",
    "MDM1": "kW",
    "D179": "01139",
    "N179": "01140",
    "O212": "00212",
    "0151": "00151",
    "SG1U": "00001",
    "0184": "00184",
    "0072": "00072",
    "DM22": "00039",
    "NM22": "00221",
    "MM22": "kW",
    "0044": "00044",
    "0208": "00208",
    "URM1": "00001",
    "1043": "01043",
    "1042": "01042",
    "U393": "00001",
    "D244": "00040",
    "N244": "00206",
    "24D4": "00040",
    "24N4": "00206",
    "OFX2": "00001",
    "D151": "00043",
    "N151": "00210",
    "N184": "01150",
    "D184": "01149",
    "OPF2": "00257",
    "N154": "00221",
    "O2EC": "00190",
    "OFC2": "00159",
    "CMACUF": "kW",
    "251A": "00251",
    "208D": "00208",
    "073A": "00073",
    "093A": "00093",
    "248A": "00248",
    "239A": "00239",
    "EA1E": "kVA",
    "MDM2": "kVA",
}

WRONG_TPRS = {
    "20 0000 5855 970",
    "20 0000 6048 528",
    "20 0002 1909 377",
    "20 0002 2254 214",
    "20 0002 2326 515",
    "20 0002 2371 155",
    "20 0002 5282 171",
    "20 0002 5476 287",
    "20 0002 6228 157",
    "20 0002 6308 157",
    "20 0002 6419 768",
    "20 0002 6440 184",
    "20 0002 6467 511",
    "22 0001 3834 361",
    "22 0001 4442 321",
    "22 0002 1394 727",
    "22 0002 1401 756",
    "22 0002 1427 578",
    "22 0002 1442 103",
    "22 0002 1502 222",
    "22 0002 1528 986",
    "22 0002 1540 176",
    "22 0002 1589 599",
    "22 0002 1823 142",
    "22 0002 1829 376",
    "22 0002 1839 541",
    "22 0002 1878 160",
}


def _process_BCD(elements, headers):
    ivdt = elements["IVDT"]
    headers["issue_date"] = to_date(ivdt[0])

    invn = elements["INVN"]
    reference = invn[0]
    headers["reference"] = reference
    headers["account"] = "SA" + reference[:9]

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


def _process_BTL(elements, headers):
    uvlt = elements["UVLT"]
    utva = elements["UTVA"]
    tbtl = elements["TBTL"]

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

    if headers["is_ebatch"]:
        for r in headers["reads"]:
            if r["pres_type_code"] == "C":
                r["pres_type_code"] = "E"

    return {
        "bill_type_code": headers["bill_type_code"],
        "account": headers["account"],
        "mpan_core": headers["mpan_core"],
        "reference": headers["reference"],
        "issue_date": headers["issue_date"],
        "start_date": headers["start_date"],
        "finish_date": headers["finish_date"],
        "kwh": headers["kwh"],
        "net": to_gbp(uvlt),
        "vat": to_gbp(utva),
        "gross": to_gbp(tbtl),
        "breakdown": headers["breakdown"],
        "reads": headers["reads"],
        "elements": headers["elements"],
    }


def _process_MHD(elements, headers):
    message_type = elements["TYPE"][0]
    sess = headers["sess"]
    if message_type == "UTLBIL":
        headers.clear()
        headers["kwh"] = Decimal("0")
        headers["reads"] = []
        headers["breakdown"] = defaultdict(int, {"raw-lines": []})
        headers["elements"] = []
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
    cona = elements["CONA"]

    coefficient = Decimal(adjf[1]) / Decimal(100000)
    pres_reading_value = Decimal(prrd[0])
    prev_reading_value = Decimal(prrd[2])
    msn = mtnr[0]
    tpr_native = tmod[0]
    if tpr_native not in tmod_map:
        raise BadRequest(
            f"The TPR code {tpr_native} can't be found in the TPR list "
            f"for mpan {mpan}."
        )
    tpr_code = tmod_map[tpr_native]
    if tpr_code == "kW":
        units = "kW"
        tpr_code = None
    elif tpr_code == "kVA":
        units = "kVA"
        tpr_code = None
    else:
        units = "kWh"
        headers["kwh"] += to_decimal(cona) / Decimal("1000")

    if mpan_core in WRONG_TPRS and pres_read_date == to_utc(
        ct_datetime(2020, 4, 1, 23, 30)
    ):
        pres_read_date = to_utc(ct_datetime(2020, 4, 1, 22, 30))
        headers["reads"].append(
            {
                "msn": "Separator Read",
                "mpan": mpan,
                "coefficient": coefficient,
                "units": units,
                "tpr_code": tpr_code,
                "prev_date": to_utc(ct_datetime(2020, 4, 1, 23)),
                "prev_value": 0,
                "prev_type_code": "N",
                "pres_date": to_utc(ct_datetime(2020, 4, 1, 23)),
                "pres_value": 0,
                "pres_type_code": "N",
            }
        )

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
    nuct = elements["NUCT"]
    csdt = elements["CSDT"]
    cedt = elements["CEDT"]
    ctot = elements["CTOT"]
    cppu = elements["CPPU"]

    coefficient = Decimal(adjf[1]) / Decimal(100000)
    pres_reading_value = Decimal(prrd[0])
    prev_reading_value = Decimal(prrd[2])
    msn = mtnr[0]
    tpr_code = tmod[0]
    if tpr_code not in tmod_map:
        raise BadRequest(
            f"The TPR code {tpr_code} can't be found in the TPR list "
            f"for mpan {mpan}."
        )
    tpr = tmod_map[tpr_code]
    if tpr == "kW":
        units = "kW"
        tpr = None
        el_name = "md"
    elif tpr == "kVA":
        units = "kVA"
        tpr = None
        el_name = "md"
    else:
        units = "kWh"
        headers["kwh"] += to_decimal(cona) / Decimal("1000")
        el_name = tpr

    headers["elements"].append(
        {
            "name": el_name,
            "breakdown": {
                cona[1].lower(): to_decimal(nuct) / Decimal("1000"),
                "rate": {to_decimal(cppu) / Decimal("100000")},
            },
            "start_date": to_date(csdt[0]),
            "finish_date": to_finish_date(cedt[0]),
            "net": to_gbp(ctot),
        }
    )

    if mpan_core in WRONG_TPRS and pres_read_date == to_utc(
        ct_datetime(2020, 4, 1, 23, 30)
    ):
        pres_read_date = to_utc(ct_datetime(2020, 4, 1, 22, 30))
        headers["reads"].append(
            {
                "msn": "Separator Read",
                "mpan": mpan,
                "coefficient": coefficient,
                "units": units,
                "tpr_code": tpr,
                "prev_date": to_utc(ct_datetime(2020, 4, 1, 23)),
                "prev_value": 0,
                "prev_type_code": "N",
                "pres_date": to_utc(ct_datetime(2020, 4, 1, 23)),
                "pres_value": 0,
                "pres_type_code": "N",
            }
        )

    headers["reads"].append(
        {
            "msn": msn,
            "mpan": mpan,
            "coefficient": coefficient,
            "units": units,
            "tpr_code": tpr,
            "prev_date": prev_read_date,
            "prev_value": prev_reading_value,
            "prev_type_code": prev_read_type,
            "pres_date": pres_read_date,
            "pres_value": pres_reading_value,
            "pres_type_code": pres_read_type,
        }
    )


def _process_CCD3(elements, headers):
    tmod = elements["TMOD"]
    tmod0 = tmod[0]
    if tmod0 == "CCL":
        el_name = "ccl"
    elif tmod0 in ("CQFITC", "CMFITC", "FITARR"):
        el_name = "fit"
    else:
        tpr_code = tmod0
        if tpr_code not in tmod_map:
            raise BadRequest(
                f"The TPR code {tpr_code} can't be found in the TPR "
                f"list for mpan {headers['mpan']}."
            )
        el_name = tmod_map[tpr_code]

    nuct = elements["NUCT"]
    cppu = elements["CPPU"]
    ctot = elements["CTOT"]
    csdt = elements["CSDT"]
    start_date = to_date(csdt[0])
    cedt = elements["CEDT"]
    finish_date = to_finish_date(cedt[0])
    headers["elements"].append(
        {
            "name": el_name,
            "net": to_gbp(ctot),
            "start_date": start_date,
            "finish_date": finish_date,
            "breakdown": {
                "kwh": to_decimal(nuct) / Decimal("1000"),
                "rate": {to_decimal(cppu) / Decimal("100000")},
            },
        }
    )


def _process_CCD4(elements, headers):
    ndrp = elements["NDRP"]
    ctot = elements["CTOT"]
    csdt = elements["CSDT"]
    cedt = elements["CEDT"]

    if len(ctot[0]) > 0:
        breakdown = {}
        el = {
            "name": "standing",
            "net": to_gbp(ctot),
            "start_date": to_date(csdt[0]),
            "finish_date": to_finish_date(cedt[0]),
            "breakdown": breakdown,
        }
        if len(ndrp[0]) > 0:
            breakdown["days"] = to_decimal(ndrp)
        headers["elements"].append(el)


def _process_MTR(elements, headers):
    pass


def _process_MAN(elements, headers):
    madn = elements["MADN"]
    headers["mpan_core"] = parse_mpan_core("".join((madn[0], madn[1], madn[2])))


def _process_VAT(elements, headers):
    uvla = elements["UVLA"]
    to_decimal(uvla) / Decimal("100")
    uvtt = elements["UVTT"]
    to_decimal(uvtt) / Decimal("100")
    ucsi = elements["UCSI"]
    to_decimal(ucsi) / Decimal("100")


def _process_NOOP(elements, headers):
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
    "CLO": _process_NOOP,
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
