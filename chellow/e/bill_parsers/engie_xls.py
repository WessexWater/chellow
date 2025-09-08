import csv
import decimal
from datetime import datetime as Datetime
from decimal import Decimal
from itertools import count

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest

from xlrd import open_workbook, xldate_as_tuple

from chellow.utils import HH, parse_mpan_core, to_ct, to_utc


ELEM_MAP = {
    None: {
        None: None,
        "OOC MOP": {None: "meter-rental"},
    },
    "Charge - Recurring": {None: "duos-fixed"},
    "Meter - Standard": {
        "Energy Bill Relief Scheme": {None: "ebrs"},
        "Energy Bill Relief Scheme Discount": {None: "ebrs"},
        "Energy Bill Discount Scheme": {None: "ebrs"},
    },
    "Meter - UK Electricity - AAHEDC Pass-Thru": {None: "aahedc"},
    "Meter - UK Electricity - BSUoS Pass-Thru": {None: "bsuos"},
    "Meter - UK Electricity - Capacity Market Pass-Thru": {
        None: "capacity",
        "Reverse Capacity Market Estimate": {None: "capacity"},
    },
    "Meter - UK Electricity - CfD FiT Pass-Thru": {None: "cfd-fit"},
    "Meter - UK Electricity - CCL": {
        None: "ccl",
        "CCL": {None: "ccl"},
        "Levy Exempt Energy": {None: "lec"},
    },
    "Meter - UK Electricity - DUoS": {
        None: None,
        "DUoS Unit Rate 3": {
            None: "duos-green",
        },
        "DUoS Unit Charge 3": {
            None: "duos-green",
        },
        "DUoS Unit Charge 2": {
            None: "duos-amber",
        },
        "DUoS Unit Rate 2": {
            None: "duos-amber",
        },
        "DUoS Unit Charge 1": {None: "duos-red"},
        "DUoS Unit Rate 1": {None: "duos-red"},
        "DUoS Standing Charge": {None: "duos-fixed"},
        "DUoS Fixed": {None: "duos-fixed"},
        "DUoS Reactive": {
            None: "duos-reactive",
        },
    },
    "Meter - UK Electricity - FiT Pass-Thru": {
        None: "fit",
    },
    "Pass Thru - UK Electricity Cost Component": {
        None: "meter-rental",
    },
    "Meter - UK Electricity - RO Pass-Thru": {None: "ro"},
    "Meter - UK Electricity - TUoS": {
        None: "triad",
        "TNUoS Fixed": {
            None: "tnuos",
        },
    },
    "Meter - UK Electricity - Standard": {
        None: None,
        "Unit Rate": {
            "Summer Weekday": {
                None: "summer-weekday",
            },
            "Peak": {None: "peak"},
            "Peak Shoulder": {
                None: "peak-shoulder",
            },
            "Summer Night": {
                None: "summer-night",
            },
            "Summer Weekend & Bank Holiday": {
                None: "summer-weekend",
            },
            "Night": {None: "night"},
            "Winter Weekday": {
                None: "winter-weekday",
            },
            "Winter Weekend & Bank Holiday": {
                None: "winter-weekend",
            },
            "Winter Night": {
                None: "winter-night",
            },
            "Day": {None: "day"},
            "Single": {None: "day"},
            "Off Peak / Weekends": {None: "day"},
        },
        "Reverse BSUoS in Unit Rate": {
            None: "bsuos-reverse",
        },
    },
    "Meter - UK Gas - CCL": {None: "ccl"},
}


def _find_name(tree, path):
    if len(path) > 0:
        try:
            return _find_name(tree[path[0]], path[1:])
        except KeyError:
            pass

    return tree[None]


COLUMNS = [
    "Billing Entity",
    "Customer Name",
    "Customer Number",
    "Account Name",
    "Account Number",
    "Billing Address",
    "Bill Number",
    "Bill Date",
    "Due Date",
    "Accepted Date",
    "Bill Period",
    "Agreement Number",
    "Product Bundle",
    "Product Name",
    "Bill Status",
    "Product Item Class",
    "Type",
    "Description",
    "From Date",
    "To Date",
    "Sales Tax Rate",
    "Meter Point",
    "Usage",
    "Usage Unit",
    "Price",
    "Amount",
    "Currency",
    "Indicator",
    "Product Item Name",
    "Rate Name",
]

COLUMN_MAP = dict(zip(COLUMNS, count()))


def get_date(row, name, datemode):
    dt = get_date_naive(row, name, datemode)
    return dt if dt is None else to_utc(to_ct(dt))


def get_date_naive(row, name, datemode):
    val = get_value(row, name)
    if isinstance(val, float):
        return Datetime(*xldate_as_tuple(val, datemode))
    else:
        return None


def get_value(row, name):
    idx = COLUMN_MAP[name]
    try:
        val = row[idx].value
    except IndexError:
        raise BadRequest(
            f"For the name '{name}', the index is {idx} which is beyond the end of "
            f"the row. "
        )
    if isinstance(val, str):
        return val.strip()
    else:
        return val


def get_dec(row, name):
    try:
        return Decimal(str(get_value(row, name)))
    except decimal.InvalidOperation:
        return None


def _get_vat_values(bd, percentage):
    if "vat" in bd:
        vat_breakdown = bd["vat"]
    else:
        vat_breakdown = bd["vat"] = {}

    try:
        vat_values = vat_breakdown[percentage]
    except KeyError:
        vat_values = vat_breakdown[percentage] = {
            "vat": Decimal("0.00"),
            "net": Decimal("0.00"),
        }
    return vat_values


def _parse_row(bills, row, row_index, datemode, title_row):
    val = get_value(row, "Meter Point")
    try:
        mpan_core = parse_mpan_core(str(int(val)))
    except ValueError as e:
        raise BadRequest(
            f"Can't parse the MPAN core in column 'Meter Point' with value '{val}' : "
            f"{e}"
        )

    try:
        mc = bills[mpan_core]
    except KeyError:
        mc = bills[mpan_core] = {}

    bill_period = get_value(row, "Bill Period")
    if "-" in bill_period:
        period_start_naive, period_finish_naive = [
            Datetime.strptime(v, "%Y-%m-%d") for v in bill_period.split(" - ")
        ]
        period_start = to_utc(to_ct(period_start_naive))
        period_finish = to_utc(to_ct(period_finish_naive + relativedelta(days=1) - HH))
    else:
        period_start, period_finish = None, None

    issue_date = get_date(row, "Bill Date", datemode)

    try:
        bill = mc[bill_period]
    except KeyError:
        bill = mc[bill_period] = {
            "bill_type_code": "N",
            "kwh": Decimal(0),
            "vat": Decimal("0.00"),
            "net": Decimal("0.00"),
            "reads": [],
            "breakdown": {"raw_lines": [str(title_row)]},
            "account": mpan_core,
            "issue_date": issue_date,
            "start_date": period_start,
            "finish_date": period_finish,
            "mpan_core": mpan_core,
            "elements": [],
        }

    from_date = get_date(row, "From Date", datemode)
    if from_date is None:
        if period_start is None:
            raise BadRequest("Can't find a bill start date.")
        else:
            from_date = period_start

    to_date_naive = get_date_naive(row, "To Date", datemode)
    if to_date_naive is None:
        if period_finish is None:
            raise BadRequest("Can't find a bill finish date.")
        else:
            to_date = period_finish

    else:
        to_date = to_utc(to_ct(to_date_naive + relativedelta(days=1) - HH))

    bill_number = get_value(row, "Bill Number")
    bd = bill["breakdown"]

    usage = get_dec(row, "Usage")
    usage_units = get_value(row, "Usage Unit")
    price = get_dec(row, "Price")
    amount = get_dec(row, "Amount")
    product_item_name = get_value(row, "Product Item Name")
    rate_name = get_value(row, "Rate Name")
    if product_item_name == "Renewables Obligation (RO)" and usage is not None:
        bill["kwh"] += round(usage, 2)
    description = get_value(row, "Description")
    product_class = get_value(row, "Product Item Class")

    if description in ("Standard VAT@20%", "Reduced VAT@5%"):
        vat_gbp = round(amount, 2)
        bill["vat"] += vat_gbp
        if description.endswith("20%"):
            vat_percentage = Decimal("20")
        else:
            vat_percentage = Decimal("5")
        bd["vat_percentage"] = vat_percentage

        if "vat-rate" in bd:
            vat_rate = bd["vat-rate"]
        else:
            vat_rate = bd["vat-rate"] = set()

        vat_rate.add(vat_percentage / Decimal("100"))

        vat_values = _get_vat_values(bd, vat_percentage)
        vat_values["vat"] += vat_gbp
    else:
        net = round(amount, 2)
        bill["net"] += net

        sales_tax_rate = get_value(row, "Sales Tax Rate")
        if sales_tax_rate == "Commercial UK Energy VAT":
            vat_values = _get_vat_values(bd, 20)
            vat_values["net"] += net

        path = [product_class, description, rate_name]
        elname = _find_name(ELEM_MAP, path)
        ebd = {}
        duos_avail_prefix = "DUoS Availability ("
        duos_excess_avail_prefix = "DUoS Excess Availability ("

        for prefix, name in (
            ("DUoS Availability Adjustment ", "duos-availability"),
            ("DUoS Availability", "duos-availability"),
            ("DUoS Excess Availability", "duos-excess-availability"),
            ("BSUoS Black Start ", "black-start"),
            ("BSUoS Reconciliation - ", "bsuos"),
            ("FiT Rec - ", "fit"),
            ("FiT Reconciliation ", "fit"),
            ("CfD FiT Rec - ", "cfd-fit"),
            ("CfD FiT Reconciliation", "cfd-fit"),
            ("Flex", "reconciliation"),
            ("Legacy TNUoS Reversal ", "triad"),
            ("Hand Held Read -", "meter-rental"),
            ("RO Mutualisation ", "ro"),
            ("OOC MOP - ", "meter-rental"),
            ("KVa Adjustment ", "duos-availability"),
        ):
            if description.startswith(prefix):
                elname = name
                if description.startswith(duos_excess_avail_prefix):
                    ebd["kva"] = int(description[len(duos_excess_avail_prefix) : -5])
                elif description.startswith(duos_avail_prefix):
                    ebd["kva"] = int(description[len(duos_avail_prefix) : -5])
                break

        if elname is None:
            raise BadRequest(
                f"For the path {path} the parser can't work out the element."
            )

        if usage is not None:
            if isinstance(usage_units, str) and usage_units != "":
                units = usage_units.lower()
            else:
                units = "kwh"
            ebd[units] = usage
        if price is not None:
            ebd["rate"] = price
        bill["elements"].append(
            {
                "start_date": from_date,
                "finish_date": to_date,
                "name": elname,
                "net": net,
                "breakdown": ebd,
            }
        )

    reference = str(bill_number) + "_" + str(row_index + 1)

    bill["reference"] = reference
    bill["gross"] = bill["net"] + bill["vat"]


def _make_raw_bills(sheet, datemode):
    bills = {}
    title_row = sheet.row(0)
    for row_index in range(1, sheet.nrows):
        row = sheet.row(row_index)
        if len(row) > 21:
            val = row[21].value
            if val not in (None, ""):
                try:
                    _parse_row(bills, row, row_index, datemode, title_row)
                except BadRequest as e:
                    raise BadRequest(f"On row {row_index + 1}: {e.description}")

    return [b for mc in bills.values() for b in mc.values()]


class Parser:
    def __init__(self, f):
        self.book = open_workbook(file_contents=f.read())
        self.sheet = self.book.sheet_by_index(0)

        self.last_line = None
        lines = (self._set_last_line(i, l) for i, l in enumerate(f))
        self.reader = csv.reader(lines, skipinitialspace=True)
        self._line_number = None
        self._title_line = None

    @property
    def line_number(self):
        return None if self._line_number is None else self._line_number + 1

    def _set_last_line(self, i, line):
        self._line_numer = i
        self.last_line = line
        if i == 0:
            self._title_line = line
        return line

    def make_raw_bills(self):
        return _make_raw_bills(self.sheet, self.book.datemode)
