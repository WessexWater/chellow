import traceback
import zipfile
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from chellow.models import Session, Supply, Era, HhDatum, Channel
import os
import threading
import chellow.dloads
from chellow.utils import (
    hh_range, req_bool, req_int, req_str, parse_mpan_core, to_ct, to_utc,
    ct_datetime)
from flask import request, g
from chellow.views import chellow_redirect
from io import StringIO
import csv


def content(
        start_date_ct, finish_date_ct, imp_related, channel_type, is_zipped,
        supply_id, mpan_cores, user):
    start_date, finish_date = to_utc(start_date_ct), to_utc(finish_date_ct)
    zf = sess = tf = None
    base_name = ["supplies_hh_data", finish_date_ct.strftime('%Y%m%d%H%M')]
    cache = {}
    try:
        sess = Session()
        supplies = sess.query(Supply).join(Era).filter(
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
            Era.start_date <= finish_date).order_by(Supply.id).distinct()
        if supply_id is not None:
            supply = Supply.get_by_id(sess, supply_id)
            supplies = supplies.filter(Supply.id == supply.id)
            first_era = sess.query(Era).filter(
                Era.supply == supply,
                or_(
                    Era.finish_date == null(), Era.finish_date >= start_date),
                Era.start_date <= finish_date).order_by(Era.start_date).first()
            if first_era.imp_mpan_core is None:
                name_core = first_era.exp_mpan_core
            else:
                name_core = first_era.imp_mpan_core
            base_name.append("supply_" + name_core.replace(' ', '_'))

        if mpan_cores is not None:
            supplies = supplies.filter(
                or_(
                    Era.imp_mpan_core.in_(mpan_cores),
                    Era.exp_mpan_core.in_(mpan_cores)))
            base_name.append('filter')

        cf = StringIO()
        writer = csv.writer(cf, lineterminator='\n')
        titles = [
            'Import MPAN Core', 'Export MPAN Core', 'Import Related?',
            'Channel Type', 'HH Start Clock-Time'] + list(range(1, 51))
        writer.writerow(titles)
        titles_csv = cf.getvalue()
        cf.close()

        running_name, finished_name = chellow.dloads.make_names(
            '_'.join(base_name) + ('.zip' if is_zipped else '.csv'), user)
        if is_zipped:
            zf = zipfile.ZipFile(running_name, "w", zipfile.ZIP_DEFLATED)
        else:
            tf = open(running_name, mode='w', newline='')
            tf.write(titles_csv)

        for supply in supplies:
            cf = StringIO()
            writer = csv.writer(cf, lineterminator='\n')
            era = supply.find_era_at(sess, finish_date)
            if era is None:
                imp_mpan_core_str = exp_mpan_core_str = 'NA'
            else:
                if era.imp_mpan_core is None:
                    imp_mpan_core_str = "NA"
                else:
                    imp_mpan_core_str = era.imp_mpan_core
                if era.exp_mpan_core is None:
                    exp_mpan_core_str = "NA"
                else:
                    exp_mpan_core_str = era.exp_mpan_core

            imp_related_str = "TRUE" if imp_related else "FALSE"

            hh_data = iter(
                sess.query(HhDatum).join(Channel).join(Era).filter(
                    Era.supply == supply, HhDatum.start_date >= start_date,
                    HhDatum.start_date <= finish_date,
                    Channel.imp_related == imp_related,
                    Channel.channel_type == channel_type
                ).order_by(HhDatum.start_date))
            datum = next(hh_data, None)

            row = []
            for current_date in hh_range(cache, start_date, finish_date):
                dt_ct = to_ct(current_date)
                if dt_ct.hour == 0 and dt_ct.minute == 0:
                    if len(row) > 0:
                        writer.writerow(row)
                    row = [
                        imp_mpan_core_str, exp_mpan_core_str, imp_related_str,
                        channel_type, dt_ct.strftime('%Y-%m-%d')
                    ]

                if datum is not None and datum.start_date == current_date:
                    row.append(datum.value)
                    datum = next(hh_data, None)
                else:
                    row.append(None)

            if len(row) > 0:
                writer.writerow(row)

            if is_zipped:
                fname = '_'.join(
                    (
                        imp_mpan_core_str, exp_mpan_core_str,
                        str(supply.id) + '.csv'
                    )
                )
                zf.writestr(fname.encode('ascii'), titles_csv + cf.getvalue())
            else:
                tf.write(cf.getvalue())
            cf.close()

            # Avoid long-running transaction
            sess.rollback()

        if is_zipped:
            zf.close()
        else:
            tf.close()

    except BaseException:
        msg = traceback.format_exc()
        if is_zipped:
            zf.writestr('error.txt', msg)
            zf.close()
        else:
            tf.write(msg)
    finally:
        if sess is not None:
            sess.close()
        os.rename(running_name, finished_name)


def do_get(sess):
    return handle_request()


def do_post(sess):
    if 'mpan_cores' in request.values:
        mpan_cores_str = req_str('mpan_cores')
        mpan_cores = mpan_cores_str.splitlines()
        if len(mpan_cores) == 0:
            mpan_cores = None
        else:
            for i in range(len(mpan_cores)):
                mpan_cores[i] = parse_mpan_core(mpan_cores[i])
    return handle_request(mpan_cores)


def handle_request(mpan_cores=None):
    start_year = req_int('start_year')
    start_month = req_int('start_month')
    start_day = req_int('start_day')
    start_date_ct = ct_datetime(start_year, start_month, start_day)

    finish_year = req_int('finish_year')
    finish_month = req_int('finish_month')
    finish_day = req_int('finish_day')
    finish_date_ct = ct_datetime(finish_year, finish_month, finish_day, 23, 30)

    imp_related = req_bool('imp_related')
    channel_type = req_str('channel_type')
    is_zipped = req_bool('is_zipped')
    supply_id = req_int('supply_id') if 'supply_id' in request.values else None
    user = g.user
    args = (
        start_date_ct, finish_date_ct, imp_related, channel_type, is_zipped,
        supply_id, mpan_cores, user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
