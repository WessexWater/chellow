from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Tpr', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    tpr_id = inv.getLong('tpr_id')
    tpr = Tpr.get_by_id(sess, tpr_id)
    render(inv, template, {'tpr': tpr})
finally:
    sess.close()