from net.sf.chellow.monad import Monad
from datetime import datetime
from dateutil.relativedelta import relativedelta
import db
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    init = datetime.utcnow()
    init = datetime(init.year, init.month, 1) - relativedelta(months=1)

    render(inv, template, {'init': init})

finally:
    if sess is not None:
        sess.close()
