from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'MarketRole', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    contracts = sess.query(Contract).join(MarketRole).filter(MarketRole.code == 'X').order_by(Contract.name)
    render(inv, template, {'contracts': contracts})
finally:
    sess.close()