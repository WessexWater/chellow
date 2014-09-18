from net.sf.chellow.monad import Monad
import threading

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'set_read_write'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH'],
        'templater': ['render'],
        'hh_importer': ['get_hh_import_task']})

def make_fields(contract, task, message=None):
    messages = None if message is None else [str(message)]
    return {'task': task, 'messages': messages, 'contract': contract}

sess = None
task = None
try:
    sess = session()
    contract_id = inv.getLong('hhdc_contract_id')
    contract = Contract.get_hhdc_by_id(sess, contract_id)

    if inv.getRequest().getMethod() == 'GET':
        task = get_hh_import_task(contract)   
        render(inv, template, make_fields(contract, task))
    else:
        task = get_hh_import_task(contract)
        task.go()
        inv.sendSeeOther("/reports/213/output/?hhdc_contract_id=" + str(contract.id))
except UserException, e:
    render(inv, template, make_fields(contract, task, e), 400)
finally:
    if sess is not None:
        sess.close()