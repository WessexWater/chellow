import csv
import os
import sys
import threading
import traceback

from dateutil.relativedelta import relativedelta

from flask import g

from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true

from werkzeug.exceptions import BadRequest

import chellow.dloads
from chellow.computer import contract_func, forecast_date
from chellow.g_engine import GDataSource
from chellow.models import GContract, GEra, Session, Site, SiteGEra
from chellow.utils import (
    HH,
    hh_format,
    hh_max,
    hh_min,
    make_val,
    req_date,
    req_int,
    utc_datetime,
)
from chellow.views.home import chellow_redirect


def content(start_date, finish_date, g_contract_id, user):
    report_context = {}
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            "gas_virtual_bills.csv", user
        )
        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")

        g_contract = GContract.get_by_id(sess, g_contract_id)
        forecast_dt = forecast_date()

        month_start = utc_datetime(start_date.year, start_date.month, 1)
        month_finish = month_start + relativedelta(months=1) - HH

        bill_titles = contract_func(report_context, g_contract, "virtual_bill_titles")()
        writer.writerow(
            ["MPRN", "Site Code", "Site Name", "Account", "From", "To"] + bill_titles
        )

        while not month_start > finish_date:
            period_start = hh_max(start_date, month_start)
            period_finish = hh_min(finish_date, month_finish)

            for g_era in (
                sess.query(GEra)
                .distinct()
                .filter(
                    GEra.g_contract == g_contract,
                    GEra.start_date <= period_finish,
                    or_(GEra.finish_date == null(), GEra.finish_date >= period_start),
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

                contract_func(report_context, g_contract, "virtual_bill")(data_source)
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

            month_start += relativedelta(months=1)
            month_finish = month_start + relativedelta(months=1) - HH
    except BadRequest as e:
        writer.writerow(["Problem: " + e.description])
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
    start_date = req_date("start")
    finish_date = req_date("finish")
    g_contract_id = req_int("g_contract_id")

    threading.Thread(
        target=content, args=(start_date, finish_date, g_contract_id, g.user)
    ).start()
    return chellow_redirect("/downloads", 303)
