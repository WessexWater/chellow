from net.sf.chellow.monad import Monad
from java.util import Properties
from java.io import StringReader
from net.sf.chellow.physical import Configuration
from net.sf.chellow.ui import Report
from sqlalchemy.orm import joinedload_all
import datetime
from dateutil.relativedelta import relativedelta
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException', 'HH'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    last_month = datetime.datetime.now(pytz.utc) - relativedelta(months=1)
    last_month_start = datetime.datetime(last_month.year, last_month.month, 1, tzinfo=pytz.utc)
    last_month_finish = last_month_start + relativedelta(months=1) - HH
    render(inv, template, {'last_month_start': last_month_start, 'last_month_finish': last_month_finish})
finally:
    if sess is not None:
        sess.close()