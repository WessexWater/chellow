from net.sf.chellow.monad import Monad
import csv
from dateutil.relativedelta import relativedelta
import itertools
import decimal
import datetime
from datetime import timedelta
import pytz

Monad.getUtils()['impt'](globals(), 'utils', 'templater')
parse_mpan_core, UserException = utils.parse_mpan_core, utils.UserException
HH = utils.HH


def create_parser(reader,mpan_map):
    return HhParserBglobal(reader, mpan_map)


class HhParserBglobal():
    def __init__(self, reader, mpan_map):
        self.shredder = itertools.izip(itertools.count(1), csv.reader(reader))
        self.line_number, self.values = self.shredder.next()
        self.mpan_map = mpan_map
        self.col_idx = 0

    def __iter__(self):
        return self

    def next(self):
        datum = None
        try:
            while datum is None:   
                if self.col_idx > 50:
                    self.line_number, self.values = self.shredder.next()
                    if len(self.values) == 0:
                        continue
                    self.col_idx = 0

                if self.col_idx == 0:
                    try:
                        self.core = self.values[self.col_idx]
                    except KeyError:
                        raise UserException(
                            "There doesn't seem to be an MPAN Core at the "
                            "beginning of this line. ")
                    self.core = self.mpan_map.get(self.core, self.core)
                    self.core = parse_mpan_core(self.core)
                elif self.col_idx == 2:
                    day, month, year = map(
                        int, self.values[self.col_idx].split('/'))
                    self.date = datetime.datetime(
                        year, month, day, tzinfo=pytz.utc)
                elif 2 < self.col_idx < len(self.values):
                    hh_value = self.values[self.col_idx].strip()
                    mins = 30 * (self.col_idx - 3)
                    if len(hh_value) > 0:
                        datum = {
                            'mpan_core': self.core, 'channel_type': 'ACTIVE',
                            'start_date': self.date + timedelta(minutes=mins),
                            'value': decimal.Decimal(hh_value), 'status': 'A'}

                self.col_idx += 1
        except UserException, e:
            raise UserException(
                "Problem at line number: " + str(self.line_number) + ": " +
                str(e))
        return datum

    def close(self):
        self.shredder.close()
