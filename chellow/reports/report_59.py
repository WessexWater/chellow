import csv
import os
import sys
import threading
import traceback

from flask import g, request

from sqlalchemy import null, or_, select, true
from sqlalchemy.orm import joinedload

import chellow.dloads
from chellow.models import Era, Session, Site, SiteEra, Supply
from chellow.utils import csv_make_val, req_date, req_int, req_str
from chellow.views.home import chellow_redirect


METER_ORDER = {"hh": 0, "amr": 1, "nhh": 2, "unmetered": 3, "": 4}


def content(start_date, finish_date, site_id, user, site_codes):
    sess = f = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            "sites_duration.csv", user
        )
        f = open(running_name, mode="w", newline="")
        _process(sess, f, start_date, finish_date, site_id, site_codes)
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


def _process(sess, f, start_date, finish_date, site_id, site_codes):
    writer = csv.writer(f, lineterminator="\n")
    streams = "imp_net", "displaced", "exp_net", "used", "exp_gen", "imp_gen"
    titles = [
        "site_code",
        "site_name",
        "associated_site_ids",
        "sources",
        "generator_types",
        "from",
        "to",
    ]
    for stream in streams:
        for suf in ("sum_kwh", "max_kw", "avg_kw"):
            titles.append(f"{stream}_{suf}")

    titles.append("metering_type")

    writer.writerow(titles)

    sites = select(Site).order_by(Site.code)
    if site_id is not None:
        sites = sites.where(Site.id == site_id)

    if site_codes is not None:
        sites = sites.where(Site.code.in_(site_codes))

    for site in sess.execute(sites).scalars():
        assoc = " ".join(
            s.code for s in site.find_linked_sites(sess, start_date, finish_date)
        )

        totals = {stream: {"sum": 0, "max": 0} for stream in streams}

        metering_type = ""
        source_codes = set()
        gen_types = set()
        for era in (
            sess.query(Era)
            .join(SiteEra)
            .filter(
                SiteEra.is_physical == true(),
                SiteEra.site == site,
                Era.start_date <= finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
            )
            .distinct()
            .options(
                joinedload(Era.supply).joinedload(Supply.source),
                joinedload(Era.supply).joinedload(Supply.generator_type),
            )
        ):
            supply = era.supply
            source_codes.add(supply.source.code)
            gen_type = supply.generator_type
            if gen_type is not None:
                gen_types.add(gen_type.code)
            era_meter_type = era.meter_category
            if METER_ORDER[era_meter_type] < METER_ORDER[metering_type]:
                metering_type = era_meter_type

        hh_count = 0
        for hh in site.hh_data(sess, start_date, finish_date):
            hh_count += 1
            for stream in streams:
                total = totals[stream]
                hhs = hh[stream]
                total["sum"] += hhs
                total["max"] = max(total["max"], hhs * 2)

        vals = {
            "site_code": site.code,
            "site_name": site.name,
            "associated_site_ids": assoc,
            "sources": source_codes,
            "generator_types": gen_types,
            "from": start_date,
            "to": finish_date,
        }

        for stream in streams:
            for k, suf in (("sum", "sum_kwh"), ("max", "max_kw")):
                vals[f"{stream}_{suf}"] = totals[stream][k]
            vals[f"{stream}_avg_kw"] = totals[stream]["sum"] / hh_count * 2

        vals["metering_type"] = metering_type
        writer.writerow([csv_make_val(vals[t]) for t in titles])

        # Prevent long-running transaction
        sess.rollback()


def do_get(sess):
    start_date = req_date("start")
    finish_date = req_date("finish")
    site_id = req_int("site_id") if "site_id" in request.values else None

    site_codes_str = req_str("site_codes")
    site_codes = site_codes_str.splitlines()
    if len(site_codes) == 0:
        site_codes = None

    args = start_date, finish_date, site_id, g.user, site_codes
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
