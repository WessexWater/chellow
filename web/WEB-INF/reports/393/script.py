from net.sf.chellow.monad import Monad
from datetime import datetime
from dateutil.relativedelta import relativedelta
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
inv, template = globals()['inv'], globals()['template']
HH = utils.HH

sess = None
try:
    sess = db.session()
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = datetime(now.year, now.month, 1) - HH

    render(
        inv, template, {
            'month_start': month_start, 'month_finish': month_finish})
finally:
    if sess is not None:
        sess.close()
