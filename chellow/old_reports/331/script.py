import os
import io
from net.sf.chellow.monad import Monad
import bill_import
import db
import templater
import utils

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'bill_import')
inv, template = globals()['inv'], globals()['template']
Batch = db.Batch
render = templater.render
UserException = utils.UserException


def make_fields(sess, batch, message=None):
    messages = [] if message is None else [str(message)]
    return {
        'messages': messages,
        'importer_ids': sorted(
            bill_import.get_bill_importer_ids(batch.id), reverse=True),
        'batch': batch}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        batch_id = inv.getLong('mop_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        render(inv, template, make_fields(sess, batch))
    else:
        batch_id = inv.getLong('mop_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        file_item = inv.getFileItem("import_file")
        f = io.StringIO(str(file_item.f.read(), 'utf8'))
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        f.seek(0)
        iid = bill_import.start_bill_importer(
            sess, batch.id, file_item.getName(), file_size, f)
        inv.sendSeeOther("/reports/333/output/?importer_id=" + str(iid))
except UserException as e:
    render(inv, template, make_fields(sess, batch, e), 400)
finally:
    if sess is not None:
        sess.close()
