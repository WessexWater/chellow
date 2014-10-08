from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from java.lang import System

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'MarketRole', 'Participant', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

def make_fields(sess, contract, message=None):
    parties = sess.query(Party).join(MarketRole, Participant).filter(MarketRole.code == 'X').order_by(Participant.code).all()
    messages = None if message is None else [str(message)]
    return {'contract': contract, 'messages': messages, 'parties': parties}


sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('supplier_contract_id')
        contract = Contract.get_supplier_by_id(sess, contract_id)
        render(inv, template, make_fields(sess, contract))
    else:
        set_read_write(sess)
        contract_id = inv.getLong('supplier_contract_id')
        contract = Contract.get_supplier_by_id(sess, contract_id)
        if inv.hasParameter('delete'):
            contract.delete(sess)
            sess.commit()
            inv.sendSeeOther('/reports/75/output/')
        else:
            party_id = inv.getLong('party_id')
            party = Party.get_by_id(sess, party_id)
            name = inv.getString('name')
            charge_script = inv.getString('charge_script')
            properties = inv.getString('properties')
            contract.update(sess, False, name, party, charge_script, properties)
            sess.commit()
            inv.sendSeeOther('/reports/77/output/?supplier_contract_id='
                + str(contract.id))
except UserException, e:
    sess.rollback()
    if str(e).startswith("There isn't a contract"):
        inv.sendNotFound(str(e))
    render(inv, template, make_fields(sess, contract, e), 400)
finally:
    sess.close()
