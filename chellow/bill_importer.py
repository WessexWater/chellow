import threading
import traceback
import datetime
import collections
import pytz
from chellow.models import Batch, BillType, Tpr, ReadType
from werkzeug.exceptions import BadRequest
import importlib
from pkgutil import iter_modules
from chellow.models import set_read_write, Session
import chellow
import chellow.bill_parser_sse_edi

import_id = 0
import_lock = threading.Lock()
imports = {}


def find_parser_names():
    return ', '.join(
        '.' + name[12:].replace('_', '.') for module_finder, name, ispkg in
        iter_modules(chellow.__path__) if name.startswith('bill_parser_'))


class BillImport(threading.Thread):
    def __init__(self, sess, batch_id, file_name, file_size, f):
        threading.Thread.__init__(self)
        global import_id
        self.import_id = import_id
        import_id += 1

        self.batch_id = batch_id
        if file_size == 0:
            raise BadRequest("File has zero length")

        imp_mod = None
        parts = file_name.split('.')[::-1]
        for i in range(len(parts)):
            nm = 'bill_parser_' + '_'.join(parts[:i+1][::-1]).lower()
            try:
                imp_mod = nm, importlib.import_module('chellow.' + nm)
            except ImportError:
                pass

        if imp_mod is None:
            raise BadRequest(
                "Can't find a parser for the file '" + file_name +
                "'. The file name needs to have an extension that's one of " +
                "the following: " + find_parser_names() + ".")

        self.parser_name = imp_mod[0]
        self.parser = imp_mod[1].Parser(f)
        self.successful_bills = []
        self.failed_bills = []
        self.log = collections.deque()
        self.bill_num = None

    def _log(self, msg):
        with import_lock:
            self.log.appendleft(
                datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S") +
                ' - ' + msg)

    def status(self):
        if self.isAlive():
            if self.bill_num is None:
                return "Parsing file: I've reached line number " + \
                    str(self.parser.line_number) + "."
            else:
                return "Inserting raw bills: I've reached bill number " + \
                    str(self.bill_num) + "."
        else:
            return ''

    def run(self):
        sess = None
        try:
            sess = Session()
            self._log(
                "Starting to parse the file with '" + self.parser_name + "'.")
            set_read_write(sess)
            batch = Batch.get_by_id(sess, self.batch_id)
            raw_bills = self.parser.make_raw_bills()
            self._log(
                "Successfully parsed the file, and now I'm starting to "
                "insert the raw bills.")
            for self.bill_num, raw_bill in enumerate(raw_bills):
                try:
                    with sess.begin_nested():
                        sess.execute(
                            "set transaction isolation level serializable "
                            "read write")
                        bill_type = BillType.get_by_code(
                            sess, raw_bill['bill_type_code'])
                        bill = batch.insert_bill(
                            sess, raw_bill['account'], raw_bill['reference'],
                            raw_bill['issue_date'], raw_bill['start_date'],
                            raw_bill['finish_date'], raw_bill['kwh'],
                            raw_bill['net'], raw_bill['vat'],
                            raw_bill['gross'],
                            bill_type, raw_bill['breakdown'])
                        sess.flush()
                        for raw_read in raw_bill['reads']:
                            tpr_code = raw_read['tpr_code']
                            if tpr_code is None:
                                tpr = None
                            else:
                                tpr = Tpr.get_by_code(sess, tpr_code)

                            prev_type = ReadType.get_by_code(
                                sess, raw_read['prev_type_code'])
                            pres_type = ReadType.get_by_code(
                                sess, raw_read['pres_type_code'])
                            bill.insert_read(
                                sess, tpr, raw_read['coefficient'],
                                raw_read['units'], raw_read['msn'],
                                raw_read['mpan'], raw_read['prev_date'],
                                raw_read['prev_value'], prev_type,
                                raw_read['pres_date'], raw_read['pres_value'],
                                pres_type)
                        self.successful_bills.append(raw_bill)
                except BadRequest as e:
                    raw_bill['error'] = str(e.description)
                    self.failed_bills.append(raw_bill)

            if len(self.failed_bills) == 0:
                sess.commit()
                self._log(
                    "All the bills have been successfully loaded and attached "
                    "to the batch.")
            else:
                sess.rollback()
                self._log(
                    "The import has finished, but there were " +
                    str(len(self.failed_bills)) + " failures, and so the "
                    "whole import has been rolled back.")

        except:
            sess.rollback()
            self._log("I've encountered a problem: " + traceback.format_exc())
        finally:
            if sess is not None:
                sess.close()

    def make_fields(self):
        with import_lock:
            fields = {
                'log': tuple(self.log), 'is_alive': self.isAlive(),
                'importer_id': self.import_id}
            if not self.isAlive():
                fields['successful_bills'] = self.successful_bills
                fields['failed_bills'] = self.failed_bills
            return fields


def start_bill_import(sess, batch_id, file_name, file_size, f):
    with import_lock:
        bi = BillImport(sess, batch_id, file_name, file_size, f)
        imports[bi.import_id] = bi
        bi.start()

    return bi.import_id


def get_bill_import_ids(batch_id):
    with import_lock:
        return [k for k, v in imports.items() if v.batch_id == batch_id]


def get_bill_import(id):
    with import_lock:
        return imports[id]
