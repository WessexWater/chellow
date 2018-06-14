import pytz
import datetime
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
import traceback
from chellow.utils import HH, hh_format, req_int
from chellow.models import Site, SiteEra, Era, Supply, Source, Session
import chellow.computer
import chellow.duos
import chellow.triad
from flask import request, g
import csv
import chellow.dloads
import os
from chellow.views import chellow_redirect
import threading
from werkzeug.exceptions import BadRequest


def content(year, site_id, user):
    caches = {}
    sess = f = writer = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'output.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(
            (
                "Site Code", "Site Name", "Displaced TRIAD 1 Date",
                "Displaced TRIAD 1 MSP kW", "Displaced TRIAD LAF",
                "Displaced TRIAD 1 GSP kW", "Displaced TRIAD 2 Date",
                "Displaced TRIAD 2 MSP kW", "Displaced TRIAD 2 LAF",
                "Displaced TRIAD 2 GSP kW", "Displaced TRIAD 3 Date",
                "Displaced TRIAD 3 MSP kW", "Displaced TRIAD 3 LAF",
                "Displaced TRIAD 3 GSP kW", "Displaced GSP kW",
                "Displaced Rate GBP / kW", "GBP"))

        march_finish = datetime.datetime(year, 4, 1, tzinfo=pytz.utc) - HH
        march_start = datetime.datetime(year, 3, 1, tzinfo=pytz.utc)

        forecast_date = chellow.computer.forecast_date()

        if site_id is None:
            sites = sess.query(Site).join(SiteEra).join(Era).join(Supply).join(
                Source).filter(
                Source.code.in_(('gen', 'gen-net')),
                Era.start_date <= march_finish,
                or_(
                    Era.finish_date == null(),
                    Era.finish_date >= march_start)).distinct()
        else:
            site = Site.get_by_id(sess, site_id)
            sites = sess.query(Site).filter(Site.id == site.id)

        for site in sites.order_by(Site.code):
            displaced_era = chellow.computer.displaced_era(
                sess, caches, site, march_start, march_finish, forecast_date)
            if displaced_era is None:
                continue

            site_ds = chellow.computer.SiteSource(
                sess, site, march_start, march_finish, forecast_date, caches,
                displaced_era)
            chellow.duos.duos_vb(site_ds)
            chellow.triad.hh(site_ds)
            chellow.triad.bill(site_ds)

            bill = site_ds.supplier_bill
            for rname, rset in site_ds.supplier_rate_sets.items():
                if len(rset) == 1:
                    bill[rname] = rset.pop()
            values = [site.code, site.name]
            for i in range(1, 4):
                triad_prefix = 'triad-actual-' + str(i)
                values.append(hh_format(bill[triad_prefix + '-date']))
                for suffix in ['-msp-kw', '-laf', '-gsp-kw']:
                    values.append(bill[triad_prefix + suffix])

            values += [
                str(bill['triad-actual-' + suf]) for suf in [
                    'gsp-kw', 'rate', 'gbp']]

            writer.writerow(values)

            # Avoid long-running transaction
            sess.rollback()
    except BadRequest as e:
        writer.writerow([e.description])
    except BaseException:
        writer.writerow([traceback.format_exc()])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    site_id = req_int('site_id') if 'site_id' in request.values else None
    year = req_int('year')
    threading.Thread(target=content, args=(year, site_id, g.user)).start()
    return chellow_redirect("/downloads", 303)
