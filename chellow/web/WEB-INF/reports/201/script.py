from net.sf.chellow.monad import Monad
import db
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
BillType = db.BillType
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    bill_type_id = inv.getLong('bill_type_id')
    bill_type = BillType.get_by_id(sess, bill_type_id)
    render(inv, template, {'bill_type': bill_type})
finally:
    if sess is not None:
        sess.close()
