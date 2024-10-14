import csv
from codecs import iterdecode
from datetime import datetime as Datetime
from decimal import Decimal

from werkzeug.exceptions import BadRequest

from chellow.utils import (
    HH,
    parse_mpan_core,
    to_ct,
    to_utc,
)

# From the EDF Portal select:
# - Electricity
# - Half-hourly
# - Reactive Power and kWh combined
# export data as CSV
#
#
# "Month","MPAN","Measurement Type","Settlement Date","00:00",..,"00:00_Act_Est",
# "Apr-24", "2200000000000", "AI", "01-04-2024", "0.0000", ..., "Actual", "Actual",


def create_parser(reader, mpan_map, messages):
    return HhParserEdfCsv(reader, mpan_map, messages)


CHANNEL_LOOKUP = {
    "AI": "ACTIVE",
    "RI": "REACTIVE_IMP",
    "RE": "REACTIVE_EXP",
}

STATUS_LOOKUP = {
    "Actual": "A",
    "Estimated": "E",
    "-": "E",
}


def _get_field(values, index, name):
    if len(values) > index:
        return values[index].strip()
    else:
        raise BadRequest(f"Can't find field {index}, {name}.")


def _find_data(shredder):
    try:
        for line_number, values in enumerate(shredder, start=2):
            mpan_core_str = _get_field(values, 1, "MPAN Core")
            mpan_core = parse_mpan_core(mpan_core_str)
            channel_type_str = _get_field(values, 2, "Channel Type")
            channel_type = CHANNEL_LOOKUP[channel_type_str]
            start_day_ct_str = _get_field(values, 3, "Day")
            start_day_ct = to_ct(Datetime.strptime(start_day_ct_str, "%d-%m-%Y"))

            for i in range(50):
                val_idx = i + 4
                value_str = values[val_idx]
                if value_str == "-":
                    break

                status_idx = val_idx + 50
                status_str = values[status_idx]
                try:
                    status = STATUS_LOOKUP[status_str]
                except KeyError:
                    raise BadRequest(
                        f"Unrecognized status {status_str} at index {status_idx}."
                    )
                yield {
                    "mpan_core": mpan_core,
                    "channel_type": channel_type,
                    "start_date": to_utc(start_day_ct + HH * i),
                    "value": Decimal(value_str),
                    "status": status,
                }
    except BadRequest as e:
        e.description = (
            f"Problem at line number: {line_number} : {values} : {e.description}"
        )
        raise e


class HhParserEdfCsv:
    def __init__(self, reader, mpan_map, messages):
        s = iterdecode(reader, "utf-8")
        self.reader = csv.reader(s)
        next(self.reader)  # skip the title line
        self.data = iter(_find_data(self.reader))

    def __iter__(self):
        return self

    def __next__(self):
        return next(self.data)

    def close(self):
        self.shredder.close()
