import csv
import sys
import threading
import traceback

from flask import g, redirect

from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true

import chellow.e.computer
from chellow.dloads import open_file
from chellow.e.computer import contract_func
from chellow.gas.engine import GDataSource
from chellow.models import GEra, GSupply, Session, Site, SiteGEra
from chellow.utils import csv_make_val, hh_range, req_date, req_int


def content(g_supply_id, start_date, finish_date, user):
    caches = {}
    try:
        with Session() as sess:
            g_supply = GSupply.get_by_id(sess, g_supply_id)

            forecast_date = chellow.e.computer.forecast_date()

            prev_titles = None
            f = open_file(
                f"g_supply_virtual_bills_hh_{g_supply_id}.csv",
                user,
                mode="w",
                newline="",
            )
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
                contract = g_era.g_contract
                contract_titles = contract_func(
                    caches, contract, "virtual_bill_titles"
                )()

                titles = [
                    "mprn",
                    "site_code",
                    "site_name",
                    "account",
                    "hh_start",
                ] + contract_titles

                vals = {
                    "mprn": ds.mprn,
                    "site_code": site.code,
                    "site_name": site.name,
                    "account": ds.account,
                    "hh_start": ds.start_date,
                }

                contract_func(caches, contract, "virtual_bill")(ds)
                for k, v in ds.bill.items():
                    if k == "elements":
                        for elname, parts in v.items():
                            for part_name, part_val in parts.items():
                                vals[f"{elname}-{part_name}"] = part_val
                    else:
                        vals[k] = v

                if titles != prev_titles:
                    prev_titles = titles
                    w.writerow(titles)
                w.writerow([csv_make_val(vals.get(title)) for title in titles])
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        w.writerow([msg])
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    g_supply_id = req_int("g_supply_id")
    start_date = req_date("start")
    finish_date = req_date("finish")

    args = g_supply_id, start_date, finish_date, g.user
    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
