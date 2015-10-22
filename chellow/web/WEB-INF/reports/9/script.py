from net.sf.chellow.monad import Monad
import datetime
import pytz
import templater
import db
import utils

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
UserException = utils.UserException
Site = db.Site

inv, template = globals()['inv'], globals()['template']


def make_fields(site, e=None):
    messages = None if e is None else [str(e)]
    finish_date = datetime.datetime(year, month, 1, tzinfo=pytz.utc)

    return {'site': site, 'finish_date': finish_date, 'messages': messages}


sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        site_id = inv.getLong("site_id")
        site = Site.get_by_id(sess, site_id)

        year = inv.getInteger("finish_year")
        month = inv.getInteger("finish_month")
        months = inv.getInteger("months")

        render(inv, template, make_fields(site))
    else:
        raise UserException("POST not allowed.")

except UserException as e:
    render(inv, template, make_fields(site, e))
finally:
    sess.close()
