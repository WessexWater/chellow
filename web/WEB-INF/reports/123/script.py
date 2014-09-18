from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'MarketRole', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    market_role_id = inv.getLong('market_role_id')
    market_role = MarketRole.get_by_id(sess, market_role_id)
    render(inv, template, {'market_role': market_role})
finally:
    sess.close()