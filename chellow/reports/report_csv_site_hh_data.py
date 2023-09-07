import csv
import os
import sys
import threading
import traceback

from flask import g, request

from sqlalchemy import null, or_, true
from sqlalchemy.orm import joinedload

import chellow.dloads
from chellow.models import Era, Session, Site, SiteEra, Source, Supply
from chellow.utils import req_date, req_int, write_row
from chellow.views import chellow_redirect


TYPE_ORDER = {"hh": 0, "amr": 1, "nhh": 2, "unmetered": 3}


def content(sess, start_date, finish_date, site_id, user):
    try:
        with Session() as sess:
            running_name, finished_name = chellow.dloads.make_names(
                "site_hh_data.csv", user
            )
            f = open(running_name, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            write_row(
                writer,
                "Site Id",
                "Site Name",
                "Associated Site Ids",
                "Sources",
                "Generator Types",
                "HH Start Clock-Time",
                "Imported kWh",
                "Displaced kWh",
                "Exported kWh",
                "Used kWh",
                "Parasitic kWh",
                "Generated kWh",
                "3rd Party Import",
                "3rd Party Export",
                "Meter Type",
            )

            sites = sess.query(Site).order_by(Site.code)
            if site_id is not None:
                sites = sites.filter(Site.id == site_id)

            for site in sites:
                sources = set()
                generator_types = set()
                assoc = site.find_linked_sites(sess, start_date, finish_date)
                metering_type = ""
                for era in (
                    sess.query(Era)
                    .join(SiteEra)
                    .filter(
                        SiteEra.site == site,
                        SiteEra.is_physical == true(),
                        Era.start_date <= finish_date,
                        or_(Era.finish_date == null(), Era.finish_date >= start_date),
                        Source.code != "sub",
                    )
                    .options(
                        joinedload(Era.supply).joinedload(Supply.source),
                        joinedload(Era.supply).joinedload(Supply.generator_type),
                    )
                ):
                    mtype = era.meter_category
                    if (
                        metering_type == ""
                        or TYPE_ORDER[mtype] < TYPE_ORDER[metering_type]
                    ):
                        metering_type = mtype
                    sources.add(era.supply.source.code)
                    generator_type = era.supply.generator_type
                    if generator_type is not None:
                        generator_types.add(generator_type.code)

                assoc_str = ",".join(sorted(s.code for s in assoc))
                sources_str = ",".join(sorted(list(sources)))
                generators_str = ",".join(sorted(list(generator_types)))

                for hh in site.hh_data(sess, start_date, finish_date):
                    write_row(
                        writer,
                        site.code,
                        site.name,
                        assoc_str,
                        sources_str,
                        generators_str,
                        hh["start_date"],
                        hh["imp_net"],
                        hh["displaced"],
                        hh["exp_net"],
                        hh["used"],
                        hh["exp_gen"],
                        hh["imp_gen"],
                        hh["imp_3p"],
                        hh["exp_3p"],
                        metering_type,
                    )

    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    start_date = req_date("start")
    finish_date = req_date("finish")
    if "site_id" in request.values:
        site_id = req_int("site_id")
    else:
        site_id = None

    args = (sess, start_date, finish_date, site_id, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
