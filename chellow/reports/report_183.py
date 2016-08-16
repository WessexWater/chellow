import zipfile
import traceback
from sqlalchemy.sql.expression import true, null
from sqlalchemy import or_
from chellow.models import Site, SiteEra, Era, Session
from chellow.utils import hh_format, req_date, req_int, HH
from flask import request, g
import chellow.dloads
import sys
import os
import csv
from chellow.views import chellow_redirect
import threading
from io import StringIO
from dateutil.relativedelta import relativedelta


def none_content(site_id, start_date, finish_date, user, file_name):
    sess = zf = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            file_name, user)
        sites = sess.query(Site).join(SiteEra).join(Era).filter(
            SiteEra.is_physical == true(), or_(
                Era.finish_date == null(), Era.finish_date >= start_date),
            Era.start_date <= finish_date)
        zf = zipfile.ZipFile(running_name, 'w')

        for site in sites:
            for group in site.groups(sess, start_date, finish_date, True):
                buf = StringIO()
                writer = csv.writer(buf, lineterminator='\n')
                writer.writerow(
                    [
                        "Site Code", "Site Name", "Associated Site Codes",
                        "Sources", "Generator Types", "From", "To", "Type",
                        "Date"] + list(map(str, range(1, 49))))
                associates = ' '.join(site.code for site in group.sites[1:])
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
                row = None
                for hh in group.hh_data(sess):
                    hh_start = hh['start_date']
                    if hh_start.hour == 0 and hh_start.minute == 0:
                        if row is not None:
                            writer.writerow(row)
                        row = [
                            site.code, site.name, associates, source_codes,
                            gen_types, group_start_str, group_finish_str,
                            'used', hh_start.strftime('%Y-%m-%d')]
                    used_gen_kwh = hh['imp_gen'] - hh['exp_net'] - \
                        hh['exp_gen']
                    used_3p_kwh = hh['imp_3p'] - hh['exp_3p']
                    used_kwh = hh['imp_net'] + used_gen_kwh + used_3p_kwh
                    row.append(str(round(used_kwh, 2)))
                if row is not None:
                    writer.writerow(row)
                zf.writestr(
                    site.code + '_' +
                    group.finish_date.strftime('%Y%m%d%M%H') + '.csv',
                    buf.getvalue())
    except:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        zf.write(msg)
    finally:
        if sess is not None:
            sess.close()
        if zf is not None:
            zf.close()
            os.rename(running_name, finished_name)


def site_content(site_id, start_date, finish_date, user, file_name):
    sess = f = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            file_name, user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        site = Site.get_by_id(sess, site_id)
        sites = sess.query(Site).filter(Site.id == site_id)

        for site in sites:
            for group in site.groups(sess, start_date, finish_date, True):
                writer.writerow(
                    [
                        "Site Code", "Site Name", "Associated Site Codes",
                        "Sources", "Generator Types", "From", "To", "Type",
                        "Date"] + list(map(str, range(1, 49))))
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
                vals = None
                for hh in group.hh_data(sess):
                    hh_start = hh['start_date']
                    if hh_start.hour == 0 and hh_start.minute == 0:
                        if vals is not None:
                            writer.writerow(vals)
                        vals = [
                            site.code, site.name, associates, source_codes,
                            gen_types, group_start_str, group_finish_str,
                            'used', hh_start.strftime('%Y-%m-%d')]
                    used_gen_kwh = hh['imp_gen'] - hh['exp_net'] - \
                        hh['exp_gen']
                    used_3p_kwh = hh['imp_3p'] - hh['exp_3p']
                    used_kwh = hh['imp_net'] + used_gen_kwh + used_3p_kwh
                    vals.append(str(round(used_kwh, 2)))
                if vals is not None:
                    writer.writerow(vals)
    except:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        f.write(msg)
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    start_date = req_date('start', 'day')
    finish_date = req_date('finish', 'day')
    finish_date = finish_date + relativedelta(days=1) - HH

    if 'site_id' in request.values:
        site_id = req_int('site_id')
        file_name = "sites_hh_data_" + str(site_id) + "_" + \
            finish_date.strftime('%Y%m%d%H%M') + ".csv"
    else:
        site_id = None
        file_name = "supplies_hh_data_" + \
            finish_date.strftime('%Y%m%d%H%M') + ".zip"

    content = none_content if site_id is None else site_content
    args = (site_id, start_date, finish_date, g.user, file_name)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
