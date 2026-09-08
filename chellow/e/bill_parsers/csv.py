import csv
from decimal import Decimal, InvalidOperation
from io import StringIO

from dateutil.relativedelta import relativedelta

from werkzeug.exceptions import BadRequest

from zish import ZishLocationException

from chellow.utils import (
    HH,
    ct_datetime_parse,
    loads,
    parse_mpan_core,
    to_utc,
    validate_hh_start,
)


def parse_date(row, idx, is_finish=False):
    date_str = row[idx].strip()
    try:
        if len(date_str) == 10:
            dt = to_utc(ct_datetime_parse(date_str, "%Y-%m-%d"))
            if is_finish:
                dt = dt + relativedelta(days=1) - HH
        else:
            dt = to_utc(ct_datetime_parse(date_str, "%Y-%m-%d %H:%M"))
        return validate_hh_start(dt)
    except BaseException as e:
        raise BadRequest(
            f"Can't parse the date at column {idx}. The required spreadsheet format is "
            f"'YYYY-MM-DD HH:MM'. {e}"
        )


def to_decimal(vals, dec_index, dec_name, is_money=False):
    try:
        dec_str = vals[dec_index]
        dec_str = dec_str.replace(",", "")
        dec = Decimal(dec_str)
        if is_money:
            dec += Decimal("0.00")
            dec = round(dec, 2)
        return dec
    except InvalidOperation as e:
        raise BadRequest(
            f"The value '{dec_str}' can't be parsed as a decimal: {e}. It's in "
            f"the '{dec_name}' column at position {dec_index} in {vals}."
        )
    except IndexError:
        raise BadRequest(
            f"The field '{dec_name}' can't be found. It's expected at "
            f"position {dec_index} in the list of fields."
        )
    except ValueError:
        raise BadRequest(
            f"The {dec_name} field '{dec_str}' cannot be parsed as a number. The "
            f"{dec_name} field is the {dec_index} field of {vals}."
        )


def _process_bill(vals):
    reference = vals[0]
    bill_type_code = vals[1]
    account = vals[2]
    mpan_core = parse_mpan_core(vals[3])
    issue_date = parse_date(vals, 4)
    start_date = parse_date(vals, 5)
    finish_date = parse_date(vals, 6, True)

    kwh = to_decimal(vals, 7, "kwh")
    net = to_decimal(vals, 8, "net", is_money=True)
    vat = to_decimal(vals, 9, "vat", is_money=True)
    gross = to_decimal(vals, 10, "gross", is_money=True)
    breakdown_str = vals[11].strip()
    if len(breakdown_str) == 0:
        breakdown = {}
    else:
        try:
            breakdown = loads(breakdown_str)
        except ZishLocationException as e:
            raise BadRequest(str(e))

    return {
        "bill_type_code": bill_type_code,
        "account": account,
        "mpan_core": mpan_core,
        "reference": reference,
        "issue_date": issue_date,
        "start_date": start_date,
        "finish_date": finish_date,
        "kwh": kwh,
        "net": net,
        "vat": vat,
        "gross": gross,
        "breakdown": breakdown,
        "reads": [],
        "elements": [],
    }


def _process_element(vals):
    bill_reference = vals[0]
    name = vals[1]
    start_date = parse_date(vals, 2)
    finish_date = parse_date(vals, 3)
    net = to_decimal(vals, 4, "net", is_money=True)
    breakdown_str = vals[5].strip()
    if len(breakdown_str) == 0:
        breakdown = {}
    else:
        try:
            breakdown = loads(breakdown_str)
        except ZishLocationException as e:
            raise BadRequest(str(e))

    return {
        "bill_reference": bill_reference,
        "name": name,
        "start_date": start_date,
        "finish_date": finish_date,
        "net": net,
        "breakdown": breakdown,
    }


def _process_read(vals):
    tpr_str = vals[5].strip()
    tpr_code = None if len(tpr_str) == 0 else tpr_str.zfill(5)
    return {
        "bill_reference": vals[0],
        "msn": vals[1],
        "mpan": vals[2],
        "coefficient": to_decimal(vals, 3, "coefficient"),
        "units": vals[4],
        "tpr_code": tpr_code,
        "prev_date": parse_date(vals, 6),
        "prev_value": Decimal(vals[7]),
        "prev_type_code": vals[8],
        "pres_date": parse_date(vals, 9),
        "pres_value": Decimal(vals[10]),
        "pres_type_code": vals[11],
    }


class Parser:
    def __init__(self, f):
        self.reader = csv.reader(
            StringIO(str(f.read(), "utf-8-sig", errors="ignore")), skipinitialspace=True
        )
        self.line_number = None

    def make_raw_bills(self):
        bills = {}
        for self.line_number, self.vals in enumerate(self.reader, start=2):
            try:
                # skip blank lines and comment lines
                if (
                    len(self.vals) == 0
                    or set(self.vals) == {""}
                    or self.vals[0].strip().startswith("#")
                ):
                    continue
                action = self.vals[0]
                if action == "bill":
                    bill = _process_bill(self.vals[1:])
                    bills[bill["reference"]] = bill
                elif action == "element":
                    element = _process_element(self.vals[1:])
                    bill = bills[element["bill_reference"]]
                    bill["elements"].append(element)
                elif action == "read":
                    read = _process_read(self.vals[1:])
                    bill = bills[read["bill_reference"]]
                    bill["reads"].append(read)
                else:
                    raise BadRequest(
                        f"The type {action} must be either 'bill', 'element' or 'read'."
                    )

            except BadRequest as e:
                raise BadRequest(
                    f"Problem at line {self.line_number} {self.vals}: {e.description}"
                )
        return bills.values()
