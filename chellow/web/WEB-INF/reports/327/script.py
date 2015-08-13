import os
import sys
import StringIO
from net.sf.chellow.monad import Monad
import templater
import db
import utils
import bill_import
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'bill_import')
render = templater.render
Batch = db.Batch
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']


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
        batch_id = inv.getLong('hhdc_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        render(inv, template, make_fields(sess, batch))
    else:
        batch_id = inv.getLong('hhdc_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        file_item = inv.getFileItem("import_file")

        f = StringIO.StringIO()
        if sys.platform.startswith('java'):
            from java.io import InputStreamReader
            stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
            bt = stream.read()
            while bt != -1:
                f.write(chr(bt))
                bt = stream.read()
        else:
            f.writelines(file_item.f.stream)
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        f.seek(0)
        id = bill_import.start_bill_importer(
            sess, batch.id, file_item.getName(), file_size, f)
        inv.sendSeeOther("/reports/329/output/?importer_id=" + str(id))
except UserException, e:
    render(inv, template, make_fields(sess, batch, e), 400)
finally:
    if sess is not None:
        sess.close()
