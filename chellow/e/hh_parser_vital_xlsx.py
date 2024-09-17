from datetime import datetime as Datetime

from decimal import Decimal, InvalidOperation
from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.utils import HH, ct_datetime, hh_before, hh_range, to_utc


def create_parser(input_stream, mpan_map, messages):
    return HhParserVital(input_stream, mpan_map, messages)


def get_cell(sheet, col, row):
    try:
        coordinates = f"{col}{row}"
        return sheet[coordinates]
    except IndexError:
        raise BadRequest(f"Can't find the cell {coordinates} on sheet {sheet}.")


def get_date(sheet, col, row):
    cell = get_cell(sheet, col, row)
    val = cell.value
    if not isinstance(val, Datetime):
        raise BadRequest(
            f"Problem reading {val} (of type {type(val)}) as a timestamp at "
            f"{cell.coordinate}."
        )
    return val


def get_str(sheet, col, row):
    return get_cell(sheet, col, row).value.strip()


def get_dec(sheet, col, row):
    return get_dec_from_cell(get_cell(sheet, col, row))


def get_dec_from_cell(cell):
    try:
        return Decimal(str(cell.value))
    except InvalidOperation as e:
        raise BadRequest(f"Problem parsing the number at {cell.coordinate}. {e}")


def get_int(sheet, col, row):
    return int(get_cell(sheet, col, row).value)


def find_hhs(sheet, imp_mpan, exp_mpan):
    row = pres_readings = pres_ts = None
    caches = {}
    try:
        for row in range(2, len(sheet["A"]) + 1):
            imp_read_cell = get_cell(sheet, "H", row)
            imp_read_val = imp_read_cell.value
            if imp_read_val is None or imp_read_val == "":
                break

            exp_read_cell = get_cell(sheet, "I", row)
            exp_read_val = exp_read_cell.value
            if exp_read_val is None or exp_read_val == "":
                break

            # '16/09/2024 14:45:00
            ts_str = get_str(sheet, "A", row)
            ts_naive = Datetime.strptime(ts_str, "%d/%m/%Y %H:%M:%S")
            ts_ct = ct_datetime(
                ts_naive.year,
                ts_naive.month,
                ts_naive.day,
                ts_naive.hour,
                ts_naive.minute,
            )

            imp_read = get_dec_from_cell(imp_read_cell)
            exp_read = get_dec_from_cell(exp_read_cell)
            ts = to_utc(ts_ct)

            if ts_naive.minute in (0, 30) and hh_before(ts, pres_ts):
                if pres_readings is not None:
                    pres_imp_read, pres_exp_read = pres_readings
                    hhs = hh_range(caches, ts, pres_ts - HH)
                    num_hhs = len(hhs)
                    val_imp = (pres_imp_read - imp_read) / num_hhs
                    val_exp = (pres_exp_read - exp_read) / num_hhs
                    for hh in hhs:

                        yield {
                            "mpan_core": imp_mpan,
                            "channel_type": "ACTIVE",
                            "start_date": hh,
                            "value": val_imp,
                            "status": "A",
                        }
                        yield {
                            "mpan_core": exp_mpan,
                            "channel_type": "ACTIVE",
                            "start_date": hh,
                            "value": val_exp,
                            "status": "A",
                        }

                pres_readings = imp_read, exp_read
                pres_ts = ts

    except BadRequest as e:
        e.description = (f"Problem at row: {row}: {e.description}",)
        raise e


class HhParserVital:
    def __init__(self, input_stream, mpan_map, messages):
        book = load_workbook(input_stream, data_only=True)
        sheet = book.worksheets[0]
        imp_name = get_str(sheet, "H", 1).strip()
        imp_mpan = mpan_map[imp_name]
        exp_name = get_str(sheet, "I", 1).strip()
        exp_mpan = mpan_map[exp_name]
        self.data = iter(find_hhs(sheet, imp_mpan, exp_mpan))

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.data)

    def close(self):
        pass
