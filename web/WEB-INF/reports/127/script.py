from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Ssc', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    ssc_id = inv.getLong('ssc_id')
    ssc = Ssc.get_by_id(sess, ssc_id)
    render(inv, template, {'ssc': ssc})
finally:
    sess.close()