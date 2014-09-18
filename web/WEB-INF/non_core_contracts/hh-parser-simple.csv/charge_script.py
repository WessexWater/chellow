from net.sf.chellow.monad import Monad
from java.lang import System
import threading
import traceback
import csv
import datetime
import collections
import decimal
import tempfile
import dateutil
import dateutil.parser
import pytz
from sqlalchemy import or_
import csv
import itertools
import datetime

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'set_read_write', 'Site', 'Supply', 'Source', 'GeneratorType', 'GspGroup', 'Pc', 'Cop', 'Era', 'Mtc', 'Ssc', 'HhDatum', 'Snag', 'BillType', 'Tpr', 'ReadType'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH', 'parse_hh_start', 'parse_mpan_core', 'parse_bool', 'validate_hh_start', 'parse_channel_type'],
        'templater': ['render']})


def create_parser(reader, mpan_map):
    return HhParserCsvSimple(reader, mpan_map)

class HhParserCsvSimple():
    def __init__(self, reader, mpan_map):
        self.shredder = itertools.izip(itertools.count(1), csv.reader(reader))
        self.shredder.next()  # skip the title line
        self.values = None

    def get_field(self, index, name):
        if len(self.values) > index:
            return self.values[index].strip()
        else:
            raise UserException("Can't find field " + index + ", " + name + ".")

    def __iter__(self):
        return self

    def next(self):
        try:
            self.line_number, self.values = self.shredder.next()
            mpan_core_str = self.get_field(0, "MPAN Core")
            datum = {'mpan_core': parse_mpan_core(mpan_core_str)}
            channel_type_str = self.get_field(1, "Channel Type")
            datum['channel_type'] = parse_channel_type(channel_type_str)
 
            start_date_str = self.get_field(2, "Start Date")
            datum['start_date'] = validate_hh_start(datetime.datetime.strptime(start_date_str, "%Y-%m-%d %h:%M").replace(tzinfo=pytz.utc))

            value_str = self.get_field(3, "Value")
            datum['value'] = decimal.Decimal(value_str)

            status = self.get_field(4, "Status")
            if len(status) != 1:
                raise UserException("The status character must be one character in length.")
            datum['status'] = status
            return datum
        except UserException, e:
            raise UserException("Problem at line number: " + str(self.line_number) + ": "  + str(self.values) + ": " + str(e))
            

    def close(self):
        self.shredder.close()