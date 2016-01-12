from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
Contract = db.Contract
inv, template = globals()['inv'], globals()['templater']

sess = None
try:
    sess = db.session()
    contract_id = inv.getLong('mop_contract_id')

    contract = Contract.get_mop_by_id(contract_id)
    templater.render(inv, template, {'contract': contract})
finally:
    if sess is not None:
        sess.close()
