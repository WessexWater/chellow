import sys
import os
from net.sf.chellow.monad import Monad
import StringIO
import bill_import
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'bill_import')
inv, template = globals()['inv'], globals()['template']

Contract = db.Contract


def make_fields(sess, batch, message=None):
    messages = [] if message is None else [str(message)]
    parser_names = ', '.join(
        '.' + row[0][12:] for row in sess.query(Contract.name).filter(
            Contract.name.like("bill-parser-%")))
    return {
        'messages': messages,
        'importer_ids': sorted(
            bill_import.get_bill_importer_ids(batch.id), reverse=True),
        'batch': batch, 'parser_names': parser_names}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('supplier_batch_id')
        batch = db.Batch.get_by_id(sess, batch_id)
        templater.render(inv, template, make_fields(sess, batch))
    else:
        batch_id = inv.getLong('supplier_batch_id')
        batch = db.Batch.get_by_id(sess, batch_id)
        file_item = inv.getFileItem("import_file")
        f = StringIO.StringIO()
        if sys.platform.startswith('java'):
            from java.io import InputStreamReader

            stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
            bt = stream.read()
            while bt != -1:
                f.write(unichr(bt))
                bt = stream.read()
            file_size = file_item.getSize()
        else:
            f.writelines(file_item.f.stream)
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
        f.seek(0)
        id = bill_import.start_bill_importer(
            sess, batch.id, file_item.getName(), file_size, f)
        inv.sendSeeOther("/reports/323/output/?importer_id=" + str(id))
except utils.UserException, e:
    templater.render(inv, template, make_fields(sess, batch, e), 400)
finally:
    if sess is not None:
        sess.close()
