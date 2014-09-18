from net.sf.chellow.monad import Monad

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'set_read_write'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH'],
        'templater': ['render']})


def make_fields(sess, contract, message=None):
        batches = sess.query(Batch).filter(Batch.contract == contract).order_by(Batch.reference.desc())
        messages = None if message is None else [str(e)]
        return {'contract': contract, 'batches': batches, 'messages': messages}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, contract_id)
        render(inv, template, make_fields(sess, contract))
    else:
        set_read_write(sess)
        contract_id = inv.getLong('hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, contract_id)
        reference = inv.getString("reference")
        description = inv.getString("description")

        batch = contract.insert_batch(sess, reference, description)
        sess.commit()
        inv.sendSeeOther("/reports/203/output/?hhdc_batch_id=" + str(batch.id))

except UserException, e:
    render(inv, template, make_fields(sess, contract, e))
finally:
    if sess is not None:
        sess.close()