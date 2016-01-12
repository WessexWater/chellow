from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Ssc = db.Ssc
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    ssc_id = inv.getLong('ssc_id')
    ssc = Ssc.get_by_id(sess, ssc_id)
    render(inv, template, {'ssc': ssc})
finally:
    if sess is not None:
        sess.close()
