from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
MarketRole = db.MarketRole
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    market_roles = sess.query(MarketRole).order_by(MarketRole.code).all()
    render(inv, template, {'market_roles': market_roles})
finally:
    if sess is not None:
        sess.close()
