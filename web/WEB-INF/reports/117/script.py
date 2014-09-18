from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
import datetime
import pytz
from dateutil.relativedelta import relativedelta
from java.lang import System

Monad.getUtils()['imprt'](globals(), {
        'db': ['Channel', 'Era', 'HhDatum', 'Snag', 'set_read_write', 'session'], 
        'utils': ['UserException', 'HH', 'hh_after'],
        'templater': ['render']})

def make_fields(sess, snag, message=None):
    messages = [] if message is None else [str(message)]
    return {'messages': messages, 'snag': snag}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        snag_id = inv.getLong('snag_id')
        snag = Snag.get_by_id(sess, snag_id)
        render(inv, template, make_fields(sess, snag))
except UserException, e:
    render(inv, template, make_fields(sess, snag, e), 400)
finally:
    sess.close()