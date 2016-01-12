from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract = db.Contract
UserException = utils.UserException
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('dno_contract_id')
        contract = Contract.get_dno_by_id(sess, contract_id)
        render(inv, template, {'contract': contract})
    else:
        db.set_read_write(sess)
        contract_id = inv.getLong('dno_contract_id')
        contract = Contract.get_dno_by_id(sess, contract_id)
        name = inv.getString('name')
        charge_script = inv.getString('charge_script')
        contract.update(
            sess, True, name, contract.party, charge_script, '{}')
        sess.commit()
        inv.sendSeeOther(
            '/reports/67/output/?dno_contract_id=' + str(contract.id))
except UserException as e:
    render(inv, template, {'contract': contract, 'messages': [str(e)]})
finally:
    sess.close()
