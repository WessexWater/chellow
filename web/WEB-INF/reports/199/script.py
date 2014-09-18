from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'BillType', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    bill_types = sess.query(BillType).order_by(BillType.code)
    render(inv, template, {'bill_types': bill_types})
finally:
    sess.close()