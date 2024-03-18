import csv
import threading
import traceback
from datetime import datetime as Datetime

from dateutil.relativedelta import relativedelta

from flask import g

import pytz

from sqlalchemy.sql.expression import null, or_, true

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.e.computer import SupplySource, contract_func, forecast_date
from chellow.models import Era, Session, Site, SiteEra, Supply, User
from chellow.utils import HH, csv_make_val, hh_format, hh_max, hh_min, req_bool, req_int
from chellow.views import chellow_redirect


def content(
    start_year,
    start_month,
    start_day,
    finish_year,
    finish_month,
    finish_day,
    is_import,
    supply_id,
    user_id,
):
    caches = {}
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("daily_supplier_virtual_bill.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            start_date = Datetime(start_year, start_month, start_day, tzinfo=pytz.utc)
            finish_date = (
                Datetime(finish_year, finish_month, finish_day, tzinfo=pytz.utc)
                + relativedelta(days=1)
                - HH
            )

            supply = Supply.get_by_id(sess, supply_id)
            fd = forecast_date()
            day_start = start_date
            header_titles = [
                "MPAN Core",
                "Site Code",
                "Site Name",
                "Account",
                "From",
                "To",
                "Is Forecast?",
            ]

            bill_titles = []
            # Find titles
            for era in sess.query(Era).filter(
                Era.supply == supply,
                Era.start_date <= finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
            ):
                if is_import:
                    cont = era.imp_supplier_contract
                else:
                    cont = era.exp_supplier_contract

                for title in contract_func(caches, cont, "virtual_bill_titles")():
                    if title not in bill_titles:
                        bill_titles.append(title)

                ssc = era.ssc
                if ssc is not None:
                    for mr in ssc.measurement_requirements:
                        for suffix in ("-kwh", "-rate", "-gbp"):
                            title = mr.tpr.code + suffix
                            if title not in bill_titles:
                                bill_titles.append(title)

            writer.writerow(header_titles + bill_titles)

            while not day_start > finish_date:
                day_finish = day_start + relativedelta(days=1) - HH

                for era in supply.find_eras(sess, day_start, day_finish):
                    chunk_start = hh_max(era.start_date, day_start)
                    chunk_finish = hh_min(era.finish_date, day_finish)

                    ss = SupplySource(
                        sess,
                        chunk_start,
                        chunk_finish,
                        fd,
                        era,
                        is_import,
                        caches,
                    )

                    site = (
                        sess.query(Site)
                        .join(SiteEra)
                        .filter(SiteEra.era == era, SiteEra.is_physical == true())
                        .one()
                    )
                    row = [
                        ss.mpan_core,
                        site.code,
                        site.name,
                        ss.supplier_account,
                        hh_format(ss.start_date),
                        hh_format(ss.finish_date),
                        ss.years_back > 0,
                    ]

                    contract_func(caches, ss.supplier_contract, "virtual_bill")(ss)
                    bill = ss.supplier_bill
                    for title in bill_titles:
                        if title in bill:
                            row.append(csv_make_val(bill[title]))
                            del bill[title]
                        else:
                            row.append("")

                    for k in sorted(bill.keys()):
                        row.append(k)
                        row.append(csv_make_val(bill[k]))
                    writer.writerow(row)

                day_start += relativedelta(days=1)
    except BadRequest as e:
        writer.writerow(["Problem: " + e.description])
    except BaseException:
        writer.writerow([traceback.format_exc()])
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    start_year = req_int("start_year")
    start_month = req_int("start_month")
    start_day = req_int("start_day")

    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    finish_day = req_int("finish_day")

    is_import = req_bool("is_import")
    supply_id = req_int("supply_id")

    args = (
        start_year,
        start_month,
        start_day,
        finish_year,
        finish_month,
        finish_day,
        is_import,
        supply_id,
        g.user.id,
    )
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
