from net.sf.chellow.monad import Monad
import datetime
import pytz
from dateutil.relativedelta import relativedelta
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    now = datetime.datetime.now(pytz.utc)
    templater.render(
        inv, template, {
            'last_month': datetime.datetime(
                now.year, now.month, 1, tzinfo=pytz.utc) -
            relativedelta(months=1)})
finally:
    if sess is not None:
        sess.close()
