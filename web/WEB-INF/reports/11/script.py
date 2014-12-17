import datetime
from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'templater', 'db')
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    site_id = inv.getLong("site_id")
    year = inv.getInteger("finish_year")
    month = inv.getInteger("finish_month")
    months = inv.getInteger("months")

    finish_date = datetime.datetime(year, month, 1)

    site = db.Site.get_by_id(sess, site_id)

    templater.render(
        inv, template, {
            'year': year, 'month': month, 'months': months, 'site': site,
            'finish_date': finish_date})
finally:
    if sess is not None:
        sess.close()
