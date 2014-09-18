from net.sf.chellow.monad import Monad
from java.lang import System
from java.io import InputStreamReader
import StringIO

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'set_read_write'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH'],
        'templater': ['render'],
        'bill_import': ['start_bill_importer', 'get_bill_importer_ids', 'get_bill_importer']})


def make_fields(sess, batch, message=None):
    messages = [] if message is None else [str(message)]
    return {'messages': messages, 'importer_ids': sorted(get_bill_importer_ids(batch.id), reverse=True), 'batch': batch}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('hhdc_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        render(inv, template, make_fields(sess, batch))
    else:
        batch_id = inv.getLong('hhdc_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        file_item = inv.getFileItem("import_file")
        stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
        f = StringIO.StringIO()
        bt = stream.read()
        while bt != -1:
            f.write(chr(bt))
            bt = stream.read()
        f.seek(0)
        id = start_bill_importer(sess, batch.id, file_item.getName(), file_item.getSize(), f)
        inv.sendSeeOther("/reports/329/output/?importer_id=" + str(id))
except UserException, e:
    render(inv, template, make_fields(sess, batch, e), 400)
finally:
    if sess is not None:
        sess.close()