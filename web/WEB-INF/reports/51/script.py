from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Llfc', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    llfc_id = inv.getLong('llfc_id')
    llfc = Llfc.get_by_id(sess, llfc_id)
    dno_contract = Contract.get_dno_by_name(sess, llfc.dno.dno_code)
    render(inv, template, {'llfc': llfc, 'dno_contract': dno_contract})
finally:
    if sess is not None:
        sess.close()