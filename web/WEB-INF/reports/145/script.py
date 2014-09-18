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
    start_date = datetime(now.year, now.month, 1) - relativedelta(months=1)
    finish_date = datetime(now.year, now.month, 1) - HH

    render(inv, template, {'start_date': start_date, 'finish_date': finish_date})
finally:
    sess.close()