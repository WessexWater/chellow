from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    contract_id = inv.getLong('non_core_contract_id')
    contract = Contract.get_non_core_by_id(sess, contract_id)
    rate_scripts = sess.query(RateScript).from_statement("select * from rate_script where rate_script.contract_id = :contract_id order by start_date desc").params(contract_id=contract_id).all()
    render(inv, template, {'contract': contract, 'rate_scripts': rate_scripts})
finally:
    sess.close()