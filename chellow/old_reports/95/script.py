from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Tpr = db.Tpr
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    tprs = sess.query(Tpr).order_by(Tpr.code).all()
    render(inv, template, {'tprs': tprs})
finally:
    sess.close()
