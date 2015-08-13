from net.sf.chellow.monad import Monad
import db
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
Party, MarketRole = db.Party, db.MarketRole
inv, template = globals()['inv'], globals()['template']


sess = None
try:
    sess = db.session()
    parties = sess.query(Party).join(MarketRole).order_by(
        Party.name, MarketRole.code).all()
    render(inv, template, {'parties': parties})
finally:
    if sess is not None:
        sess.close()
