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
        contract_id = inv.getLong('non_core_contract_id')
        contract = Contract.get_non_core_by_id(sess, contract_id)
        render(inv, template, {'contract': contract})
    else:
        set_read_write(sess)
        contract_id = inv.getLong('non_core_contract_id')
        contract = Contract.get_non_core_by_id(sess, contract_id)
        if inv.hasParameter('delete'):
            contract.delete(sess)
            sess.commit()
            inv.sendSeeOther('/reports/259/output/')
        else:
            name = inv.getString('name')
            charge_script = inv.getString('charge_script')
            properties = inv.getString('properties')
            contract.update(sess, contract.is_core, name, contract.party,
                    charge_script, properties)
            sess.commit()
            inv.sendSeeOther('/reports/267/output/?non_core_contract_id='
                + str(contract.id))
except UserException, e:
    render(inv, template, {'contract': contract, 'messages': [str(e)]})
finally:
    sess.close()