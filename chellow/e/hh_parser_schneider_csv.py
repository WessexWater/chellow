import csv
import itertools
from codecs import iterdecode
from datetime import datetime as Datetime
from decimal import Decimal, InvalidOperation

from werkzeug.exceptions import BadRequest

from chellow.utils import parse_mpan_core, to_utc, validate_hh_start

# "Time stamp","Value","Events","Comment","User"
# "18/10/2024 09:30:00","88.0","","",""
# "18/10/2024 09:00:00","89.1","","",""


def create_parser(reader, mpan_map, messages):
    return HhParserSchneiderCsv(reader, mpan_map, messages)


def get_field(values, index, name):
    if len(values) > index:
        return values[index].strip()
    else:
        raise BadRequest(f"Can't find field {index}, {name}.")


def parse_values(values):
    start_date_str = get_field(values, 0, "Timestamp")
    start_date = validate_hh_start(
        to_utc(Datetime.strptime(start_date_str, "%d/%m/%Y %H:%M:%S"))
    )

    reading_str = get_field(values, 1, "Reading")
    reading_str = reading_str.replace(",", "")
    try:
        reading = Decimal(reading_str)
    except InvalidOperation as e:
        raise BadRequest(f"Problem parsing the number {reading_str}. {e}")
    return start_date, reading


class HhParserSchneiderCsv:
    def __init__(self, reader, mpan_map, messages):
        s = iterdecode(reader, "utf-8")
        self.shredder = zip(itertools.count(1), csv.reader(s))
        next(self.shredder)  # skip the title line
        self.line_number, self.values = next(self.shredder)
        _, self.pres_reading = parse_values(self.values)
        self.mpan_core = parse_mpan_core(next(iter(mpan_map.values())))

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.line_number, self.values = next(self.shredder)
            start_date, reading = parse_values(self.values)
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
                f"Problem at line number: {self.line_number}: {self.values}: "
                f"{e.description}"
            )
            raise e

    def close(self):
        self.shredder.close()
