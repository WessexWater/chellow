from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Tpr', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    tprs = sess.query(Tpr).order_by(Tpr.code).all()
    render(inv, template, {'tprs': tprs})
finally:
    sess.close()