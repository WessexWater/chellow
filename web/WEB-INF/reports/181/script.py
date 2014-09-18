from net.sf.chellow.monad import Monad
import pytz
import datetime
from sqlalchemy import or_

Monad.getUtils()['impt'](globals(), 'computer', 'db', 'utils', 'triad', 'duos')

HH = utils.HH
Site, SiteEra, Era, Supply = db.Site, db.SiteEra, db.Era, db.Supply
Source, Channel = db.Source, db.Channel

caches = {}

sess = None
try:
    sess = db.session()
    inv.getResponse().setContentType("text/csv")
    inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="output.csv"')
    year = inv.getInteger('year')

    pw = inv.getResponse().getWriter()

    march_finish = datetime.datetime(year, 4, 1, tzinfo=pytz.utc) - HH
    march_start = datetime.datetime(year, 3, 1, tzinfo=pytz.utc)

    pw.println("Site Code, Site Name, Displaced TRIAD 1 Date, Displaced TRIAD 1 MSP kW, Displaced TRIAD LAF, Displaced TRIAD 1 GSP kW, Displaced TRIAD 2 Date, Displaced TRIAD 2 MSP kW, Displaced TRIAD 2 LAF, Displaced TRIAD 2 GSP kW, Displaced TRIAD 3 Date, Displaced TRIAD 3 MSP kW, Displaced TRIAD 3 LAF, Displaced TRIAD 3 GSP kW, Displaced GSP kW, Displaced Rate GBP / kW, GBP")
    pw.flush()

    forecast_date = computer.forecast_date()

    if inv.hasParameter('site_id'):
        site_id = inv.getLong('site_id')
        sites = sess.query(Site).filter(Site.id==Site.get_by_id(site_id).id)
    else:
        sites = sess.query(Site).join(SiteEra).join(Era).join(Supply).join(Source).filter(Source.code.in_(('gen', 'gen-net')), Era.start_date<=march_finish, or_(Era.finish_date==None, Era.finish_date>= march_start)).distinct()

    for site in sites:
        for site_group in site.groups(sess, march_start, march_finish, True):
            if site_group.start_date > march_start:
                chunk_start = site_group.start_date
            else:
                chunk_start = march_start

            if not site_group.finish_date < march_finish:
                chunk_finish = march_finish
            else:
                continue

            pw.print('"' + site.code + '","' + site.name + '"')

            displaced_era = computer.displaced_era(sess, site_group, chunk_start, chunk_finish)
            if displaced_era is None:
                continue

            site_ds = computer.SiteSource(sess, site, chunk_start, chunk_finish, forecast_date, pw, caches, displaced_era)
            duos.duos_vb(site_ds)
            triad.triad_bill(site_ds)

            bill = site_ds.supplier_bill
            values = []
            for i in range(3):
                triad_prefix = 'triad-actual-' + str(i)
                for suffix in ['-date', '-msp-kw', '-laf', '-gsp-kw']:
                    values.append(bill[triad_prefix + suffix])

            values += [bill['triad-actual-' + suf] for suf in ['gsp-kw', 'rate', 'gbp']]

            for value in values:
                pw.print("," + str(value))
            pw.println('')
            pw.flush()

    pw.close()
finally:
    if sess is not None:
        sess.close()