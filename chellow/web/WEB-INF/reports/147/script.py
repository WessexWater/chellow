from net.sf.chellow.monad import Monad
import datetime
from dateutil.relativedelta import relativedelta
import pytz
import db
import templater
import utils

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
HH = utils.HH
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    last_month = datetime.datetime.now(pytz.utc) - relativedelta(months=1)
    last_month_start = datetime.datetime(
        last_month.year, last_month.month, 1, tzinfo=pytz.utc)
    last_month_finish = last_month_start + relativedelta(months=1) - HH
    render(
        inv, template, {
            'last_month_start': last_month_start,
            'last_month_finish': last_month_finish})
finally:
    if sess is not None:
        sess.close()
