import traceback
from flask import request
from chellow.utils import req_date, send_response, req_int
from chellow.models import sess, Site


def content(start_date, finish_date, site_id):
    try:
        yield ','.join(
            (
                "Site Id", "Site Name", "Associated Site Ids", "Sources",
                "Generator Types", "Date", "Imported kWh", "Displaced kWh",
                "Exported kWh", "Used kWh", "Parasitic kWh", "Generated kWh",
                "Meter Type")) + '\n'

        sites = Site.query.order_by(Site.code)
        if site_id is not None:
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


def do_get(sess):
    start_date = req_date('start')
    finish_date = req_date('finish')
    if 'site_id' in request.values:
        site_id = req_int('site_id')
    else:
        site_id = None

    return send_response(
        content, args=(start_date, finish_date, site_id),
        file_name="site_hh_data.csv")
