import traceback
from chellow.utils import req_date, req_int
from chellow.models import Site, Session
from flask import request, g
import csv
import chellow.dloads
from chellow.views import chellow_redirect
import threading
import sys
import os


def content(start_date, finish_date, site_id, user):
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'sites_duration.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(
            (
                "Site Id", "Site Name", "Associated Site Ids", "Sources",
                "Generator Types", "From", "To", "Imported kWh",
                "Displaced kWh", "Exported kWh", "Used kWh", "Parasitic kWh",
                "Generated kWh", "Meter Type"))

        streams = (
            'imp_net', 'displaced', 'exp_net', 'used', 'exp_gen', 'imp_gen')

        sites = sess.query(Site).order_by(Site.code)
        if site_id is not None:
            sites = sites.filter(Site.id == site_id)

        for site in sites:
            sources = set()
            generator_types = set()
            assoc = set()

            totals = dict((stream, 0) for stream in streams)

            metering_type = 'nhh'
            site_code = site.code

            for group in site.groups(sess, start_date, finish_date, False):
                assoc.update(
                    s.code for s in group.sites if s.code != site_code)

                for supply in group.supplies:
                    for era in supply.find_eras(
                            sess, group.start_date, group.finish_date):
                        if metering_type != 'hh':
                            if era.pc.code == '00':
                                metering_type = 'hh'
                            elif metering_type != 'amr':
                                if len(era.channels) > 0:
                                    metering_type = 'amr'
                                elif metering_type != 'nhh':
                                    if era.mtc.meter_type.code in ['UM', 'PH']:
                                        metering_type = 'unmetered'
                                    else:
                                        metering_type = 'nhh'

            for group in site.groups(sess, start_date, finish_date, True):
                for supply in group.supplies:
                    sources.add(supply.source.code)
                    generator_type = supply.generator_type
                    if generator_type is not None:
                        generator_types.add(generator_type.code)

                for hh in group.hh_data(sess):
                    for stream in streams:
                        totals[stream] += hh[stream]

            assoc_str = ','.join(sorted(list(assoc)))
            sources_str = ','.join(sorted(list(sources)))
            generators_str = ','.join(sorted(list(generator_types)))
            writer.writerow(
                (
                    site.code, site.name, assoc_str, sources_str,
                    generators_str, start_date.strftime("%Y-%m-%d %H:%M"),
                    finish_date.strftime("%Y-%m-%d %H:%M"), totals['imp_net'],
                    totals['displaced'], totals['exp_net'], totals['used'],
                    totals['exp_gen'], totals['imp_gen'], metering_type))
    except:
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
    site_id = req_int('site_id') if 'site_id' in request.values else None
    args = (start_date, finish_date, site_id, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
