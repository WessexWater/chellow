from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, MarketRole = db.Contract, db.MarketRole
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    hhdc_contracts = sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'C').order_by(Contract.name).all()
    templater.render(inv, template, {'hhdc_contracts': hhdc_contracts})
finally:
    if sess is not None:
        sess.close()
