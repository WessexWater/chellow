from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Site', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

def make_fields(site, e=None):
    messages = None if e is None else [str(e)]
    finish_date = datetime.datetime(year, month, 1, tzinfo=pytz.utc)
        
    return {'site': site, 'finish_date': finish_date, 'messages': messages}


sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        site_id = inv.getLong("site_id")
        site = Site.get_by_id(sess, site_id)

        year = inv.getInteger("finish_year")
        month = inv.getInteger("finish_month")
        months = inv.getInteger("months")
        
        render(inv, template, make_fields(site))
    else:
        raise UserException("POST not allowed.")

except UserException, e:
    render(inv, template, make_fields(site, e))
finally:
    sess.close()