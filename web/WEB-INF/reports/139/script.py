from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('dno_contract_id')
        contract = Contract.get_dno_by_id(sess, contract_id)
        render(inv, template, {'contract': contract})
    else:
        set_read_write(sess)
        contract_id = inv.getLong('dno_contract_id')
        contract = Contract.get_dno_by_id(sess, contract_id)
        name = inv.getString('name')
        charge_script = inv.getString('charge_script')
        contract.update(sess, True, name, contract.party,
                    charge_script, '{}')
        sess.commit()
        inv.sendSeeOther('/reports/67/output/?dno_contract_id='
                + str(contract.id))
except UserException, e:
    render(inv, template, {'contract': contract, 'messages': [str(e)]})
finally:
    sess.close()