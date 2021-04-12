import csv
import os
import sys
import threading
import traceback

from flask import g, request

from sqlalchemy import null, or_, true
from sqlalchemy.orm import joinedload

import chellow.dloads
from chellow.models import Era, Session, Site, SiteEra, Supply
from chellow.utils import hh_format, req_date, req_int
from chellow.views import chellow_redirect


METER_ORDER = {"hh": 0, "amr": 1, "nhh": 2, "unmetered": 3, "": 4}


def content(start_date, finish_date, site_id, user):
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            "sites_duration.csv", user
        )
        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(
            (
                "Site Id",
                "Site Name",
                "Associated Site Ids",
                "Sources",
                "Generator Types",
                "From",
                "To",
                "Imported kWh",
                "Displaced kWh",
                "Exported kWh",
                "Used kWh",
                "Parasitic kWh",
                "Generated kWh",
                "Meter Type",
            )
        )

        streams = ("imp_net", "displaced", "exp_net", "used", "exp_gen", "imp_gen")

        sites = sess.query(Site).order_by(Site.code)
        if site_id is not None:
            sites = sites.filter(Site.id == site_id)

        start_date_str = hh_format(start_date)
        finish_date_str = hh_format(finish_date)

        for site in sites:
            assoc = " ".join(
                s.code for s in site.find_linked_sites(sess, start_date, finish_date)
            )

            totals = dict((stream, 0) for stream in streams)

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

            assoc_str = ",".join(sorted(assoc))
            sources_str = ",".join(sorted(source_codes))
            generators_str = ",".join(sorted(gen_types))

            for hh in site.hh_data(sess, start_date, finish_date):
                for stream in streams:
                    totals[stream] += hh[stream]

            writer.writerow(
                (
                    site.code,
                    site.name,
                    assoc_str,
                    sources_str,
                    generators_str,
                    start_date_str,
                    finish_date_str,
                    totals["imp_net"],
                    totals["displaced"],
                    totals["exp_net"],
                    totals["used"],
                    totals["exp_gen"],
                    totals["imp_gen"],
                    metering_type,
                )
            )

            # Prevent long-running transaction
            sess.rollback()
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
    site_id = req_int("site_id") if "site_id" in request.values else None
    args = (start_date, finish_date, site_id, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
