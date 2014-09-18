from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render'],
        'hh_importer': ['get_hh_import_processes']})

sess = None
try:
    sess = session()
    contract_id = inv.getLong('hhdc_contract_id')
    contract = Contract.get_hhdc_by_id(sess, contract_id)
    process_id = inv.getLong('process_id')
    process = get_hh_import_processes(contract_id)[process_id]

    render(inv, template, {'contract': contract, 'process': process})
finally:
    if sess is not None:
        sess.close()