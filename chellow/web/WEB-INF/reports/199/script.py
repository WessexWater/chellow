from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
BillType = db.BillType
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    bill_types = sess.query(BillType).order_by(BillType.code)
    render(inv, template, {'bill_types': bill_types})
finally:
    if sess is not None:
        sess.close()
