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
    market_role_id = inv.getLong('market_role_id')
    market_role = MarketRole.get_by_id(sess, market_role_id)
    render(inv, template, {'market_role': market_role})
finally:
    if sess is not None:
        sess.close()
