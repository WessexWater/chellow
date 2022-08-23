import csv
import os
import sys
import threading
import traceback

from flask import g

from sqlalchemy import or_, select
from sqlalchemy.sql.expression import null, true

import chellow.dloads
from chellow.e.computer import SupplySource, forecast_date
from chellow.models import Era, Session, Site, SiteEra, Supply
from chellow.utils import (
    csv_make_val,
    hh_format,
    hh_range,
    req_date,
    req_int,
)
from chellow.views import chellow_redirect


def content(supply_id, start_date, finish_date, user):
    caches = {}
    f = sess = None
    try:
        sess = Session()
        supply = Supply.get_by_id(sess, supply_id)

        f_date = forecast_date()

        running_name, finished_name = chellow.dloads.make_names(
            f"supply_virtual_bills_hh_{supply_id}.csv", user
        )
        f = open(running_name, mode="w", newline="")
        w = csv.writer(f, lineterminator="\n")

        mop_titles = []
        dc_titles = []
        imp_supplier_titles = []
        exp_supplier_titles = []

        for era in sess.execute(
            select(Era).where(
                Era.supply == supply,
                Era.start_date <= finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
            )
        ).scalars():

            ds = SupplySource(
                sess, era.start_date, era.start_date, f_date, era, True, caches
            )

            for t in ds.contract_func(era.mop_contract, "virtual_bill_titles")():
                if t not in mop_titles:
                    mop_titles.append(t)

            for t in ds.contract_func(era.dc_contract, "virtual_bill_titles")():
                if t not in dc_titles:
                    dc_titles.append(t)

            if era.imp_supplier_contract is not None:
                for t in ds.contract_func(
                    era.imp_supplier_contract, "virtual_bill_titles"
                )():
                    if t not in imp_supplier_titles:
                        imp_supplier_titles.append(t)

            if era.exp_supplier_contract is not None:
                ds = SupplySource(
                    sess,
                    era.start_date,
                    era.start_date,
                    f_date,
                    era,
                    False,
                    caches,
                )
                for t in ds.contract_func(
                    era.exp_supplier_contract, "virtual_bill_titles"
                )():
                    if t not in exp_supplier_titles:
                        exp_supplier_titles.append(t)

        titles = [
            "mpan_core",
            "site_code",
            "site_name",
            "hh_start",
        ]
        for pref, t in (
            ("mop", mop_titles),
            ("dc", dc_titles),
            ("imp_supplier", imp_supplier_titles),
            ("exp_supplier", exp_supplier_titles),
        ):
            titles.append("")
            titles.extend([f"{pref}_{n}" for n in t])

        w.writerow(titles)

        for hh_start in hh_range(caches, start_date, finish_date):
            era = sess.execute(
                select(Era).where(
                    Era.supply == supply,
                    Era.start_date <= hh_start,
                    or_(Era.finish_date == null(), Era.finish_date >= hh_start),
                )
            ).scalar_one()

            site = sess.execute(
                select(Site)
                .join(SiteEra)
                .where(SiteEra.era == era, SiteEra.is_physical == true())
            ).scalar_one()

            ds = SupplySource(sess, hh_start, hh_start, f_date, era, True, caches)

            vals = {
                "mpan_core": ds.mpan_core,
                "site_code": site.code,
                "site_name": site.name,
                "hh_start": hh_format(ds.start_date),
            }

            ds.contract_func(era.mop_contract, "virtual_bill")(ds)
            for k, v in ds.mop_bill.items():
                vals[f"mop_{k}"] = v

            ds.contract_func(era.dc_contract, "virtual_bill")(ds)
            for k, v in ds.dc_bill.items():
                vals[f"dc_{k}"] = v

            if era.imp_supplier_contract is not None:
                ds.contract_func(era.imp_supplier_contract, "virtual_bill")(ds)
                for k, v in ds.supplier_bill.items():
                    vals[f"imp_supplier_{k}"] = v

            if era.exp_supplier_contract is not None:
                ds = SupplySource(sess, hh_start, hh_start, f_date, era, False, caches)
                ds.contract_func(era.exp_supplier_contract, "virtual_bill")(ds)
                for k, v in ds.supplier_bill.items():
                    vals[f"exp_supplier_{k}"] = v

            w.writerow([csv_make_val(vals.get(t)) for t in titles])
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        if f is not None:
            f.write(msg)
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    supply_id = req_int("supply_id")
    start_date = req_date("start")
    finish_date = req_date("finish")

    args = supply_id, start_date, finish_date, g.user
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
