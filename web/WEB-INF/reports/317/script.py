from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Party, MarketRole, Participant = db.Party, db.MarketRole, db.Participant
Contract = db.Contract
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, contract, message=None):
    parties = sess.query(Party).join(MarketRole, Participant).filter(
        MarketRole.code == 'X').order_by(Participant.code).all()
    messages = None if message is None else [str(message)]
    return {'contract': contract, 'messages': messages, 'parties': parties}


sess = None
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
            contract.update(
                sess, False, name, party, charge_script, properties)
            sess.commit()
            inv.sendSeeOther(
                '/reports/77/output/?supplier_contract_id=' + str(contract.id))
except UserException, e:
    sess.rollback()
    if str(e).startswith("There isn't a contract"):
        inv.sendNotFound(str(e))
    else:
        render(inv, template, make_fields(sess, contract, e), 400)
finally:
    if sess is not None:
        sess.close()
