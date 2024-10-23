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


def find_hhs(sheet, set_line_number, mpan_core):
    pres_reading = None
    for row in range(2, len(sheet["A"]) + 1):
        set_line_number(row)
        try:
            timestamp_cell = get_cell(sheet, "A", row)
            timestamp_str = timestamp_cell.value
            if timestamp_str is None:
                continue

            # 2024-10-02 00:00:00 +1H, DST
            ts_str = timestamp_str.split(",")[0]
            ts_naive = Datetime.strptime(ts_str[:19], "%Y-%m-%d %H:%M:%S")
            # Sometimes has seconds
            ts_naive = Datetime(
                ts_naive.year,
                ts_naive.month,
                ts_naive.day,
                ts_naive.hour,
                ts_naive.minute,
            )
            is_dst = ts_str[21] == 1
            if is_dst:
                start_date = to_utc(to_ct(ts_naive))
            else:
                start_date = to_utc(ts_naive)
            start_date = validate_hh_start(start_date)

            reading = get_dec(sheet, "B", row)

            if pres_reading is not None:
                value = pres_reading - reading
                if value >= 0:
                    yield {
                        "mpan_core": mpan_core,
                        "channel_type": "ACTIVE",
                        "start_date": start_date,
                        "value": value,
                        "status": "A",
                    }
            pres_reading = reading
        except BadRequest as e:
            e.description = f"Problem at line number: {row}: {e.description}"
            raise e


class HhParserSchneiderXlsx:
    def __init__(self, input_stream, mpan_map, messages):
        book = load_workbook(input_stream, data_only=True)
        self.sheet = book.worksheets[0]
        imp_name = get_str(self.sheet, "B", 1).strip()
        self.mpan_core = parse_mpan_core(mpan_map[imp_name])
        self.line_number = 0

    def _set_line_number(self, line_number):
        self.line_number = line_number

    def __iter__(self):
        return find_hhs(self.sheet, self._set_line_number, self.mpan_core)

    def close(self):
        self.shredder.close()
