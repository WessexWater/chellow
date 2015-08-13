from net.sf.chellow.monad import Monad
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import utils
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
HH = utils.HH
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    now = datetime.now(pytz.utc)
    month_start = datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = month_start + relativedelta(months=1) - HH

    templater.render(
        inv, template, {
            'month_start': month_start, 'month_finish': month_finish})

finally:
    if sess is not None:
        sess.close()
