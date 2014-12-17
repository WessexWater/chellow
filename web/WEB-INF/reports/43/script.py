from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
GspGroup = db.GspGroup
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    groups = sess.query(GspGroup).order_by(GspGroup.code).all()
    templater.render(inv, template, {'groups': groups})
finally:
    if sess is not None:
        sess.close()
