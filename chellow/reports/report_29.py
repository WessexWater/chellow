from datetime import datetime as Datetime
import pytz
from dateutil.relativedelta import relativedelta
import traceback
from chellow.utils import send_response, req_int, HH, req_str
from chellow.models import Site


def content(start_date, finish_date, site_id, typ, sess):
    try:
        site = Site.get_by_id(sess, site_id)
        yield ','.join(
            ('Site Code', 'Type', 'Date') + tuple(map(str, range(1, 49))))
        for group in site.groups(sess, start_date, finish_date, True):
            for hh in group.hh_data(sess):
                hh_start = hh['start_date']
                if (hh_start.hour, hh_start.minute) == (0, 0):
                    yield '\r\n' + ','.join(
                        (site.code, typ, hh_start.strftime("%Y-%m-%d")))
                yield "," + str(hh[typ])
    except:
        yield traceback.format_exc()


def do_get(sess):
    months = req_int('months')
    finish_year = req_int('finish_year')
    finish_month = req_int('finish_month')

    finish_date = Datetime(finish_year, finish_month, 1, tzinfo=pytz.utc) + \
        relativedelta(months=1) - HH
    start_date = finish_date + HH - relativedelta(months=months)

    file_name = "site_hh_data_" + start_date.strftime("%Y%m%d%H%M") + ".csv"
    typ = req_str('type')
    site_id = req_int('site_id')
    return send_response(
        content, args=(start_date, finish_date, site_id, typ, sess),
        file_name=file_name)
