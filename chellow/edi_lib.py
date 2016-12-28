from decimal import Decimal
from datetime import datetime as Datetime
from werkzeug.exceptions import BadRequest
from chellow.utils import to_utc


class EdiParser():
    def __init__(self, f):
        self.f_iterator = iter(f)

    def __iter__(self):
        return self

    def __next__(self):
        self.line = next(self.f_iterator).strip()
        if self.line[-1] != "'":
            raise BadRequest("This parser expects one segment per line.")
        self.elements = [
            element.split(':') for element in self.line[4:-1].split("+")]
        return self.line[:3]

    def to_decimal(self, components):
        result = Decimal(components[0])
        if len(components) > 1 and components[-1] == "R":
            result *= Decimal("-1")
        return result

    def to_date(self, component):
        return to_utc(Datetime.strptime(component, "%y%m%d"))

    def to_int(self, component):
        return int(component)
