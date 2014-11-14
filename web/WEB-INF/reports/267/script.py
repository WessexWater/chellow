from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
RateScript = db.RateScript

sess = None
try:
    sess = db.session()
    contract_id = inv.getLong('non_core_contract_id')
    contract = db.Contract.get_non_core_by_id(sess, contract_id)
    rate_scripts = sess.query(RateScript).filter(
        RateScript.contract_id == contract_id).order_by(
        RateScript.start_date.desc()).all()
    templater.render(
        inv, template, {'contract': contract, 'rate_scripts': rate_scripts})
finally:
    if sess is not None:
        sess.close()
