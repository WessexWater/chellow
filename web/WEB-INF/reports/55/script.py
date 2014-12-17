from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    pc_id = inv.getLong('pc_id')
    pc = db.Pc.get_by_id(sess, pc_id)
    templater.render(inv, template, {'pc': pc})
finally:
    if sess is not None:
        sess.close()
