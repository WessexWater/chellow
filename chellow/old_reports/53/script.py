from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
Pc = db.Pc
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    pcs = sess.query(Pc).order_by(Pc.code)
    templater.render(inv, template, {'pcs': pcs})
finally:
    if sess is not None:
        sess.close()
