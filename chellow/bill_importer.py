import collections
import importlib
import threading
import traceback
from io import BytesIO
from pkgutil import iter_modules

import chellow
import chellow.bill_parser_engie_xls
from chellow.models import (
    Batch, BatchFile, BillType, ReadType, Session, Supply, Tpr,
)
from chellow.utils import keydefaultdict, utc_datetime_now

from werkzeug.exceptions import BadRequest


import_id = 0
import_lock = threading.Lock()
imports = {}


def find_parser_names():
    return [
        name[12:] for _, name, _ in iter_modules(chellow.__path__)
        if name.startswith('bill_parser_')
    ]


class BillImport(threading.Thread):
    def __init__(self, batch):
        threading.Thread.__init__(self)
        global import_id
        self.import_id = import_id
        import_id += 1

        self.batch_id = batch.id
        self.successful_bills = []
        self.failed_bills = []
        self.log = collections.deque()
        self.bill_num = None
        self.parser = None

    def _log(self, msg):
        with import_lock:
            self.log.appendleft(
                f"{utc_datetime_now().strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

    def status(self):
        if self.isAlive():
            if self.bill_num is not None:
                return "Inserting raw bills: I've reached bill number " + \
                    str(self.bill_num) + "."
            elif self.parser is not None:
                return "Parsing file: I've reached line number " + \
                    str(self.parser.line_number) + "."
            else:
                return 'Running'
        else:
            return 'Not running'

    def run(self):
        sess = None
        try:
            sess = Session()
            batch = Batch.get_by_id(sess, self.batch_id)

            bill_types = keydefaultdict(
                lambda k: BillType.get_by_code(sess, k))

            tprs = keydefaultdict(
                lambda k: None if k is None else Tpr.get_by_code(sess, k))

            read_types = keydefaultdict(
                lambda k: ReadType.get_by_code(sess, k))

            for bf in sess.query(BatchFile).filter(
                    BatchFile.batch == batch).order_by(
                    BatchFile.upload_timestamp):

                self.parser = _process_batch_file(sess, bf, self._log)
                for self.bill_num, raw_bill in enumerate(
                        self.parser.make_raw_bills()):

                    if 'error' in raw_bill:
                        self.failed_bills.append(raw_bill)
                    else:
                        try:
                            mpan_core = raw_bill['mpan_core']
                            supply = Supply.get_by_mpan_core(sess, mpan_core)
                            with sess.begin_nested():
                                bill = batch.insert_bill(
                                    sess, raw_bill['account'],
                                    raw_bill['reference'],
                                    raw_bill['issue_date'],
                                    raw_bill['start_date'],
                                    raw_bill['finish_date'],
                                    raw_bill['kwh'],
                                    raw_bill['net'],
                                    raw_bill['vat'],
                                    raw_bill['gross'],
                                    bill_types[raw_bill['bill_type_code']],
                                    raw_bill['breakdown'], supply)
                                for raw_read in raw_bill['reads']:
                                    bill.insert_read(
                                        sess, tprs[raw_read['tpr_code']],
                                        raw_read['coefficient'],
                                        raw_read['units'],
                                        raw_read['msn'], raw_read['mpan'],
                                        raw_read['prev_date'],
                                        raw_read['prev_value'],
                                        read_types[raw_read['prev_type_code']],
                                        raw_read['pres_date'],
                                        raw_read['pres_value'],
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
                    f"The import has finished, but there were "
                    f"{len(self.failed_bills)} failures, and so the "
                    f"whole import has been rolled back.")

        except BadRequest as e:
            sess.rollback()
            self._log(f"Problem: {e.description}")
        except BaseException:
            sess.rollback()
            self._log(f"I've encountered a problem: {traceback.format_exc()}")
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


def _process_batch_file(sess, batch_file, log_f):
    data = batch_file.data
    parser_name = batch_file.parser_name

    if len(data) == 0:
        raise BadRequest("File has zero length")

    try:
        imp_mod = importlib.import_module(
            f'chellow.bill_parser_{parser_name}')
    except ImportError:
        raise BadRequest(
            f"Can't find a parser with the name '{parser_name}'.")

    parser = imp_mod.Parser(BytesIO(data))
    log_f(f"Starting to parse the file with '{parser_name}'.")

    return parser


def start_bill_import(batch):
    with import_lock:
        bi = BillImport(batch)
        imports[bi.import_id] = bi
        bi.start()

    return bi.import_id


def get_bill_import_ids(batch):
    with import_lock:
        return [k for k, v in imports.items() if v.batch_id == batch.id]


def get_bill_import(id):
    with import_lock:
        return imports[id]
