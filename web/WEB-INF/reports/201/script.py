from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'BillType', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    bill_type_id = inv.getLong('bill_type_id')
    bill_type = BillType.get_by_id(sess, bill_type_id)
    render(inv, template, {'bill_type': bill_type})
finally:
    sess.close()