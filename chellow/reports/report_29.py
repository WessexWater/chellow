from datetime import datetime as Datetime
import pytz
from dateutil.relativedelta import relativedelta
import traceback
from chellow.utils import req_int, HH, req_str
from chellow.models import Site, Session
import chellow.dloads
import csv
from flask import g
import threading
import sys
import os
from chellow.views import chellow_redirect


def content(start_date, finish_date, site_id, typ, user):
    sess = f = writer = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            "site_hh_data_" + start_date.strftime("%Y%m%d%H%M") + ".csv", user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(
            ('Site Code', 'Type', 'Date') + tuple(map(str, range(1, 49))))
        site = Site.get_by_id(sess, site_id)
        line = None
        for hh in site.hh_data(sess, start_date, finish_date):
            hh_start = hh['start_date']
            if (hh_start.hour, hh_start.minute) == (0, 0):
                if line is not None:
                    writer.writerow(line)
                line = [site.code, typ, hh_start.strftime("%Y-%m-%d")]
            line.append(str(hh[typ]))
        if line is not None:
            writer.writerow(line)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    months = req_int('months')
    finish_year = req_int('finish_year')
    finish_month = req_int('finish_month')

    finish_date = Datetime(finish_year, finish_month, 1, tzinfo=pytz.utc) + \
        relativedelta(months=1) - HH
    start_date = finish_date + HH - relativedelta(months=months)

    typ = req_str('type')
    site_id = req_int('site_id')
    args = (start_date, finish_date, site_id, typ, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
