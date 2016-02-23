import pytz
import datetime
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
import traceback
from chellow.utils import send_response, HH, hh_format, req_int
from chellow.models import Site, SiteEra, Era, Supply, Session, Source
import chellow.computer
import chellow.duos
import chellow.triad
from flask import request


def content(year, site_id):
    sess = None
    caches = {}
    try:
        sess = Session()

        march_finish = datetime.datetime(year, 4, 1, tzinfo=pytz.utc) - HH
        march_start = datetime.datetime(year, 3, 1, tzinfo=pytz.utc)

        yield ', '.join(
            (
                "Site Code", "Site Name", "Displaced TRIAD 1 Date",
                "Displaced TRIAD 1 MSP kW", "Displaced TRIAD LAF",
                "Displaced TRIAD 1 GSP kW", "Displaced TRIAD 2 Date",
                "Displaced TRIAD 2 MSP kW", "Displaced TRIAD 2 LAF",
                "Displaced TRIAD 2 GSP kW", "Displaced TRIAD 3 Date",
                "Displaced TRIAD 3 MSP kW", "Displaced TRIAD 3 LAF",
                "Displaced TRIAD 3 GSP kW", "Displaced GSP kW",
                "Displaced Rate GBP / kW", "GBP")) + '\n'

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

        for site in sites:
            for site_group in site.groups(
                    sess, march_start, march_finish, True):
                if site_group.start_date > march_start:
                    chunk_start = site_group.start_date
                else:
                    chunk_start = march_start

                if not site_group.finish_date < march_finish:
                    chunk_finish = march_finish
                else:
                    continue

                yield '"' + site.code + '","' + site.name + '"'

                displaced_era = chellow.computer.displaced_era(
                    sess, site_group, chunk_start, chunk_finish)
                if displaced_era is None:
                    continue

                site_ds = chellow.computer.SiteSource(
                    sess, site, chunk_start, chunk_finish, forecast_date, None,
                    caches, displaced_era)
                chellow.duos.duos_vb(site_ds)
                chellow.triad.triad_bill(site_ds)

                bill = site_ds.supplier_bill
                values = []
                for i in range(1, 4):
                    triad_prefix = 'triad-actual-' + str(i)
                    for suffix in ['-date', '-msp-kw', '-laf', '-gsp-kw']:
                        values.append(bill[triad_prefix + suffix])

                values += [
                    bill['triad-actual-' + suf] for suf in [
                        'gsp-kw', 'rate', 'gbp']]

                for value in values:
                    if isinstance(value, datetime.datetime):
                        yield "," + hh_format(value)
                    else:
                        yield "," + str(value)
                yield '\n'
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()


def do_get(sess):
    site_id = req_int('site_id') if 'site_id' in request.values else None
    year = req_int('year')
    return send_response(content, args=(year, site_id), file_name='output.csv')
