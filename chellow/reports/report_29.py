import csv
import sys
import threading
import traceback

from flask import g

from chellow.dloads import open_file
from chellow.models import Session, Site, User
from chellow.utils import c_months_u, csv_make_val, req_int, req_str, to_ct
from chellow.views import chellow_redirect


def _write_row(writer, total, values, titles):
    values["total"] = total
    writer.writerow([csv_make_val(values[t]) for t in titles])


def content(start_date, finish_date, site_id, typ, user_id):
    f = writer = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file(
                f'site_hh_data_{to_ct(start_date).strftime("%Y%m%d%H%M")}.csv',
                user,
                mode="w",
                newline="",
            )
            writer = csv.writer(f, lineterminator="\n")
            titles = ["site_code", "type", "hh_start_clock_time", "total"]
            hr_titles = tuple(map(str, range(1, 51)))
            titles.extend(hr_titles)
            writer.writerow(titles)
            site = Site.get_by_id(sess, site_id)

            vals = total = hh_num = None
            for hh in site.hh_data(sess, start_date, finish_date):
                hh_start_ct = to_ct(hh["start_date"])
                if (hh_start_ct.hour, hh_start_ct.minute) == (0, 0):
                    if vals is not None:
                        _write_row(writer, total, vals, titles)
                    vals = {
                        "site_code": site.code,
                        "type": typ,
                        "hh_start_clock_time": hh_start_ct.strftime("%Y-%m-%d"),
                    }
                    for t in hr_titles:
                        vals[t] = None
                    total = 0
                    hh_num = 1
                val = hh[typ]
                vals[str(hh_num)] = val
                hh_num += 1
                total += val
            if vals is not None:
                _write_row(writer, total, vals, titles)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    months = req_int("months")
    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")

    month_list = list(
        c_months_u(finish_year=finish_year, finish_month=finish_month, months=months)
    )
    start_date, finish_date = month_list[0][0], month_list[-1][-1]

    typ = req_str("type")
    site_id = req_int("site_id")
    args = start_date, finish_date, site_id, typ, g.user.id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
