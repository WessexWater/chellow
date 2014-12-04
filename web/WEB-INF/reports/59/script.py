from net.sf.chellow.monad import Monad
import pytz
import datetime
import traceback
import utils
import db
Monad.getUtils()['impt'](globals(), 'templater', 'db', 'computer', 'utils')

HH, hh_before, hh_format = utils.HH, utils.hh_before, utils.hh_format
form_date = utils.form_date
Batch, Bill, Era, Site = db.Batch, db.Bill, db.Era, db.Site
SiteEra = db.SiteEra
Supply, Source, Channel = db.Supply, db.Source, db.Channel
HhDatum = db.HhDatum
inv = globals()['inv']

caches = {}
forecast_date = datetime.datetime.max.replace(tzinfo=pytz.utc)
start_date = form_date(inv, 'start')
finish_date = form_date(inv, 'finish')
if inv.hasParameter('site_id'):
    site_id = inv.getLong('site_id')
else:
    site_id = None


def content():
    sess = None
    try:
        sess = db.session()
        yield "Site Id, Site Name, Associated Site Ids, Sources, " + \
            "Generator Types, From, To, Imported kWh, Displaced kWh, " + \
            "Exported kWh, Used kWh, Parasitic kWh, Generated kWh,Meter Type\n"

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
            yield ','.join('"' + str(v) + '"' for v in (
                site.code, site.name, assoc_str, sources_str, generators_str,
                start_date.strftime("%Y-%m-%d %H:%M"),
                finish_date.strftime("%Y-%m-%d %H:%M"), totals['imp_net'],
                totals['displaced'], totals['exp_net'], totals['used'],
                totals['exp_gen'], totals['imp_gen'], metering_type)) + '\n'
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name='sites_duration.csv')
