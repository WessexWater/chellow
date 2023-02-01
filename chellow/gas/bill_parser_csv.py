import csv
from decimal import Decimal, InvalidOperation
from io import StringIO
from itertools import count

from werkzeug.exceptions import BadRequest

from zish import ZishLocationException, loads

from chellow.utils import parse_hh_start


def get_str(row, idx, name, lineno):
    return row[idx].strip()


def get_datetime(row, idx, name, lineno):
    val = get_str(row, idx, name, lineno)
    try:
        return parse_hh_start(val)
    except BadRequest as e:
        raise BadRequest(
            "Problem parsing the timestamp '"
            + val
            + "' at line number "
            + str(lineno)
            + " for the field '"
            + name
            + "' in column "
            + str(idx + 1)
            + ": "
            + e.description
        )


def get_decimal(row, idx, name, lineno):
    val = get_str(row, idx, name, lineno)
    try:
        return Decimal(val)
    except InvalidOperation as e:
        raise BadRequest(
            "Problem parsing the decimal '"
            + val
            + "' at line number "
            + str(lineno)
            + " for the field '"
            + name
            + "' at "
            + str(idx + 1)
            + ": "
            + str(e)
        )


class Parser:
    def __init__(self, file_bytes):
        self.csv_reader = csv.reader(
            StringIO(file_bytes.decode("utf8", errors="ignore")), skipinitialspace=True
        )
        self.titles = ",".join(next(self.csv_reader))
        self._line_number = None

    @property
    def line_number(self):
        return None if self._line_number is None else self._line_number + 2

    def _set_last_line(self, line):
        self.last_line = line
        return line

    def make_raw_bills(self):
        raw_bills = []
        for self._line_number, row in enumerate(self.csv_reader):
            bill_reference = row[0]
            if bill_reference == "" or bill_reference.startswith("#"):
                continue

            mprn = row[1]
            bill_type = row[2]
            account = row[3]
            issue_date = get_datetime(row, 4, "Issue Date", self.line_number)
            start_date = get_datetime(row, 5, "Start Date", self.line_number)
            finish_date = get_datetime(row, 6, "Finish Date", self.line_number)
            kwh = get_decimal(row, 7, "kWh", self.line_number)
            net = get_decimal(row, 8, "Net GBP", self.line_number)
            vat = get_decimal(row, 9, "VAT GBP", self.line_number)
            gross = get_decimal(row, 10, "Gross GBP", self.line_number)
            try:
                breakdown = loads(row[11])
            except ZishLocationException as e:
                raise BadRequest(
                    "Problem parsing the breakdown field at line number "
                    + str(self.line_number)
                    + ": "
                    + str(e)
                )

            reads = []

            for i in count(12, 10):
                if i > len(row) - 1 or len("".join(row[i:]).strip()) == 0:
                    break

                msn = get_str(row, i, "Meter Serial Number", self.line_number)
                unit = get_str(row, i + 1, "Unit", self.line_number).upper()
                correction_factor = get_decimal(
                    row, i + 2, "Correction Factor", self.line_number
                )

                calorific_value = get_str(
                    row, i + 3, "Calorific Value", self.line_number
                )
                if len(calorific_value) > 0:
                    calorific_value = get_decimal(
                        row, i + 3, "Calorific Value", self.line_number
                    )
                else:
                    calorific_value = None

                prev_date = get_datetime(row, i + 4, "Previous Date", self.line_number)
                prev_value = get_decimal(row, i + 5, "Previous Value", self.line_number)
                prev_type = get_str(row, i + 6, "Previous Type", self.line_number)
                pres_date = get_datetime(row, i + 7, "Previous Date", self.line_number)
                pres_value = get_decimal(row, i + 8, "Present Value", self.line_number)
                pres_type = get_str(row, i + 9, "Present Type", self.line_number)
                reads.append(
                    {
                        "msn": msn,
                        "unit": unit,
                        "correction_factor": correction_factor,
                        "calorific_value": calorific_value,
                        "prev_date": prev_date,
                        "prev_value": prev_value,
                        "prev_type_code": prev_type,
                        "pres_date": pres_date,
                        "pres_value": pres_value,
                        "pres_type_code": pres_type,
                    }
                )

            raw_bills.append(
                {
                    "mprn": mprn,
                    "reference": bill_reference,
                    "account": account,
                    "reads": reads,
                    "kwh": kwh,
                    "breakdown": breakdown,
                    "net_gbp": net,
                    "vat_gbp": vat,
                    "gross_gbp": gross,
                    "raw_lines": self.titles + "\n" + ",".join(row),
                    "bill_type_code": bill_type,
                    "start_date": start_date,
                    "finish_date": finish_date,
                    "issue_date": issue_date,
                }
            )
        return raw_bills
