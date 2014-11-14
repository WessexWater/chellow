from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'hh_importer')
render = templater.render

sess = None
try:
    sess = db.session()
    contract_id = inv.getLong('hhdc_contract_id')
    contract = db.Contract.get_hhdc_by_id(sess, contract_id)
    process_id = inv.getLong('process_id')
    process = hh_importer.get_hh_import_processes(contract_id)[process_id]

    render(inv, template, {'contract': contract, 'process': process})
finally:
    if sess is not None:
        sess.close()
