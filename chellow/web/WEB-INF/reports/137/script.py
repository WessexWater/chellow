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
    dno_contracts = sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'R').order_by(Contract.name).all()

    render(inv, template, {'dno_contracts': dno_contracts})
finally:
    if sess is not None:
        sess.close()
