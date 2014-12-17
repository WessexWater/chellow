from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract, Batch = db.Contract, db.Batch
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, contract_id)
        batches = sess.query(Batch).filter(
            Batch.contract == contract).order_by(Batch.reference.desc()).all()
        templater.render(
            inv, template, {'contract': contract, 'batches': batches})
finally:
    if sess is not None:
        sess.close()
