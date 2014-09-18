from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'UserRole', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    user_roles = sess.query(UserRole).order_by(UserRole.code)
    render(inv, template, {'user_roles': user_roles})
finally:
    sess.close()