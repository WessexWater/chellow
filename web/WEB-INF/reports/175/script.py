import datetime
from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    now = datetime.datetime.utcnow()
    templater.render(inv, template, {'year': now.year - 1})
finally:
    if sess is not None:
        sess.close()
