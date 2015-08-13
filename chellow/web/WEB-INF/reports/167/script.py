from net.sf.chellow.monad import Monad
from datetime import datetime
from dateutil.relativedelta import relativedelta
import db
import utils
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
HH = utils.HH
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    now = datetime.utcnow()
    start_date = datetime(now.year, now.month, 1) - relativedelta(months=1)
    finish_date = datetime(now.year, now.month, 1) - HH

    render(
        inv, template, {'start_date': start_date, 'finish_date': finish_date})
finally:
    if sess is not None:
        sess.close()
