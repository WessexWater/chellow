from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from openpyxl import load_workbook

from werkzeug.exceptions import BadRequest

from chellow.utils import parse_mpan_core, to_ct, to_utc, validate_hh_start

# "Time stamp","Value","Events","Comment","User"
# "18/10/2024 09:30:00","88.0","","",""
# "18/10/2024 09:00:00","89.1","","",""


def create_parser(reader, mpan_map, messages):
    return HhParserSchneiderXlsx(reader, mpan_map, messages)


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


def parse_line(sheet, row):
    timestamp_cell = get_cell(sheet, "A", row)
    timestamp_str = timestamp_cell.value
    # 2024-10-02 00:00:00 +1H, DST
    ts_str = timestamp_str.split(",")[0]
    ts_naive = Datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
    is_dst = ts_str[21] == 1
    if is_dst:
        start_date = to_utc(to_ct(ts_naive))
    else:
        start_date = to_utc(ts_naive)
    start_date = validate_hh_start(start_date)

    reading = get_dec(sheet, "B", row)
    return start_date, reading


class HhParserSchneiderXlsx:
    def __init__(self, input_stream, mpan_map, messages):
        book = load_workbook(input_stream, data_only=True)
        self.sheet = book.worksheets[0]
        imp_name = get_str(self.sheet, "B", 1).strip()
        self.mpan_core = parse_mpan_core(mpan_map[imp_name])
        self.row_iter = iter(range(3, len(self.sheet["A"]) + 1))
        _, self.pres_reading = parse_line(self.sheet, 2)

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.line_number = next(self.row_iter)
            start_date, reading = parse_line(self.sheet, self.line_number)
            datum = {
                "mpan_core": self.mpan_core,
                "channel_type": "ACTIVE",
                "start_date": start_date,
                "value": self.pres_reading - reading,
                "status": "A",
            }
            self.pres_reading = reading
            return datum
        except BadRequest as e:
            e.description = (
                f"Problem at line number: {self.line_number}: {e.description}"
            )
            raise e

    def close(self):
        self.shredder.close()
