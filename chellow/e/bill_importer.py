import collections
import importlib
import threading
import traceback
from io import BytesIO
from pkgutil import iter_modules

from sqlalchemy import select

from werkzeug.exceptions import BadRequest

import chellow
import chellow.e.bill_parsers.engie_xls
from chellow.models import (
    Batch,
    BatchFile,
    BillType,
    Contract,
    ReadType,
    Session,
    Supply,
    Tpr,
)
from chellow.utils import ct_datetime_now, keydefaultdict


import_id = 0
import_lock = threading.Lock()
imports = {}


def find_parser_names():
    return [name for _, name, _ in iter_modules(chellow.e.bill_parsers.__path__)]


class BillImport(threading.Thread):
    def __init__(self, batch_contract, now=None):
        threading.Thread.__init__(self)
        global import_id
        self.import_id = import_id
        import_id += 1

        if isinstance(batch_contract, Batch):
            self.contract_id = None
            self.batch_id = batch_contract.id
        elif isinstance(batch_contract, Contract):
            self.contract_id = batch_contract.id
            self.batch_id = None
        else:
            raise BadRequest("batch_contract must be a Batch or Contract.")
        self.successful_bills = []
        self.failed_bills = []
        self.log = collections.deque()
        self.bill_num = None
        self.parser = None
        self.now = now

    def _log(self, msg):
        with import_lock:
            ts = ct_datetime_now() if self.now is None else self.now
            self.log.appendleft(f"{ts.strftime('%Y-%m-%d %H:%M:%S')} - {msg}")

    def status(self):
        if self.is_alive():
            if self.bill_num is not None:
                return f"Inserting raw bills: I've reached bill number {self.bill_num}."
            elif self.parser is not None:
                return (
                    f"Parsing file: I've reached line number {self.parser.line_number}."
                )
            else:
                return "Running"
        else:
            return "Not running"

    def run(self):
        try:
            batch_ids = []
            with Session() as sess:
                batch_q = select(Batch).order_by(Batch.reference)
                if self.batch_id is not None:
                    batch = Batch.get_by_id(sess, self.batch_id)
                    batch_q = batch_q.where(Batch.id == self.batch_id)
                elif self.contract_id is not None:
                    contract = Contract.get_by_id(sess, self.contract_id)
                    batch_q = batch_q.where(Batch.contract == contract)
                for batch in sess.scalars(batch_q):
                    batch_ids.append(batch.id)

            for batch_id in batch_ids:
                with Session() as sess:
                    batch = Batch.get_by_id(sess, batch_id)
                    self._log(f"Importing bills from batch {batch.reference}.")
                    bf_q = (
                        select(BatchFile)
                        .where(BatchFile.batch == batch)
                        .order_by(BatchFile.upload_timestamp)
                    )
                    bill_types = keydefaultdict(lambda k: BillType.get_by_code(sess, k))

                    tprs = keydefaultdict(
                        lambda k: None if k is None else Tpr.get_by_code(sess, k)
                    )

                    read_types = keydefaultdict(lambda k: ReadType.get_by_code(sess, k))

                    for bf in sess.scalars(bf_q):
                        self.parser = _process_batch_file(sess, bf, self._log)
                        for self.bill_num, raw_bill in enumerate(
                            self.parser.make_raw_bills()
                        ):
                            batch = bf.batch
                            sum_elem = sum(el["net"] for el in raw_bill["elements"])
                            raw_bill_net = raw_bill["net"]
                            if sum_elem != raw_bill_net:
                                raw_bill["error"] = (
                                    f"The sum of the elements' net {sum_elem} doesn't "
                                    f"equal the bill net {raw_bill_net}."
                                )
                            if "error" in raw_bill:
                                self.failed_bills.append(raw_bill)
                            else:
                                try:
                                    mpan_core = raw_bill["mpan_core"]
                                    supply = Supply.get_by_mpan_core(sess, mpan_core)
                                    with sess.begin_nested():
                                        bill = batch.insert_bill(
                                            sess,
                                            raw_bill["account"],
                                            raw_bill["reference"],
                                            raw_bill["issue_date"],
                                            raw_bill["start_date"],
                                            raw_bill["finish_date"],
                                            raw_bill["kwh"],
                                            raw_bill_net,
                                            raw_bill["vat"],
                                            raw_bill["gross"],
                                            bill_types[raw_bill["bill_type_code"]],
                                            raw_bill["breakdown"],
                                            supply,
                                        )
                                        for raw_element in raw_bill["elements"]:
                                            bill.insert_element(
                                                sess,
                                                raw_element["name"],
                                                raw_element["start_date"],
                                                raw_element["finish_date"],
                                                raw_element["net"],
                                                raw_element["breakdown"],
                                            )
                                        for raw_read in raw_bill["reads"]:
                                            bill.insert_read(
                                                sess,
                                                tprs[raw_read["tpr_code"]],
                                                raw_read["coefficient"],
                                                raw_read["units"],
                                                raw_read["msn"],
                                                raw_read["mpan"],
                                                raw_read["prev_date"],
                                                raw_read["prev_value"],
                                                read_types[raw_read["prev_type_code"]],
                                                raw_read["pres_date"],
                                                raw_read["pres_value"],
                                                read_types[raw_read["pres_type_code"]],
                                            )
                                        self.successful_bills.append(raw_bill)
                                except KeyError as e:
                                    err = raw_bill.get("error", "")
                                    raw_bill["error"] = err + " " + str(e)
                                    self.failed_bills.append(raw_bill)
                                except BadRequest as e:
                                    raw_bill["error"] = str(e.description)
                                    self.failed_bills.append(raw_bill)

                    if len(self.failed_bills) == 0:
                        sess.commit()
                        self._log(
                            "All the bills have been successfully loaded and attached "
                            "to the batch."
                        )
                    else:
                        sess.rollback()
                        self._log(
                            f"The import has finished, but there were "
                            f"{len(self.failed_bills)} "
                            f"failures, and so the whole import has been rolled back."
                        )
                        break

        except BadRequest as e:
            msg = f"Problem: {e.description}"
            if e.__cause__ is not None:
                msg += f" {traceback.format_exc()}"
            self._log(msg)
        except BaseException:
            self._log(f"I've encountered a problem: {traceback.format_exc()}")

    def make_fields(self):
        with import_lock:
            fields = {
                "log": tuple(self.log),
                "is_alive": self.is_alive(),
                "importer_id": self.import_id,
            }
            if not self.is_alive():
                fields["successful_bills"] = self.successful_bills
                fields["failed_bills"] = self.failed_bills
            return fields


def _process_batch_file(sess, batch_file, log_f):
    data = batch_file.data
    parser_name = batch_file.parser_name

    if len(data) == 0:
        raise BadRequest("File has zero length")

    try:
        imp_mod = importlib.import_module(f"chellow.e.bill_parsers.{parser_name}")
    except ImportError:
        raise BadRequest(f"Can't find a parser with the name '{parser_name}'.")

    parser = imp_mod.Parser(BytesIO(data))
    log_f(f"Starting to parse the file {batch_file.filename} with '{parser_name}'.")

    return parser


def start_bill_import(batch):
    with import_lock:
        bi = BillImport(batch)
        imports[bi.import_id] = bi
        bi.start()

    return bi.import_id


def start_bill_import_contract(contract):
    with import_lock:
        bi = BillImport(contract)
        imports[bi.import_id] = bi
        bi.start()

    return bi.import_id


def get_bill_import_ids(batch):
    with import_lock:
        return [k for k, v in imports.items() if v.batch_id == batch.id]


def get_bill_import_ids_contract(contract):
    with import_lock:
        return [k for k, v in imports.items() if v.contract_id == contract.id]


def get_bill_import(id):
    with import_lock:
        return imports[id]
