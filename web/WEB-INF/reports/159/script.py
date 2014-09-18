from net.sf.chellow.monad import Monad
from datetime import datetime
from dateutil.relativedelta import relativedelta

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException', 'HH'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = datetime(now.year, now.month, 1) - HH

    render(inv, template, {'month_start': month_start, 'month_finish': month_finish})
finally:
    sess.close()