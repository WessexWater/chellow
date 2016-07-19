import traceback
from chellow.utils import send_response, req_date, req_int
from chellow.models import Site
from flask import request


def content(start_date, finish_date, site_id, sess):
    try:
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


def do_get(sess):
    start_date = req_date('start')
    finish_date = req_date('finish')
    site_id = req_int('site_id') if 'site_id' in request.values else None
    return send_response(
        content, args=(start_date, finish_date, site_id, sess),
        file_name='sites_duration.csv')
