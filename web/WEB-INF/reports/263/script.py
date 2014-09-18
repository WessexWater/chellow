from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'UserRole', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    user_role_id = inv.getLong('user_role_id')
    user_role = UserRole.get_by_id(sess, user_role_id)
    render(inv, template, {'user_role': user_role})
finally:
    sess.close()