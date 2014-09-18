from net.sf.chellow.monad import Monad
from java.io import InputStreamReader
import StringIO

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'session', 'Batch', 'set_read_write'],
        'utils': ['UserException', 'prev_hh', 'next_hh', 'hh_after', 'hh_before', 'HH'],
        'templater': ['render'],
        'general_import': ['start_general_process', 'get_general_process_ids', 'get_general_process'],
        'hh_importer': ['start_hh_import_process', 'get_hh_import_processes']})


def make_fields(sess, contract, message=None):
    messages = None if message is None else [str(message)]
    return {'contract': contract, 'processes': get_hh_import_processes(contract.id), 'messages': messages}

sess = None
try:
    sess = session()
    hh_importer_contract = Contract.get_non_core_by_name(sess, 'hh_importer')

    if inv.getRequest().getMethod() == 'GET':
        hhdc_contract_id = inv.getLong('hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)

        render(inv, template, make_fields(sess, contract))
    else:
        hhdc_contract_id = inv.getLong('hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)
        file_item = inv.getFileItem("import_file")
        stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
        f = StringIO.StringIO()
        bt = stream.read()
        while bt != -1:
            f.write(unichr(bt))
            bt = stream.read()
        f.seek(0)
        hh_import_process = start_hh_import_process(hhdc_contract_id, f, file_item.getName(), file_item.getSize())
        inv.sendSeeOther("/reports/65/output/?hhdc_contract_id=" + str(contract.id) + "&process_id=" + str(hh_import_process.id))
except UserException, e:
    render(inv, template, make_fields(sess, contract, e), 400)
finally:
    if sess is not None:
        sess.close()