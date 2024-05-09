import decimal
import itertools

from werkzeug.exceptions import BadRequest

from chellow.utils import HH, parse_mpan_core, utc_datetime


def create_parser(reader, mpan_map, messages):
    return StarkDf2HhParser(reader, mpan_map, messages)


class StarkDf2HhParser:
    def __init__(self, reader, mpan_map, messages):
        self.line = self.line_number = None
        self.reader = zip(itertools.count(1), reader)

        self.line_number, self.line = next(self.reader)
        if self.line.strip().upper() != "#F2":
            raise BadRequest("The first line must be '#F2'.")
        self.sensor_map = {
            1: "ACTIVE",
            2: "ACTIVE",
            3: "REACTIVE_IMP",
            4: "REACTIVE_EXP",
        }

        self.mpan_map = mpan_map
        self.messages = messages

    def __iter__(self):
        return self

    def __next__(self):
        local_datum = None
        try:
            while local_datum is None:
                self.line_number, self.line = next(self.reader)
                lline = self.line.strip().upper()
                if lline.startswith("#O"):
                    outstation_parts = lline[2:].split("-")
                    self.core = parse_mpan_core(outstation_parts[0])
                    if self.core in self.mpan_map and self.mpan_map[self.core] is None:
                        msg = f"The MPAN core {self.core} has been ignored"
                        if len(self.messages) == 0 or self.messages[-1] != msg:
                            self.messages.append(
                                f"The MPAN core {self.core} has been ignored"
                            )
                        self.core = None
                        continue

                elif lline.startswith("#S"):
                    sensor = int(lline[2:].strip())
                    try:
                        self.channel_type = self.sensor_map[sensor]
                    except KeyError:
                        raise BadRequest(
                            "The sensor number must be between 1 and 4 " "inclusive."
                        )
                elif lline.startswith("#F2") or len(lline) == 0:
                    continue
                else:
                    fields = [f.strip() for f in lline.split(",")]
                    if len(fields) != 4:
                        raise BadRequest(
                            "There should be 4 comma separated values, but I "
                            "found " + str(len(fields)) + "."
                        )

                    d_day, d_month, d_year = map(int, fields[0].split("/"))
                    time_fields = tuple(map(int, fields[1].split(":")))
                    if len(time_fields) > 2 and time_fields[2] != 0:
                        raise BadRequest(
                            "The number of seconds (if present) must always " "be zero."
                        )
                    start_date = (
                        utc_datetime(
                            d_year, d_month, d_day, time_fields[0], time_fields[1]
                        )
                        - HH
                    )

                    try:
                        value = decimal.Decimal(fields[2])
                    except ValueError:
                        raise BadRequest("Problem parsing the value: " + fields[2])
                    status = fields[3][-1]

                    if self.core is None:
                        continue

                    local_datum = {
                        "mpan_core": self.core,
                        "channel_type": self.channel_type,
                        "start_date": start_date,
                        "value": value,
                        "status": status,
                    }
            return local_datum
        except BadRequest as e:
            e.description = "".join(
                (
                    "Problem at line number: ",
                    str(self.line_number),
                    ": ",
                    self.line,
                    ": ",
                    e.description,
                )
            )
            raise e

    def close(self):
        self.reader.close()

    def get_status(self):
        return "Reached line number: " + str(self.line_number)
