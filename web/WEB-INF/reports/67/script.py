from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, RateScript = db.Contract, db.RateScript
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    contract_id = inv.getLong('dno_contract_id')
    contract = Contract.get_dno_by_id(sess, contract_id)
    rate_scripts = sess.query(RateScript).filter(
        RateScript.contract == contract).order_by(
        RateScript.start_date.desc()).all()

    config = db.Contract.get_non_core_by_name(sess, 'configuration')

    reports = []

    render(
        inv, template, {
            'contract': contract, 'rate_scripts': rate_scripts,
            'reports': reports})
finally:
    if sess is not None:
        sess.close()
