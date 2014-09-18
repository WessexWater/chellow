from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from datetime import datetime
from dateutil.relativedelta import relativedelta
from java.util.zip import ZipOutputStream, ZipEntry
from java.io import PrintWriter, OutputStreamWriter
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['HhDatum', 'Site', 'Supply', 'set_read_write', 'session'], 
        'utils': ['UserException', 'HH', 'form_date'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    start_date = form_date(inv, 'start')
    finish_date = form_date(inv, 'finish')
    
    #inv.getResponse().setContentType('text/csv')
    #inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="report.csv"')
    #pw = inv.getResponse().getWriter()
    #pw.println('hello')
    #pw.flush()

    if inv.hasParameter('site_id'):
        site_id = inv.getLong('site_id')
        site = Site.get_by_id(sess, site_id)
        sites = sess.query(Site).from_statement("select * from site where id = :site_id").params(site_id=site_id)
        file_name = "sites_hh_data_" + str(site_id) + "_" + finish_date.strftime('%Y%m%d%M%H') + ".csv"
        inv.getResponse().setContentType('text/csv')
        inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="' + file_name + '"')
        pw = inv.getResponse().getWriter()
        zout = None
    else:
        sites = sess.query(Site).from_statement("select site.* from site, site_era, era where site_era.site_id = site.id and site_era.era_id = era.id and site_era.is_physical is true and (era.finish_date is null or era.finish_date >= :start_date) and era.start_date <= :finish_date").params(start_date=start_date, finish_date=finish_date)
        file_name = "supplies_hh_data_" + finish_date.strftime('%Y%m%d%M%H') + ".zip"
        inv.getResponse().setContentType('application/zip')
        inv.getResponse().setHeader('Content-Disposition', 'attachment; filename="' + file_name + '"')
        sout = inv.getResponse().getOutputStream()
        zout = ZipOutputStream(sout)
        pw = PrintWriter(OutputStreamWriter(zout, 'UTF-8'))

    for site in sites:
        for group in site.groups(sess, start_date, finish_date, True):
            if zout is not None:
                zout.putNextEntry(ZipEntry(site.code + '_' + group.finish_date.strftime('%Y%m%d%M%H') + '.csv'))
            pw.print("Site Code, Site Name, Associated Site Codes, Sources, Generator Types, From, To,Type,Date," + ','.join(map(str, range(1, 49))))
            pw.flush()
            associates = ' '.join(site.code for site in group.sites[1:])
            source_codes = ' '.join(sorted(set(sup.source.code for sup in group.supplies)))
            gen_types = ' '.join(sorted(set(sup.generator_type.code for sup in group.supplies if sup.generator_type is not None)))
            group_start_str = group.start_date.strftime('%Y-%m-%d %H:%M')
            group_finish_str = group.finish_date.strftime('%Y-%m-%d %H:%M')
            for hh in group.hh_data(sess):
                hh_start = hh['start_date']
                if hh_start.hour == 0 and hh_start.minute == 0:
                    pw.print("\r\n" + ','.join('"' + str(val) + '"' for val in [site.code, site.name, associates, source_codes, gen_types, group_start_str, group_finish_str, 'used', hh_start.strftime('%Y-%m-%d')]))
                used_gen_kwh = hh['imp_gen'] - hh['exp_net'] - hh['exp_gen']
                used_3p_kwh = hh['imp_3p'] - hh['exp_3p']
                used_kwh = hh['imp_net'] + used_gen_kwh + used_3p_kwh
                pw.print(',' + str(round(used_kwh, 2)))
            pw.flush()
    pw.close()
finally:
    if sess is not None:
        sess.close()