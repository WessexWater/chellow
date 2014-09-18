from net.sf.chellow.monad import Monad
from datetime import datetime
from dateutil.relativedelta import relativedelta

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    init = datetime.utcnow()
    init = datetime(init.year, init.month, 1) - relativedelta(months=1)

    render(inv, template, {'init': init})

finally:
    sess.close()