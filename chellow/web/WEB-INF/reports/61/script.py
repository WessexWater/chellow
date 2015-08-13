from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
Mtc, Party, Contract = db.Mtc, db.Party, db.Contract
inv, template = globals()['inv'], globals()['template']
sess = None
try:
    sess = db.session()
    mtcs = sess.query(Mtc, Contract).outerjoin(Mtc.dno) \
        .outerjoin(Contract).order_by(Mtc.code, Party.dno_code).all()
    templater.render(inv, template, {'mtcs': mtcs})
finally:
    if sess is not None:
        sess.close()
