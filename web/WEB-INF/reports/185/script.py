from net.sf.chellow.monad import Monad
import db
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, MarketRole = db.Contract, db.MarketRole
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    mop_contracts = sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'M').order_by(Contract.name).all()
    render(inv, template, {'mop_contracts': mop_contracts})
finally:
    if sess is not None:
        sess.close()
