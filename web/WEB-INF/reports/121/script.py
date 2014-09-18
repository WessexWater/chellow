from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'MarketRole', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    market_roles = sess.query(MarketRole).from_statement("select market_role.* from market_role order by market_role.code").all()
    render(inv, template, {'market_roles': market_roles})
finally:
    sess.close()