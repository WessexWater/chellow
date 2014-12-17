from decimal import Decimal
from net.sf.chellow.monad import Monad
import datetime
import pytz
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'bill_import')
UserException = utils.UserException


class EdiParser():
    def __init__(self, f):
        self.f_iterator = iter(f)

    def __iter__(self):
        return self

    def next(self):
        self.line = self.f_iterator.next().strip()
        if self.line[-1] != "'":
            raise UserException("This parser expects one segment per line.")
        self.elements = [
            element.split(':') for element in self.line[4:-1].split("+")]
        return self.line[:3]

    def to_decimal(self, components):
        result = Decimal(components[0])
        if len(components) > 1 and components[-1] == "R":
            result *= Decimal("-1")
        return result

    def to_date(self, component):
        return datetime.datetime.strptime(
            component, "%y%m%d").replace(tzinfo=pytz.utc)

    def to_int(self, component):
        return int(component)
