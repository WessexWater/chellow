from net.sf.chellow.monad import Monad
import threading
import traceback
import datetime
import collections
import pytz
import utils
import db
import computer
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'computer')
UserException = utils.UserException
BillType, GBatch, GReadType = db.BillType, db.GBatch, db.GReadType
Contract, MarketRole = db.Contract, db.MarketRole

importer_id = 0
import_lock = threading.Lock()
importers = {}


class GBillImporter(threading.Thread):
    def __init__(self, sess, g_batch_id, file_name, file_size, f):
        threading.Thread.__init__(self)
        global importer_id
        self.importer_id = importer_id
        importer_id += 1

        self.g_batch_id = g_batch_id
        if file_size == 0:
            raise UserException("File has zero length")

        contract = None
        parts = file_name.split('.')[::-1]
        for i in range(len(parts)):
            contr = db.Contract.find_by_role_code_name(
                sess, 'Z',
                'g_bill_parser_' + '.'.join(parts[:i+1][::-1]).lower())
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
                        MarketRole.code == 'Z',
                        Contract.name.like("g_bill_parser_%"))) + ".")

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
            self._log(
                "Starting to parse the file with '" +
                self.contract_name + "'.")
            sess = db.session()
            g_batch = GBatch.get_by_id(sess, self.g_batch_id)
            raw_bills = self.parser.make_raw_bills()
            self._log(
                "Successfully parsed the file, and now I'm starting to "
                "insert the raw bills.")
            for self.bill_num, raw_bill in enumerate(raw_bills):
                try:
                    db.set_read_write(sess)
                    bill_type = BillType.get_by_code(
                        sess, raw_bill['bill_type_code'])
                    g_bill = g_batch.insert_g_bill(
                        sess, bill_type, raw_bill['mprn'],
                        raw_bill['reference'], raw_bill['account'],
                        raw_bill['issue_date'], raw_bill['start_date'],
                        raw_bill['finish_date'], raw_bill['kwh'],
                        raw_bill['net_gbp'], raw_bill['vat_gbp'],
                        raw_bill['gross_gbp'], raw_bill['raw_lines'],
                        raw_bill['breakdown'])
                    sess.flush()
                    for raw_read in raw_bill['reads']:
                        prev_type = GReadType.get_by_code(
                            sess, raw_read['prev_type_code'])
                        pres_type = GReadType.get_by_code(
                            sess, raw_read['pres_type_code'])
                        g_read = g_bill.insert_g_read(
                            sess, raw_read['msn'], raw_read['prev_value'],
                            raw_read['prev_date'], prev_type,
                            raw_read['pres_value'], raw_read['pres_date'],
                            pres_type, raw_read['units'],
                            raw_read['correction_factor'],
                            raw_read['calorific_value'])

                        sess.expunge(g_read)
                    sess.commit()
                    self.successful_bills.append(raw_bill)
                    sess.expunge(g_bill)
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
        bi = GBillImporter(sess, batch_id, file_name, file_size, f)
        importers[bi.importer_id] = bi
        bi.start()
    finally:
        import_lock.release()

    return bi.importer_id


def get_bill_importer_ids(g_batch_id):
    try:
        import_lock.acquire()
        return [
            k for k, v in importers.iteritems() if v.g_batch_id == g_batch_id]
    finally:
        import_lock.release()


def get_bill_importer(id):
    try:
        import_lock.acquire()
        return importers[id]
    finally:
        import_lock.release()
