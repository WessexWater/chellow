from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
Mtc, Contract = db.Mtc, db.Contract
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    mtc_id = inv.getLong('mtc_id')
    mtc, dno_contract = sess.query(Mtc, Contract).outerjoin(Mtc.dno) \
        .outerjoin(Contract).filter(Mtc.id == mtc_id).one()
    templater.render(inv, template, {'mtc': mtc, 'dno_contract': dno_contract})
finally:
    if sess is not None:
        sess.close()
