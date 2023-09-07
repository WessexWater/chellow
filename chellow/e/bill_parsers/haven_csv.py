import csv
from collections import namedtuple
from datetime import datetime as Datetime
from decimal import Decimal
from io import StringIO

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest

from chellow.models import Session, Supply
from chellow.utils import HH, parse_mpan_core, to_ct, to_utc


READ_TYPE_MAP = {
    "A": "A",
    "C": "C",
    "D": "D",
    "E": "E",
    "F": "F",
    "X": "H",
    "I": "I",
    "R": "N",
    "O": "O",
    "Q": "Q",
    "S": "S",
    "Z": "Z",
}

SSC_MAP = {
    # 0326
    "20 0000 5855 970": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0000 6048 528": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0002 1909 377": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0002 2254 214": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0002 2326 515": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0002 2371 155": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0002 5282 171": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0002 5476 287": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0002 6228 157": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0002 6440 184": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    "20 0002 6419 768": {"Night": "00187", "Other": "00210", "Weekday": "00184"},
    # 0246
    "22 0001 3834 361": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0001 4442 321": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1401 756": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1427 578": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1442 103": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1502 222": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1528 986": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1540 176": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1589 599": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1823 142": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1829 376": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1839 541": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1878 160": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    "22 0002 1394 727": {
        "Night": "00277",
        "Other": "00160",
        "Weekday": "00276",
    },
    # 0174
    "20 0002 6308 157": {"Day": "01072", "Night": "01071"},
    "20 0002 6467 511": {"Day": "01072", "Night": "01071"},
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
    },
    "0393": {"Day": "00001"},
    "0428": {
        "Energy Charges": "00258",
        "Energy Charges 2": "00259",
    },
}


# None denotes a TPR-based charge

TITLE_MAP = {
    "Standing Charge": ("standing-gbp", "standing-rate", "standing-days"),
    "Climate Change Levy": ("ccl-gbp", "ccl-rate", "ccl-kwh"),
    "CCL": ("ccl-gbp", "ccl-rate", "ccl-kwh"),
    "Night": None,
    "Day": None,
    "Weekday": None,
    "Other": None,
    "Energy Charges": None,
}


BillElement = namedtuple("BillElement", ["gbp", "rate", "cons", "titles", "desc"])


def _to_date(row, index):
    try:
        return to_utc(to_ct(Datetime.strptime(row[index], "%Y%m%d")))
    except ValueError as e:
        raise BadRequest(f"Can't parse the date at index {index}: {e}.")


class Parser:
    def __init__(self, f):
        self.reader = csv.reader(
            StringIO(str(f.read(), "utf-8", errors="ignore")), skipinitialspace=True
        )
        self.line_number = None

    def make_raw_bills(self):
        raw_bills = []
        with Session() as sess:
            headers = {"sess": sess}

            blank_set = set(("",))
            for self.line_number, row in enumerate(self.reader):
                # skip blank lines
                if len(row) == 0 or set(row) == blank_set:
                    continue

                try:
                    bill = _process_line(row[0], row[1:], headers)
                except BadRequest as e:
                    raise BadRequest(
                        f"Can't parse line number {self.line_number}: {row} : "
                        f"{e.description}"
                    )

                if bill is not None:
                    raw_bills.append(bill)
        return raw_bills


def _process_line(code, row, headers):
    if "breakdown" in headers:
        headers["breakdown"]["raw-lines"].append(row)

    if code == "INVOICE":
        _process_INVOICE(row, headers)

    elif code == "MPAN":
        _process_MPAN(row, headers)

    elif code == "VAT":
        return _process_VAT(row, headers)

    elif code == "READING":
        _process_READING(row, headers)

    elif code == "CHARGE":
        _process_CHARGE(row, headers)

    elif code == "SUMMARY":
        _process_SUMMARY(row, headers)

    else:
        raise BadRequest(f"The code {code} is not recognized.")


def _process_INVOICE(row, headers):
    sess = headers["sess"]
    headers.clear()
    headers["kwh"] = Decimal("0")
    headers["reads"] = []
    headers["breakdown"] = {"raw-lines": []}
    headers["bill_elements"] = []
    headers["sess"] = sess

    headers["reference"] = row[0]
    bill_type_raw = row[3]
    headers["bill_type_code"] = "W" if bill_type_raw == "" else bill_type_raw
    headers["issue_date"] = _to_date(row, 14)

    headers["start_date"] = _to_date(row, 17)
    headers["finish_date"] = _to_date(row, 18) + relativedelta(days=1) - HH
    headers["net"] = Decimal("0.00") + Decimal(row[19])
    headers["vat"] = Decimal("0.00") + Decimal(row[20])
    headers["gross"] = Decimal("0.00") + Decimal(row[21])
    headers["account"] = row[26]


def _process_MPAN(row, headers):
    dno = row[3]
    unique = row[4].zfill(10)
    check_digit = row[5]

    headers["mpan_core"] = parse_mpan_core("".join([dno, unique, check_digit]))


def _process_VAT(rows, headers):
    sess = headers["sess"]
    mpan_core = headers["mpan_core"]
    start_date = headers["start_date"]
    reads = headers["reads"]
    supply = Supply.get_by_mpan_core(sess, mpan_core)
    era = supply.find_era_at(sess, start_date)
    bill_elements = []
    if era is None:
        era = supply.find_last_era(sess)
    if era is not None and era.ssc is not None:
        try:
            ssc_lookup = era.imp_mpan_core
            tpr_map = SSC_MAP[ssc_lookup]
        except KeyError:
            ssc_lookup = era.ssc.code
            try:
                tpr_map = SSC_MAP[ssc_lookup]
            except KeyError:
                raise BadRequest("The SSC " + ssc_lookup + " isn't in the SSC_MAP.")

        for read in reads:
            desc = read["tpr_code"]
            try:
                read["tpr_code"] = tpr_map[desc]
            except KeyError:
                raise BadRequest(
                    "The description " + desc + " isn't in the SSC_MAP "
                    "for the SSC " + ssc_lookup + "."
                )

        for el in headers["bill_elements"]:
            if el.titles is None:
                try:
                    tpr = tpr_map[el.desc]
                except KeyError:
                    raise BadRequest(
                        f"The billing element description {el.desc} isn't in "
                        f"the SSC_MAP for the SSC {ssc_lookup}."
                    )

                titles = (tpr + "-gbp", tpr + "-rate", tpr + "-kwh")
            else:
                titles = el.titles

            bill_elements.append(
                BillElement(
                    gbp=el.gbp, titles=titles, rate=el.rate, cons=el.cons, desc=None
                )
            )
    else:
        for read in reads:
            read["tpr_code"] = "00001"

        for el in headers["bill_elements"]:
            if el.titles is None:
                des = el.desc
                titles = (des + "-kwh", des + "-rate", des + "-gbp")
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
            breakdown[eln_cons] = cons

    return {
        "kwh": headers["kwh"],
        "reference": headers["reference"],
        "mpan_core": mpan_core,
        "issue_date": headers["issue_date"],
        "account": headers["account"],
        "start_date": start_date,
        "finish_date": headers["finish_date"],
        "net": headers["net"],
        "vat": headers["vat"],
        "gross": headers["gross"],
        "breakdown": breakdown,
        "reads": reads,
        "bill_type_code": headers["bill_type_code"],
    }


def _process_READING(row, headers):
    coefficient = Decimal(row[2])
    msn = row[4]
    tpr_code_raw = row[6]

    prev_read_date = _to_date(row, 11) + relativedelta(days=1) - HH
    prev_reading_value = Decimal(row[12])
    try:
        prev_read_type = READ_TYPE_MAP[row[13]]
    except KeyError as e:
        raise BadRequest(f"The previous register read type isn't recognized {e}.")

    pres_read_date = _to_date(row, 14) + relativedelta(days=1) - HH
    pres_reading_value = Decimal(row[15])
    try:
        pres_read_type = READ_TYPE_MAP[row[16]]
    except KeyError as e:
        raise BadRequest(f"The present register read type isn't recognized {e}.")

    units_raw = row[18]
    if units_raw == "kW":
        units = "kW"
        tpr_code = None
    elif units_raw == "kVA":
        units = "kVA"
        tpr_code = None
    elif units_raw == "KWH":
        units = "kWh"
        tpr_code = tpr_code_raw
    else:
        raise BadRequest(f"Units {units_raw} not recognized.")

    headers["reads"].append(
        {
            "msn": msn,
            "mpan": "",
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


def _process_CHARGE(row, headers):
    desc = row[6]

    try:
        titles = TITLE_MAP[desc]
    except KeyError:
        raise BadRequest(f"Can't find the description {desc} in the TITLE_MAP.")

    rate = Decimal(row[20])

    if desc == "Standing Charge":
        start_date = _to_date(row, 23)
        finish_date = _to_date(row, 24)
        consumption = Decimal((finish_date - start_date).days + 1)
    else:
        consumption = Decimal(row[22])

    if titles is None:
        headers["kwh"] += consumption

    gbp = Decimal("0.00") + Decimal(row[25])

    if desc == "Energy Charges":
        headers["bill_elements"].append(
            BillElement(
                gbp=(gbp / 2),
                rate=rate,
                cons=(consumption / 2),
                titles=titles,
                desc=desc,
            )
        )
        headers["bill_elements"].append(
            BillElement(
                gbp=(gbp / 2),
                rate=rate,
                cons=(consumption / 2),
                titles=titles,
                desc="Energy Charges 2",
            )
        )
    else:
        headers["bill_elements"].append(
            BillElement(gbp=gbp, rate=rate, cons=consumption, titles=titles, desc=desc)
        )


def _process_SUMMARY(row, headers):
    pass
