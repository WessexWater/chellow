from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, MarketRole = db.Contract, db.MarketRole
render = templater.render

sess = None
try:
    sess = db.session()
    contracts = sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'X').order_by(Contract.name)
    render(inv, template, {'contracts': contracts})
finally:
    if sess is not None:
        sess.close()

