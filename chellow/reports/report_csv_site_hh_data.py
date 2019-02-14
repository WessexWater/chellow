import traceback
from flask import request, g
from chellow.utils import req_date, req_int, hh_format
from chellow.models import Site, Era, SiteEra, Source, Supply, Session
from sqlalchemy import true, or_, null
from sqlalchemy.orm import joinedload
import chellow.dloads
import csv
import sys
import os
import threading
from chellow.views import chellow_redirect


TYPE_ORDER = {'hh': 0, 'amr': 1, 'nhh': 2, 'unmetered': 3}


def content(sess, start_date, finish_date, site_id, user):
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            "site_hh_data.csv", user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(
            (
                "Site Id", "Site Name", "Associated Site Ids", "Sources",
                "Generator Types", "Date", "Imported kWh", "Displaced kWh",
                "Exported kWh", "Used kWh", "Parasitic kWh", "Generated kWh",
                "Meter Type"))

        sites = sess.query(Site).order_by(Site.code)
        if site_id is not None:
            sites = sites.filter(Site.id == site_id)

        for site in sites:
            sources = set()
            generator_types = set()
            assoc = site.find_linked_sites(sess, start_date, finish_date)
            metering_type = ''
            for era in sess.query(Era).join(SiteEra).filter(
                    SiteEra.site == site, SiteEra.is_physical == true(),
                    Era.start_date <= finish_date, or_(
                        Era.finish_date == null(),
                        Era.finish_date >= start_date),
                    Source.code != 'sub').options(
                        joinedload(Era.supply).joinedload(Supply.source),
                        joinedload(Era.supply).joinedload(
                            Supply.generator_type)):
                mtype = era.meter_category
                if metering_type == '' or \
                        TYPE_ORDER[mtype] < TYPE_ORDER[metering_type]:
                    metering_type = mtype
                sources.add(era.supply.source.code)
                generator_type = era.supply.generator_type
                if generator_type is not None:
                    generator_types.add(generator_type.code)

            assoc_str = ','.join(sorted(s.code for s in assoc))
            sources_str = ','.join(sorted(list(sources)))
            generators_str = ','.join(sorted(list(generator_types)))

            for hh in site.hh_data(sess, start_date, finish_date):
                writer.writerow(
                    (
                        site.code, site.name, assoc_str, sources_str,
                        generators_str, hh_format(hh['start_date']),
                        hh['imp_net'], hh['displaced'], hh['exp_net'],
                        hh['used'], hh['exp_gen'], hh['imp_gen'],
                        metering_type))
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
    start_date = req_date('start')
    finish_date = req_date('finish')
    if 'site_id' in request.values:
        site_id = req_int('site_id')
    else:
        site_id = None

    args = (sess, start_date, finish_date, site_id, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
