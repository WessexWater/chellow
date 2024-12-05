import csv
import sys
import threading
import traceback

from flask import g, redirect, request

from sqlalchemy import null, or_, select, true
from sqlalchemy.orm import joinedload

from chellow.dloads import open_file
from chellow.models import Era, Session, Site, SiteEra, Source, Supply, User
from chellow.utils import req_date, req_int, write_row


TYPE_ORDER = {"hh": 0, "amr": 1, "nhh": 2, "unmetered": 3}


def content(start_date, finish_date, site_id, user_id):
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("site_hh_data.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            write_row(
                writer,
                "site_id",
                "site_name",
                "associated_site_ids",
                "sources",
                "generator_types",
                "hh_start_clock_time",
                "imported_kwh",
                "displaced_kwh",
                "exported_kwh",
                "used_kwh",
                "parasitic_kwh",
                "generated_kwh",
                "3rd_party_import",
                "3rd_party_export",
                "meter_type",
            )

            sites_q = select(Site).order_by(Site.code)
            if site_id is not None:
                sites_q = sites_q.where(Site.id == site_id)

            for site in sess.scalars(sites_q):
                sources = set()
                generator_types = set()
                assoc = site.find_linked_sites(sess, start_date, finish_date)
                metering_type = ""
                for era in sess.scalars(
                    select(Era)
                    .join(SiteEra)
                    .join(Supply)
                    .join(Source)
                    .where(
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
                        hh["imp_grid"],
                        hh["displaced"],
                        hh["exp_grid"],
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


def do_get(sess):
    start_date = req_date("start")
    finish_date = req_date("finish")
    if "site_id" in request.values:
        site_id = req_int("site_id")
    else:
        site_id = None

    args = start_date, finish_date, site_id, g.user.id
    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
