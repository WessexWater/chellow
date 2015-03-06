from net.sf.chellow.monad import Monad
import StringIO
import sys
import os
import db
import utils
import templater
import hh_importer
Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'general_import', 'hh_importer')
Contract = db.Contract
UserException = utils.UserException
render = templater.render
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, contract, message=None):
    messages = None if message is None else [str(message)]
    return {
        'contract': contract,
        'processes': hh_importer.get_hh_import_processes(contract.id),
        'messages': messages}

sess = None
contract = None
try:
    sess = db.session()
    hh_importer_contract = Contract.get_non_core_by_name(sess, 'hh_importer')

    if inv.getRequest().getMethod() == 'GET':
        hhdc_contract_id = inv.getLong('hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)

        render(inv, template, make_fields(sess, contract))
    else:
        hhdc_contract_id = inv.getLong('hhdc_contract_id')
        contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)
        file_item = inv.getFileItem("import_file")
        f = StringIO.StringIO()
        if sys.platform.startswith('java'):
            from java.io import InputStreamReader

            stream = InputStreamReader(file_item.getInputStream(), 'utf-8')
            bt = stream.read()
            while bt != -1:
                f.write(unichr(bt))
                bt = stream.read()
            file_size = file_item.getSize()
        else:
            f.writelines(file_item.f.stream)
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
        f.seek(0)
        hh_import_process = hh_importer.start_hh_import_process(
            hhdc_contract_id, f, file_item.getName(), file_size)
        inv.sendSeeOther(
            "/reports/65/output/?hhdc_contract_id=" + str(contract.id) +
            "&process_id=" + str(hh_import_process.id))
except UserException, e:
    if contract is not None:
        render(inv, template, make_fields(sess, contract, e), 400)
    else:
        raise e
finally:
    if sess is not None:
        sess.close()
