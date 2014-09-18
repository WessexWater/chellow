from net.sf.chellow.monad import Monad
import collections
import operator
import pytz
import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, cast, Float

Monad.getUtils()['impt'](globals(), 'templater', 'db', 'computer', 'utils')

HH, hh_before, hh_format = utils.HH, utils.hh_before, utils.hh_format
form_date = utils.form_date
Batch, Bill, Era, Site, SiteEra = db.Batch, db.Bill, db.Era, db.Site, db.SiteEra
Supply, Source, Channel = db.Supply, db.Source, db.Channel
HhDatum = db.HhDatum

caches = {}

inv.getResponse().setContentType("text/csv")
inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="sites_duration.csv"')
pw = inv.getResponse().getWriter()

forecast_date = datetime.datetime.max.replace(tzinfo=pytz.utc)

sess = None
try:
    sess = db.session()
    pw.println("Site Id, Site Name, Associated Site Ids, Sources, Generator Types, From, To, Imported kWh, Displaced kWh, Exported kWh, Used kWh, Parasitic kWh, Generated kWh,Meter Type")
    pw.flush()

    start_date = form_date(inv, 'start')
    finish_date = form_date(inv, 'finish')

    streams = ('imp_net', 'displaced', 'exp_net', 'used', 'exp_gen', 'imp_gen')


    sites = sess.query(Site).order_by(Site.code)
    if inv.hasParameter('site_id'):
        site_id = inv.getLong('site_id')
        sites = sites.filter(Site.id == site_id)
        
    for site in sites:
        sources = set()
        generator_types = set()
        assoc = set()

        totals = dict((stream, 0) for stream in streams)

        metering_type = 'nhh'
        site_code = site.code

        for group in site.groups(sess, start_date, finish_date, False):
            assoc.update(s.code for s in group.sites if s.code != site_code)


            for supply in group.supplies:
                for era in supply.find_eras(sess, group.start_date, group.finish_date):
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
        pw.println(','.join('"' + str(v) + '"' for v in (site.code, site.name, assoc_str, sources_str, generators_str, start_date.strftime("%Y-%m-%d %H:%M"), finish_date.strftime("%Y-%m-%d %H:%M"), totals['imp_net'], totals['displaced'], totals['exp_net'], totals['used'], totals['exp_gen'], totals['imp_gen'], metering_type)))
        pw.flush()
    pw.close()
finally:
    if sess is not None:
        sess.close()

