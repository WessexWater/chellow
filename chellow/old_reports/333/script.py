from net.sf.chellow.monad import Monad
import db
import bill_import
import templater
import utils

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'bill_import')
Batch = db.Batch
inv, template = globals()['inv'], globals()['template']
render = templater.render
UserException = utils.UserException


def make_fields(sess, importer, message=None):
    messages = None if message is None else [str(message)]
    batch = Batch.get_by_id(sess, importer.batch_id)
    fields = {'batch': batch, 'messages': messages}
    if importer is not None:
        imp_fields = importer.make_fields()
        if 'successful_bills' in imp_fields and \
                len(imp_fields['successful_bills']) > 0:
            fields['successful_max_registers'] = \
                max(
                    len(bill['reads']) for bill in imp_fields[
                        'successful_bills'])
        fields.update(imp_fields)
        fields['status'] = importer.status()
    return fields

sess = None
try:
    sess = db.session()
    imp_id = inv.getLong('importer_id')
    importer = bill_import.get_bill_importer(imp_id)
    render(inv, template, make_fields(sess, importer))
except UserException as e:
    render(inv, template, make_fields(sess, importer, e), 400)
finally:
    if sess is not None:
        sess.close()
