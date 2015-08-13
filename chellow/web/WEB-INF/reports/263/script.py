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
    user_role_id = inv.getLong('user_role_id')
    user_role = UserRole.get_by_id(sess, user_role_id)
    render(inv, template, {'user_role': user_role})
finally:
    sess.close()
