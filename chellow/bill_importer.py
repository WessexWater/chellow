import threading
import traceback
import collections
from werkzeug.exceptions import BadRequest
import importlib
from pkgutil import iter_modules
from chellow.models import Session, Era, Supply, Batch, BillType, Tpr, ReadType
import chellow
import chellow.bill_parser_engie_xls
from chellow.utils import keydefaultdict, utc_datetime_now
from sqlalchemy import or_, and_


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
                utc_datetime_now().strftime("%Y-%m-%d %H:%M:%S") + ' - ' + msg)

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

            bill_types = keydefaultdict(
                lambda k: BillType.get_by_code(sess, k))

            tprs = keydefaultdict(
                lambda k: None if k is None else Tpr.get_by_code(sess, k))

            read_types = keydefaultdict(
                lambda k: ReadType.get_by_code(sess, k))

            batch = Batch.get_by_id(sess, self.batch_id)
            contract = batch.contract
            raw_bills = self.parser.make_raw_bills()
            self._log(
                "Successfully parsed the file, and now I'm starting to "
                "insert the raw bills.")
            for self.bill_num, raw_bill in enumerate(raw_bills):
                try:
                    account = raw_bill['account']
                    supply = sess.query(Supply).join(Era).filter(
                        or_(
                            and_(
                                Era.imp_supplier_contract == contract,
                                Era.imp_supplier_account == account),
                            and_(
                                Era.exp_supplier_contract == contract,
                                Era.exp_supplier_account == account),
                            and_(
                                Era.mop_contract == contract,
                                Era.mop_account == account),
                            and_(
                                Era.dc_contract == contract,
                                Era.dc_account == account))
                        ).distinct().order_by(Supply.id).first()

                    if supply is None:
                        raise BadRequest(
                            "Can't find an era with contract '" +
                            contract.name + "' and account '" + account + "'.")
                    with sess.begin_nested():
                        bill = batch.insert_bill(
                            sess, account, raw_bill['reference'],
                            raw_bill['issue_date'], raw_bill['start_date'],
                            raw_bill['finish_date'], raw_bill['kwh'],
                            raw_bill['net'], raw_bill['vat'],
                            raw_bill['gross'],
                            bill_types[raw_bill['bill_type_code']],
                            raw_bill['breakdown'], supply)
                        for raw_read in raw_bill['reads']:
                            bill.insert_read(
                                sess, tprs[raw_read['tpr_code']],
                                raw_read['coefficient'], raw_read['units'],
                                raw_read['msn'], raw_read['mpan'],
                                raw_read['prev_date'], raw_read['prev_value'],
                                read_types[raw_read['prev_type_code']],
                                raw_read['pres_date'], raw_read['pres_value'],
                                read_types[raw_read['pres_type_code']])
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

        except BadRequest as e:
            sess.rollback()
            self._log("Problem: " + e.description)
        except BaseException:
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
