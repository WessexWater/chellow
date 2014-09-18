from net.sf.chellow.monad import Monad
from java.lang import System
import tempfile

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'set_read_write'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH'],
        'templater': ['render'],
        'bill_import': ['get_bill_importer']})

def make_fields(sess, importer, message=None):
    messages = None if message is None else [str(message)]
    batch = Batch.get_by_id(sess, importer.batch_id)
    fields = {'batch': batch, 'messages': messages}
    if importer is not None:
        imp_fields = importer.make_fields()
        if 'successful_bills' in imp_fields and len(imp_fields['successful_bills']) > 0:
            fields['successful_max_registers'] = max(len(bill['reads']) for bill in imp_fields['successful_bills'])
        fields.update(imp_fields)
        fields['status'] = importer.status()
    return fields

sess = None
try:
    sess = session()
    imp_id = inv.getLong('importer_id')
    importer = get_bill_importer(imp_id)
    render(inv, template, make_fields(sess, importer))
except UserException, e:
    render(inv, template, make_fields(sess, e), 400)
finally:
    if sess is not None:
        sess.close()