from net.sf.chellow.monad import Monad
import db
import templater
import datetime
from dateutil.relativedelta import relativedelta
import utils
import pytz

Monad.getUtils()['impt'](globals(), 'templater', 'db', 'utils')
inv, template = globals()['inv'], globals()['template']

HH = utils.HH

sess = None
try:
    sess = db.session()
    config = db.Contract.get_non_core_by_name(sess, 'configuration')
    now = datetime.datetime.now(pytz.utc)
    month_start = datetime.datetime(now.year, now.month, 1) - \
        relativedelta(months=1)
    month_finish = datetime.datetime(now.year, now.month, 1) - HH

    templater.render(
        inv, template, {
            'properties': config.make_properties(), 'month_start': month_start,
            'month_finish': month_finish})
finally:
    if sess is not None:
        sess.close()
