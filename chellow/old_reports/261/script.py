from net.sf.chellow.monad import Monad
import db
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
UserRole = db.UserRole
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    user_roles = sess.query(UserRole).order_by(UserRole.code)
    render(inv, template, {'user_roles': user_roles})
finally:
    if sess is not None:
        sess.close()
