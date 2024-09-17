import csv
import itertools
from codecs import iterdecode
from datetime import datetime as Datetime
from decimal import Decimal

from werkzeug.exceptions import BadRequest

from chellow.utils import parse_channel_type, parse_mpan_core, to_utc, validate_hh_start


def create_parser(reader, mpan_map, messages):
    return HhParserCsvSimple(reader, mpan_map, messages)


class HhParserCsvSimple:
    def __init__(self, reader, mpan_map, messages):
        s = iterdecode(reader, "utf-8")
        self.shredder = zip(itertools.count(1), csv.reader(s))
        next(self.shredder)  # skip the title line
        self.values = None

    def get_field(self, index, name):
        if len(self.values) > index:
            return self.values[index].strip()
        else:
            raise BadRequest("Can't find field " + index + ", " + name + ".")

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.line_number, self.values = next(self.shredder)
            mpan_core_str = self.get_field(0, "MPAN Core")
            datum = {"mpan_core": parse_mpan_core(mpan_core_str)}
            channel_type_str = self.get_field(1, "Channel Type")
            datum["channel_type"] = parse_channel_type(channel_type_str)

            start_date_str = self.get_field(2, "Start Date")
            datum["start_date"] = validate_hh_start(
                to_utc(Datetime.strptime(start_date_str, "%Y-%m-%d %H:%M"))
            )

            value_str = self.get_field(3, "Value")
            datum["value"] = Decimal(value_str)

            status = self.get_field(4, "Status")
            if len(status) != 1:
                raise BadRequest(
                    "The status character must be one character in length."
                )
            datum["status"] = status
            return datum
        except BadRequest as e:
            e.description = "".join(
                "Problem at line number: ",
                str(self.line_number),
                ": ",
                str(self.values),
                ": ",
                e.description,
            )
            raise e

    def close(self):
        self.shredder.close()
