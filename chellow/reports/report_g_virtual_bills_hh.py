import csv
import os
import sys
import threading
import traceback

from flask import g

from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true

import chellow.e.computer
from chellow.e.computer import contract_func
from chellow.gas.engine import GDataSource
from chellow.models import GEra, GSupply, Session, Site, SiteGEra
from chellow.utils import csv_make_val, hh_format, hh_range, req_date, req_int
from chellow.views import chellow_redirect


def content(g_supply_id, start_date, finish_date, user):
    caches = {}
    try:
        sess = Session()
        g_supply = GSupply.get_by_id(sess, g_supply_id)

        forecast_date = chellow.e.computer.forecast_date()

        prev_titles = None
        running_name, finished_name = chellow.dloads.make_names(
            f"g_supply_virtual_bills_hh_{g_supply_id}.csv", user
        )
        f = open(running_name, mode="w", newline="")
        w = csv.writer(f, lineterminator="\n")

        for hh_start in hh_range(caches, start_date, finish_date):
            g_era = (
                sess.query(GEra)
                .filter(
                    GEra.g_supply == g_supply,
                    GEra.start_date <= hh_start,
                    or_(GEra.finish_date == null(), GEra.finish_date >= hh_start),
                )
                .one()
            )

            site = (
                sess.query(Site)
                .join(SiteGEra)
                .filter(SiteGEra.g_era == g_era, SiteGEra.is_physical == true())
                .one()
            )

            ds = GDataSource(
                sess, hh_start, hh_start, forecast_date, g_era, caches, None
            )

            titles = ["MPRN", "Site Code", "Site Name", "Account", "HH Start", ""]

            output_line = [
                ds.mprn,
                site.code,
                site.name,
                ds.account,
                hh_format(ds.start_date),
                "",
            ]

            contract = g_era.g_contract
            output_line.append("")
            contract_titles = contract_func(caches, contract, "virtual_bill_titles")()
            titles.append("")
            titles.extend(contract_titles)

            contract_func(caches, contract, "virtual_bill")(ds)
            bill = ds.bill
            for title in contract_titles:
                output_line.append(csv_make_val(bill.get(title, "")))
                if title in bill:
                    del bill[title]

            for k in sorted(bill.keys()):
                output_line.extend([k, csv_make_val(bill[k])])

            if titles != prev_titles:
                prev_titles = titles
                w.writerow(titles)
            w.writerow(output_line)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        w.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    g_supply_id = req_int("g_supply_id")
    start_date = req_date("start")
    finish_date = req_date("finish")

    args = g_supply_id, start_date, finish_date, g.user
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
