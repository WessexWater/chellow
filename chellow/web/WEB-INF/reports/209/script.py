from net.sf.chellow.monad import Monad
import db
import templater
import datetime
from dateutil.relativedelta import relativedelta
import pytz

Monad.getUtils()['impt'](globals(), 'templater', 'db')
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    start_date = datetime.datetime.now(pytz.utc)
    if start_date.month < 3:
        start_date = start_date - relativedelta(years=1)
    templater.render(inv, template, {'start_date': start_date})
finally:
    if sess is not None:
        sess.close()
