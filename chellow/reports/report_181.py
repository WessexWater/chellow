import csv
import os
import threading
import traceback

from flask import g, request

from sqlalchemy import or_
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

import chellow.computer
import chellow.dloads
import chellow.duos
import chellow.triad
from chellow.models import Era, Pc, Session, Site, SiteEra, Source, Supply
from chellow.utils import (
    HH,
    c_months_u,
    csv_make_val,
    ct_datetime,
    reduce_bill_hhs,
    req_int,
    to_utc,
)
from chellow.views import chellow_redirect


def _make_sites(sess, year_start, year_finish, site_id, source_codes):
    sites = (
        sess.query(Site)
        .join(SiteEra)
        .join(Era)
        .join(Pc)
        .join(Supply)
        .join(Source)
        .filter(
            Pc.code == "00",
            Source.code.in_(source_codes),
            Era.start_date <= year_finish,
            or_(Era.finish_date == null(), Era.finish_date >= year_start),
        )
        .distinct()
        .order_by(Site.code)
    )

    if site_id is not None:
        sites = sites.filter(Site.id == site_id)

    return sites


def _write_sites(sess, caches, writer, year, site_id):
    titles = (
        "Site Code",
        "Site Name",
        "Displaced TRIAD 1 Date",
        "Displaced TRIAD 1 MSP kW",
        "Displaced TRIAD LAF",
        "Displaced TRIAD 1 GSP kW",
        "Displaced TRIAD 2 Date",
        "Displaced TRIAD 2 MSP kW",
        "Displaced TRIAD 2 LAF",
        "Displaced TRIAD 2 GSP kW",
        "Displaced TRIAD 3 Date",
        "Displaced TRIAD 3 MSP kW",
        "Displaced TRIAD 3 LAF",
        "Displaced TRIAD 3 GSP kW",
        "Displaced GSP kW",
        "Displaced Rate GBP / kW",
        "GBP",
    )
    writer.writerow(titles)

    march_finish_ct = ct_datetime(year, 4, 1) - HH
    march_finish_utc = to_utc(march_finish_ct)
    march_start_ct = ct_datetime(year, 3, 1)
    march_start_utc = to_utc(march_start_ct)
    year_start = to_utc(ct_datetime(year - 1, 4, 1))

    forecast_date = chellow.computer.forecast_date()

    sites = _make_sites(sess, year_start, march_finish_utc, site_id, ("gen", "gen-net"))

    scalar_names = {"triad-actual-gsp-kw", "triad-actual-gbp"}

    rate_names = {"triad-actual-rate", "triad-estimate-rate"}

    for i in range(1, 4):
        pref = "triad-actual-" + str(i) + "-"
        for suf in ("msp-kw", "gsp-kw"):
            scalar_names.add(pref + suf)
        for suf in ("date", "status", "laf"):
            rate_names.add(pref + suf)

    for site in sites:
        displaced_era = None
        for month_start, month_finish in sorted(
            c_months_u(start_year=year - 1, start_month=4, months=12), reverse=True
        ):
            displaced_era = chellow.computer.displaced_era(
                sess, caches, site, month_start, month_finish, forecast_date
            )
            if displaced_era is not None:
                break

        if displaced_era is None:
            break

        site_ds = chellow.computer.SiteSource(
            sess,
            site,
            march_start_utc,
            march_finish_utc,
            forecast_date,
            caches,
            displaced_era,
        )
        chellow.duos.duos_vb(site_ds)
        chellow.triad.hh(site_ds)

        for hh in site_ds.hh_data:
            bill_hh = site_ds.supplier_bill_hhs[hh["start-date"]]
            for k in scalar_names & hh.keys():
                bill_hh[k] = hh[k]

            for k in rate_names & hh.keys():
                bill_hh[k] = {hh[k]}

        bill = reduce_bill_hhs(site_ds.supplier_bill_hhs)
        values = [site.code, site.name]
        for i in range(1, 4):
            triad_prefix = "triad-actual-" + str(i) + "-"
            for suffix in ("date", "msp-kw", "laf", "gsp-kw"):
                values.append(csv_make_val(bill[triad_prefix + suffix]))

        for suffix in ("gsp-kw", "rate", "gbp"):
            values.append(csv_make_val(bill["triad-actual-" + suffix]))

        writer.writerow(values)

        # Avoid long-running transaction
        sess.rollback()


def content(year, site_id, user):
    caches = {}
    sess = f = writer = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names("output.csv", user)
        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")
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
    site_id = req_int("site_id") if "site_id" in request.values else None
    year = req_int("year")
    threading.Thread(target=content, args=(year, site_id, g.user)).start()
    return chellow_redirect("/downloads", 303)
