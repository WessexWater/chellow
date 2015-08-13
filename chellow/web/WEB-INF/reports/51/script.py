from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Llfc, Contract = db.Llfc, db.Contract
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    llfc_id = inv.getLong('llfc_id')
    llfc = Llfc.get_by_id(sess, llfc_id)
    dno_contract = Contract.get_dno_by_name(sess, llfc.dno.dno_code)
    render(inv, template, {'llfc': llfc, 'dno_contract': dno_contract})
finally:
    if sess is not None:
        sess.close()
