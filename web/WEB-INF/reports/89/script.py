from net.sf.chellow.monad import Monad

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch'], 
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH'],
        'templater': ['render']})


sess = None
try:
    sess = session()
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