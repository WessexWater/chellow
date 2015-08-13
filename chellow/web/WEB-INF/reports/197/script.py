from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    cop_id = inv.getLong('cop_id')
    cop = db.Cop.get_by_id(sess, cop_id)
    templater.render(inv, template, {'cop': cop})
finally:
    if sess is not None:
        sess.close()
