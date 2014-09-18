from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Source', 'MarketRole', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    sources = sess.query(Source).order_by(Source.code).all()
    render(inv, template, {'sources': sources})
finally:
    sess.close()