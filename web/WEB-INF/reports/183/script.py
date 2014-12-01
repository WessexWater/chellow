from net.sf.chellow.monad import Monad
from datetime import datetime
from dateutil.relativedelta import relativedelta
import pytz
import StringIO
import zipfile
import traceback

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
session, SiteEra, Era = db.session, db.SiteEra, db.Era
form_int, form_date = utils.form_int, utils.form_date

start_date = form_date(inv, 'start')
finish_date = form_date(inv, 'finish')


if inv.hasParameter('site_id'):
    site_id = form_int(inv, 'site_id')
    file_name = "sites_hh_data_" + str(site_id) + "_" + \
        finish_date.strftime('%Y%m%d%M%H') + ".csv"
    mime_type = 'text/csv'
else:
    site_id = None
    file_name = "supplies_hh_data_" + \
        finish_date.strftime('%Y%m%d%M%H') + ".zip"
    mime_type = 'application/zip'

if site_id is None:
    def content():
        sess = None
        try:
            sess = session()
            
            sites = sess.query(Site).join(SiteEra).join(Era).filter(
                SiteEra.is_physical == True, or_(
                    Era.finish_date == None, Era.finish_date >= start_date),
                Era.start_date <= finish_date)
            bffr = StringIO.StringIO()
            zf = zipfile.ZipFile(bffr)

            for site in sites:
                for group in site.groups(sess, start_date, finish_date, True):
                    outs = []
                    outs.append(
                        "Site Code, Site Name, Associated Site Codes, "
                        "Sources, Generator Types, From, To,Type,Date,"
                        + ','.join(map(str, range(1, 49))))
                    associates = ' '.join(
                        site.code for site in group.sites[1:])
                    source_codes = ' '.join(
                        sorted(set(sup.source.code for sup in group.supplies)))
                    gen_types = ' '.join(
                        sorted(
                            set(
                                sup.generator_type.code for sup in
                                group.supplies
                                if sup.generator_type is not None)))
                    group_start_str = hh_format(group.start_date)
                    group_finish_str = hh_format(group.finish_date)
                    for hh in group.hh_data(sess):
                        hh_start = hh['start_date']
                        if hh_start.hour == 0 and hh_start.minute == 0:
                            outs.append(
                                "\r\n" + ','.join(
                                    '"' + str(val) + '"' for val in
                                    [
                                        site.code, site.name, associates,
                                        source_codes, gen_types,
                                        group_start_str, group_finish_str,
                                        'used',
                                        hh_start.strftime('%Y-%m-%d')]))
                        used_gen_kwh = hh['imp_gen'] - hh['exp_net'] - \
                            hh['exp_gen']
                        used_3p_kwh = hh['imp_3p'] - hh['exp_3p']
                        used_kwh = hh['imp_net'] + used_gen_kwh + used_3p_kwh
                        outs.append(',' + str(round(used_kwh, 2)))
                    zf.writestr(
                        site.code + '_' +
                        group.finish_date.strftime('%Y%m%d%M%H') + '.csv',
                        ''.join(outs))
                    yield bffr.getValue()
                    bffr.truncate()
        except:
            yield traceback.format_exc()
        finally:
            if sess is not None:
                sess.close()
else:
    def content():
        sess = None
        try:
            sess = session()
            
            site_id = inv.getLong('site_id')
            site = Site.get_by_id(sess, site_id)
            sites = sess.query(Site).filter(Site.id == site_id)

            for site in sites:
                for group in site.groups(sess, start_date, finish_date, True):
                    yield "\nSite Code, Site Name, Associated Site Codes, " + \
                        "Sources, Generator Types, From, To,Type,Date," + \
                        ','.join(map(str, range(1, 49)))
                    associates = ' '.join(st.code for st in group.sites[1:])
                    source_codes = ' '.join(
                        sorted(set(sup.source.code for sup in group.supplies)))
                    gen_types = ' '.join(
                        sorted(
                            set(
                                sup.generator_type.code for sup in
                                group.supplies
                                if sup.generator_type is not None)))
                    group_start_str = hh_format(group.start_date)
                    group_finish_str = hh_format(group.finish_date)
                    for hh in group.hh_data(sess):
                        hh_start = hh['start_date']
                        if hh_start.hour == 0 and hh_start.minute == 0:
                            yield "\r\n" + \
                                ','.join(
                                    '"' + str(val) + '"' for val in [
                                        site.code, site.name, associates,
                                        source_codes, gen_types,
                                        group_start_str, group_finish_str,
                                        'used', hh_start.strftime('%Y-%m-%d')])
                        used_gen_kwh = hh['imp_gen'] - hh['exp_net'] - \
                            hh['exp_gen']
                        used_3p_kwh = hh['imp_3p'] - hh['exp_3p']
                        used_kwh = hh['imp_net'] + used_gen_kwh + used_3p_kwh
                        yield ',' + str(round(used_kwh, 2))
        except:
            yield traceback.format_exc()
        finally:
            if sess is not None:
                sess.close()

utils.send_response(
    inv, content, status=200, mimetype=mime_type, file_name=file_name)
