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


def content():
    sess = None
    try:
        sess = db.session()
        yield "Site Id, Site Name, Associated Site Ids, Sources, " \
            "Generator Types, Date, Imported kWh, Displaced kWh, " \
            "Exported kWh, Used kWh, Parasitic kWh, Generated kWh, " \
            "Meter Type\n"

        start_date = form_date(inv, 'start')
        finish_date = form_date(inv, 'finish')

        sites = sess.query(Site).order_by(Site.code)
        if inv.hasParameter('site_id'):
            site_id = inv.getLong('site_id')
            sites = sites.filter(Site.id == site_id)

        for site in sites:
            sources = set()
            generator_types = set()
            assoc = set()

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

            assoc_str = ','.join(sorted(list(assoc)))

            for group in site.groups(sess, start_date, finish_date, True):
                for supply in group.supplies:
                    sources.add(supply.source.code)
                    generator_type = supply.generator_type
                    if generator_type is not None:
                        generator_types.add(generator_type.code)

                sources_str = ','.join(sorted(list(sources)))
                generators_str = ','.join(sorted(list(generator_types)))

                for hh in group.hh_data(sess):
                    yield ','.join(
                        '"' + str(v) + '"' for v in (
                            site.code, site.name, assoc_str, sources_str,
                            generators_str,
                            hh['start_date'].strftime("%Y-%m-%d %H:%M"),
                            hh['imp_net'], hh['displaced'], hh['exp_net'],
                            hh['used'], hh['exp_gen'], hh['imp_gen'],
                            metering_type)) + '\n'
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name="sites_duration.csv")
