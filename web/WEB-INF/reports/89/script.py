from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
Batch, Contract = db.Batch, db.Contract

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('supplier_contract_id')
        if contract_id is None:
            contract_id = inv.getLong('supplier-contract-id')
        contract = Contract.get_supplier_by_id(sess, contract_id)
        batches = sess.query(Batch).filter(Batch.contract == contract).order_by(Batch.reference.desc())
        render(inv, template, {'contract': contract, 'batches': batches})
finally:
    if sess is not None:
        sess.close()
