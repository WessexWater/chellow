from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, Llfc = db.Contract, db.Llfc
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    dno_contract_id = inv.getLong('dno_contract_id')
    contract = Contract.get_dno_by_id(sess, dno_contract_id)
    llfcs = sess.query(Llfc).filter(Llfc.dno_id == contract.party.id).order_by(
        Llfc.code).all()
    render(inv, template, {'llfcs': llfcs, 'contract': contract})
finally:
    if sess is not None:
        sess.close()
