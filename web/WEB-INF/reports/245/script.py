from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'templater', 'db', 'scenario')
Contract, MarketRole = db.Contract, db.MarketRole

sess = None
try:
    sess = db.session()
    contracts = [Contract.get_non_core_by_name(sess, name) for name in scenario.PASSTHROUGH_NON_CORE]
    scenarios = sess.query(Contract).join(MarketRole).filter(MarketRole.code == 'X', Contract.name.like('scenario_%')).order_by(Contract.name).all()
    templater.render(inv, template, {'contracts': contracts, 'scenarios': scenarios})
finally:
    if sess is not None:
        sess.close()
