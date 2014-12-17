from net.sf.chellow.monad import Monad
import db
import templater
import datetime
from dateutil.relativedelta import relativedelta
Monad.getUtils()['impt'](globals(), 'templater', 'db')
inv, template = globals()['inv'], globals()['templater']

sess = None
try:
    sess = db.session()
    now = datetime.datetime.utcnow()
    if now.month < 3:
        now += relativedelta(year=1)
    templater.render(inv, template, {'year': now.year})
finally:
    if sess is not None:
        sess.close()
