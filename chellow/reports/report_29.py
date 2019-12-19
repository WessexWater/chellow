import traceback
from chellow.utils import req_int, req_str, to_ct, c_months_u
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
            "site_hh_data_" + to_ct(start_date).strftime("%Y%m%d%H%M") +
            ".csv", user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(
            ('Site Code', 'Type', 'HH Start Clock-Time') +
            tuple(map(str, range(1, 49))))
        site = Site.get_by_id(sess, site_id)
        line = None
        for hh in site.hh_data(sess, start_date, finish_date):
            hh_start_ct = to_ct(hh['start_date'])
            if (hh_start_ct.hour, hh_start_ct.minute) == (0, 0):
                if line is not None:
                    writer.writerow(line)
                line = [site.code, typ, hh_start_ct.strftime("%Y-%m-%d")]
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

    month_list = list(
        c_months_u(
            finish_year=finish_year, finish_month=finish_month, months=months))
    start_date, finish_date = month_list[0][0], month_list[-1][-1]

    typ = req_str('type')
    site_id = req_int('site_id')
    args = (start_date, finish_date, site_id, typ, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
