from sqlalchemy import or_
from sqlalchemy.sql.expression import null
import traceback
from chellow.utils import (
    HH, csv_make_val, req_int, utc_datetime, MONTH, reduce_bill_hhs)
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
from dateutil.relativedelta import relativedelta


def _make_sites(sess, year_start, year_finish, site_id, source_codes):
    sites = sess.query(Site).join(SiteEra).join(Era).join(Supply).join(
        Source).filter(
        Source.code.in_(source_codes),
        Era.start_date <= year_finish, or_(
            Era.finish_date == null(),
            Era.finish_date >= year_start)).distinct().order_by(Site.code)

    if site_id is not None:
        sites = sites.filter(Site.id == site_id)

    return sites


def _write_sites(sess, caches, writer, year, site_id):
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

    march_finish = utc_datetime(year, 4, 1) - HH
    march_start = utc_datetime(year, 3, 1)
    year_start = utc_datetime(year - 1, 4, 1)

    forecast_date = chellow.computer.forecast_date()

    sites = _make_sites(
        sess, year_start, march_finish, site_id, ('gen', 'gen-net'))

    scalar_names = {
        'triad-actual-gsp-kw', 'triad-actual-gbp'
    }

    rate_names = {
        'triad-actual-rate', 'triad-estimate-rate'
    }

    for i in range(1, 4):
        pref = 'triad-actual-' + str(i) + '-'
        for suf in ('msp-kw', 'gsp-kw'):
            scalar_names.add(pref + suf)
        for suf in ('date', 'status', 'laf'):
            rate_names.add(pref + suf)

    for site in sites:
        displaced_era = None
        for i in range(12):
            month_start = march_start - relativedelta(months=i)
            month_finish = month_start + MONTH - HH
            displaced_era = chellow.computer.displaced_era(
                sess, caches, site, month_start, month_finish, forecast_date)
            if displaced_era is not None:
                break

        if displaced_era is None:
            break

        site_ds = chellow.computer.SiteSource(
            sess, site, march_start, march_finish, forecast_date, caches,
            displaced_era)
        chellow.duos.duos_vb(site_ds)
        chellow.triad.hh(site_ds)

        for hh in site_ds.hh_data:
            bill_hh = site_ds.supplier_bill_hhs[hh['start-date']]
            for k in scalar_names & hh.keys():
                bill_hh[k] = hh[k]

            for k in rate_names & hh.keys():
                bill_hh[k] = {hh[k]}

        bill = reduce_bill_hhs(site_ds.supplier_bill_hhs)
        values = [site.code, site.name]
        for i in range(1, 4):
            triad_prefix = 'triad-actual-' + str(i) + '-'
            for suffix in ('date', 'msp-kw', 'laf', 'gsp-kw'):
                values.append(csv_make_val(bill[triad_prefix + suffix]))

        for suffix in ('gsp-kw', 'rate', 'gbp'):
            values.append(csv_make_val(bill['triad-actual-' + suffix]))

        writer.writerow(values)

        # Avoid long-running transaction
        sess.rollback()


def content(year, site_id, user):
    caches = {}
    sess = f = writer = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'output.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        _write_sites(sess, caches, writer, year, site_id)

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
