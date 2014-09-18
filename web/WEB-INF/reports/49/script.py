from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Llfc', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    dno_contract_id = inv.getLong('dno_contract_id')
    contract = Contract.get_dno_by_id(sess, dno_contract_id)
    llfcs = sess.query(Llfc).from_statement("select * from llfc where dno_id = :dno_id order by code").params(dno_id=contract.party.id).all()
    render(inv, template, {'llfcs': llfcs, 'contract': contract})
finally:
    sess.close()