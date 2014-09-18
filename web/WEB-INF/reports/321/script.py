from net.sf.chellow.monad import Monad
from java.lang import System
from java.io import InputStreamReader
import StringIO

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'bill_import')


def make_fields(sess, batch, message=None):
    messages = [] if message is None else [str(message)]
    return {'messages': messages, 'importer_ids': sorted(bill_import.get_bill_importer_ids(batch.id), reverse=True), 'batch': batch}

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
        stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
        f = StringIO.StringIO()
        bt = stream.read()
        while bt != -1:
            f.write(unichr(bt))
            bt = stream.read()
        f.seek(0)
        id = bill_import.start_bill_importer(sess, batch.id, file_item.getName(), file_item.getSize(), f)
        inv.sendSeeOther("/reports/323/output/?importer_id=" + str(id))
except utils.UserException, e:
    templater.render(inv, template, make_fields(sess, batch, e), 400)
finally:
    if sess is not None:
        sess.close()