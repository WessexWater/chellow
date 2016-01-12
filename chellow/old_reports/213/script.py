from net.sf.chellow.monad import Monad
import db
import hh_importer
import templater
import utils

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'hh_importer')
Contract = db.Contract
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']


def make_fields(contract, task, message=None):
    messages = None if message is None else [str(message)]
    return {'task': task, 'messages': messages, 'contract': contract}

sess = None
task = None
try:
    sess = db.session()
    contract_id = inv.getLong('hhdc_contract_id')
    contract = Contract.get_hhdc_by_id(sess, contract_id)

    if inv.getRequest().getMethod() == 'GET':
        task = hh_importer.get_hh_import_task(contract)
        render(inv, template, make_fields(contract, task))
    else:
        task = hh_importer.get_hh_import_task(contract)
        task.go()
        inv.sendSeeOther(
            "/reports/213/output/?hhdc_contract_id=" + str(contract.id))
except UserException as e:
    render(inv, template, make_fields(contract, task, e), 400)
finally:
    if sess is not None:
        sess.close()
