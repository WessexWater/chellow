from net.sf.chellow.monad import Monad
import sys
import traceback
import decimal
import itertools
import datetime
import pytz

Monad.getUtils()['impt'](globals(), 'utils')
UserException, parse_mpan_core = utils.UserException, utils.parse_mpan_core
HH = utils.HH

def create_parser(reader, mpan_map):
    return StarkDf2HhParser(reader, mpan_map)


class StarkDf2HhParser():
    def __init__(self, reader, mpan_map):
        self.line = self.line_number = None
        self.reader = itertools.izip(itertools.count(1), reader)

        self.line_number, self.line = self.reader.next()
        if self.line.strip().upper() != "#F2":
            raise UserException("The first line must be '#F2'.")
        self.sensor_map = {
            1: 'ACTIVE', 2: 'ACTIVE', 3: 'REACTIVE_IMP', 4: 'REACTIVE_EXP'}

    def __iter__(self):
        return self

    def next(self):
        local_datum = None
        try:
            while local_datum is None:
                self.line_number, self.line = self.reader.next()
                lline = self.line.strip().upper()
                if lline.startswith("#O"):
                    self.core = parse_mpan_core(lline[2:])
                elif lline.startswith("#S"):
                    sensor = int(lline[2:].strip())
                    try:
                        self.channel_type = self.sensor_map[sensor]
                    except KeyError:
                        raise UserException(
                            "The sensor number must be between 1 and 4 "
                            "inclusive.")
                elif lline.startswith("#F2") or len(lline) == 0:
                    continue
                else:
                    fields = [f.strip() for f in lline.split(',')]
                    if len(fields) != 4:
                        raise UserException(
                            "There should be 4 comma separated values, but I "
                            "found " + str(len(fields)) + ".")

                    d_day, d_month, d_year = map(int, fields[0].split('/'))
                    time_fields = map(int, fields[1].split(':'))
                    if len(time_fields) > 2 and time_fields[2] != 0:
                        raise UserException(
                            "The number of seconds (if present) must always "
                            "be zero.") 
                    start_date = datetime.datetime(
                        d_year, d_month, d_day, time_fields[0], time_fields[1],
                        tzinfo=pytz.utc) - HH

                    try:
                        value = decimal.Decimal(fields[2])
                    except ValueError, e:
                        raise UserException(
                            "Problem parsing the value: " + valueStr)
                    status = fields[3][-1]
                    local_datum = {
                        'mpan_core': self.core,
                        'channel_type': self.channel_type,
                        'start_date': start_date, 'value': value,
                        'status': status}
            return local_datum
        except UserException, e:
            raise UserException(
                "Problem at line number: " + str(self.line_number) + ": " +
                self.line + ": " + str(e))

    def close(self):
        self.reader.close()

    def get_status(self):
        return "Reached line number: " + str(self.line_number)
