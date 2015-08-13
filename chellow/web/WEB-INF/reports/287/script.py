from net.sf.chellow.monad import Monad
import templater
import utils
import db
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
UserException = utils.UserException
Batch, Contract = db.Batch, db.Contract
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, contract, message=None):
    batches = sess.query(Batch).filter(
        Batch.contract == contract).order_by(Batch.reference.desc())
    messages = [] if message is None else [str(e)]
    return {'contract': contract, 'batches': batches, 'messages': messages}

sess = None
contract = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('supplier_contract_id')
        contract = Contract.get_supplier_by_id(sess, contract_id)
        render(inv, template, make_fields(sess, contract))
    else:
        db.set_read_write(sess)
        contract_id = inv.getLong('supplier_contract_id')
        contract = Contract.get_supplier_by_id(sess, contract_id)
        reference = inv.getString("reference")
        description = inv.getString("description")

        batch = contract.insert_batch(sess, reference, description)
        sess.commit()
        inv.sendSeeOther(
            "/reports/91/output/?supplier_batch_id=" + str(batch.id))

except UserException, e:
    sess.rollback()
    if contract is None:
        raise e
    else:
        render(inv, template, make_fields(sess, contract, e), 400)
finally:
    if sess is not None:
        sess.close()
