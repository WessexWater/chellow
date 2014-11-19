from net.sf.chellow.monad import Monad
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
from sqlalchemy.sql import func

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'computer')
UserException = utils.UserException
BillType, Batch, Tpr, ReadType = db.BillType, db.Batch, db.Tpr, db.ReadType

importer_id = 0
import_lock = threading.Lock()
importers = {}

class BillImporter(threading.Thread):
    def __init__(self, sess, batch_id, file_name, file_size, f):
        threading.Thread.__init__(self)
        global importer_id
        self.importer_id = importer_id
        importer_id += 1

        self.batch_id = batch_id
        if file_size == 0:
            raise UserException(null, "File has zero length")

        contract = None
        parts = file_name.split('.')[::-1]
        for i in range(len(parts)):
             contr = db.Contract.find_by_role_code_name(
                    sess, 'Z',
                    'bill-parser-' + '.'.join(parts[:i+1][::-1]).lower())
             if contr is not None:
                 contract = contr

        if contract is None:
            raise UserException(
                "Can't find a parser for the file '" + file_name +
                "'. The file name needs to have an extension that's one of " +
                "the following: " +
                ','.join(
                    name[0][12:] for name in sess.query(Contract.name).join(
                        MarketRole).filter(
                        MarketRole.code=='Z',
                        Contract.name.like("bill-parser-%"))) + ".")

        self.contract_name = contract.name
        self.parser = computer.contract_func({}, contract, 'Parser', None)(f)
        self.successful_bills = []
        self.failed_bills = []
        self.log = collections.deque()
        self.bill_num = None

    def _log(self, msg):
        try:
            import_lock.acquire()
            self.log.appendleft(
                datetime.datetime.now(pytz.utc).strftime("%Y-%m-%d %H:%M:%S") +
                ' - ' + msg)
        finally:
            import_lock.release()

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
            self._log("Starting to parse the file with '" +
                self.contract_name + "'.")
            sess = db.session()
            batch = Batch.get_by_id(sess, self.batch_id)
            raw_bills = self.parser.make_raw_bills()
            self._log(
                "Successfully parsed the file, and now I'm starting to "
                "insert the raw bills.")
            for self.bill_num, raw_bill in enumerate(raw_bills):
                try:
                    db.set_read_write(sess)
                    bill_type = BillType.get_by_code(
                        sess, raw_bill['bill_type_code'])
                    bill = batch.insert_bill(
                        sess, raw_bill['account'], raw_bill['reference'],
                        raw_bill['issue_date'], raw_bill['start_date'],
                        raw_bill['finish_date'], raw_bill['kwh'],
                        raw_bill['net'], raw_bill['vat'], raw_bill['gross'],
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
                        read = bill.insert_read(
                            sess, tpr, raw_read['coefficient'],
                            raw_read['units'], raw_read['msn'],
                            raw_read['mpan'], raw_read['prev_date'],
                            raw_read['prev_value'], prev_type,
                            raw_read['pres_date'], raw_read['pres_value'],
                            pres_type)
                        sess.expunge(read)
                    sess.commit()
                    self.successful_bills.append(raw_bill)
                    sess.expunge(bill)
                except UserException, e:
                    sess.rollback()
                    raw_bill['error'] = str(e)
                    self.failed_bills.append(raw_bill)


            if len(self.failed_bills) == 0:
                self._log(
                    "All the bills have been successfully loaded and attached "
                    "to the batch.")
            else:
		self._log(
                    "The import has finished, but " +
                    str(len(self.failed_bills)) + " bills failed to load.")

        except:
            self._log("I've encountered a problem: " + traceback.format_exc())
        finally:
            if sess is not None:
                sess.close()

    def make_fields(self):
        try:
            import_lock.acquire()
            fields = {
                'log': tuple(self.log), 'is_alive': self.isAlive(),
                'importer_id': self.importer_id}
            if not self.isAlive():
                fields['successful_bills'] = self.successful_bills
                fields['failed_bills'] = self.failed_bills
            return fields
        finally:
            import_lock.release()


def start_bill_importer(sess, batch_id, file_name, file_size, f):
    try:
        import_lock.acquire()
        bi = BillImporter(sess, batch_id, file_name, file_size, f)
        importers[bi.importer_id] = bi
        bi.start()
    finally:
        import_lock.release()
     
    return bi.importer_id

def get_bill_importer_ids(batch_id):
    try:
        import_lock.acquire()
        return [k for k, v in importers.iteritems() if v.batch_id == batch_id]
    finally:
        import_lock.release()

def get_bill_importer(id):
    try:
        import_lock.acquire()
        return importers[id]
    finally:
        import_lock.release()
