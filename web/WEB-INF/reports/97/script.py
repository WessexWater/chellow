from net.sf.chellow.monad import Monad
import templater
import db

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Tpr = db.Tpr
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    tpr_id = inv.getLong('tpr_id')
    tpr = Tpr.get_by_id(sess, tpr_id)
    render(inv, template, {'tpr': tpr})
finally:
    if sess is not None:
        sess.close()
