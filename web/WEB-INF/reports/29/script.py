from net.sf.chellow.monad import Monad
import datetime
import pytz
from dateutil.relativedelta import relativedelta
import traceback

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
form_int, form_str, HH = utils.form_int, utils.form_str, utils.HH
UserException = utils.UserException

months = form_int(inv, 'months')
finish_year = form_int(inv, 'finish_year')
finish_month = form_int(inv, 'finish_month')

finish_date = datetime.datetime(
    finish_year, finish_month, 1, tzinfo=pytz.utc) + \
    relativedelta(months=1) - HH
start_date = finish_date + HH - relativedelta(months=months)

file_name = "site_hh_data_" + start_date.strftime("%Y%m%d%H%M") + ".csv"
method = inv.getRequest().getMethod()
typ = form_str(inv, 'type')
site_id = form_int(inv, 'site_id')


def content():
    sess = None
    try:
        sess = db.session()
        if method == 'GET':
            site = db.Site.get_by_id(sess, site_id)
            yield ','.join(
                ('Site Code', 'Type', 'Date') + tuple(map(str, range(1, 49))))
            for group in site.groups(sess, start_date, finish_date, True):
                for hh in group.hh_data(sess):
                    hh_start = hh['start_date']
                    if (hh_start.hour, hh_start.minute) == (0, 0):
                        yield '\r\n' + ','.join(
                            (site.code, typ, hh_start.strftime("%Y-%m-%d")))
                    yield "," + str(hh[typ])
        else:
            raise UserException("Only GET method is supported.")
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name=file_name)
