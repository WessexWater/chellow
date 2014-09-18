from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

sess = None
try:
    sess = db.session()
    utils.clog("hello")
    templater.render(inv, template, {'clogs': utils.clogs})
finally:
    if sess is not None:
        sess.close()