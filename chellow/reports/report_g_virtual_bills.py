import csv
import sys
import threading
import traceback


from flask import g

from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.e.computer import contract_func, forecast_date
from chellow.gas.engine import GDataSource
from chellow.models import GContract, GEra, Session, Site, SiteGEra, User
from chellow.utils import (
    c_months_u,
    hh_format,
    hh_max,
    hh_min,
    make_val,
    req_date,
    req_int,
    to_ct,
)
from chellow.views import chellow_redirect


def content(start_date, finish_date, g_contract_id, user_id):
    report_context = {}
    f = writer = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("gas_virtual_bills.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")

            g_contract = GContract.get_by_id(sess, g_contract_id)
            forecast_dt = forecast_date()

            start_date_ct, finish_date_ct = to_ct(start_date), to_ct(finish_date)

            month_pairs = c_months_u(
                start_year=start_date_ct.year,
                start_month=start_date_ct.month,
                finish_year=finish_date_ct.year,
                finish_month=finish_date_ct.month,
            )

            bill_titles = contract_func(
                report_context, g_contract, "virtual_bill_titles"
            )()
            writer.writerow(
                ["MPRN", "Site Code", "Site Name", "Account", "From", "To"]
                + bill_titles
            )

            for month_start, month_finish in month_pairs:
                period_start = hh_max(start_date, month_start)
                period_finish = hh_min(finish_date, month_finish)

                for g_era in (
                    sess.query(GEra)
                    .distinct()
                    .filter(
                        GEra.g_contract == g_contract,
                        GEra.start_date <= period_finish,
                        or_(
                            GEra.finish_date == null(), GEra.finish_date >= period_start
                        ),
                    )
                ):
                    chunk_start = hh_max(g_era.start_date, period_start)
                    chunk_finish = hh_min(g_era.finish_date, period_finish)

                    data_source = GDataSource(
                        sess,
                        chunk_start,
                        chunk_finish,
                        forecast_dt,
                        g_era,
                        report_context,
                        None,
                    )

                    site = (
                        sess.query(Site)
                        .join(SiteGEra)
                        .filter(SiteGEra.g_era == g_era, SiteGEra.is_physical == true())
                        .one()
                    )

                    vals = [
                        data_source.mprn,
                        site.code,
                        site.name,
                        data_source.account,
                        hh_format(data_source.start_date),
                        hh_format(data_source.finish_date),
                    ]

                    contract_func(report_context, g_contract, "virtual_bill")(
                        data_source
                    )
                    bill = data_source.bill
                    for title in bill_titles:
                        if title in bill:
                            val = make_val(bill[title])
                            del bill[title]
                        else:
                            val = ""
                        vals.append(val)

                    for k in sorted(bill.keys()):
                        vals.append(k)
                        vals.append(str(bill[k]))
                    writer.writerow(vals)

    except BadRequest as e:
        writer.writerow(["Problem: " + e.description])
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        if writer is not None:
            writer.writerow([msg])
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    start_date = req_date("start")
    finish_date = req_date("finish")
    g_contract_id = req_int("g_contract_id")

    args = start_date, finish_date, g_contract_id, g.user.id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
