import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
from chellow.models import Supply, Era, Session, Site, SiteEra
from chellow.utils import (
    req_date, hh_format, req_str, req_int, parse_mpan_core, req_bool, hh_range)
import zipfile
import threading
import os
import chellow.dloads
from flask import request, g
from werkzeug.exceptions import BadRequest
from chellow.views import chellow_redirect
from datetime import datetime as Datetime


def csv_str(row):
    frow = []
    for cell in row:
        if cell is None:
            val = ''
        elif isinstance(cell, Datetime):
            val = hh_format(cell)
        else:
            val = str(cell)
        frow.append(val)

    return ','.join('"' + v + '"' for v in frow) + '\n'


def content(start_date, finish_date, supply_id, mpan_cores, is_zipped, user):
    if is_zipped:
        file_extension = ".zip"
    else:
        file_extension = ".csv"

    base_name = "hh_data_row_" + start_date.strftime("%Y%m%d%H%M") + \
        file_extension

    tls = ["Site Code", "Imp MPAN Core", "Exp Mpan Core", "Start Date"]
    for polarity in ('Import', 'Export'):
        for suffix in (
                "ACTIVE kWh", "ACTIVE Status", "ACTIVE Modified",
                "REACTIVE_IMP kVArh", "REACTIVE_IMP Status",
                "REACTIVE_IMP Modified", "REACTIVE_EXP kVArh",
                "REACTIVE_EXP Status", "REACTIVE_EXP Modified"):
            tls.append(polarity + ' ' + suffix)

    titles = csv_str(tls)

    running_name, finished_name = chellow.dloads.make_names(base_name, user)

    if is_zipped:
        zf = zipfile.ZipFile(running_name, 'w')
    else:
        tmp_file = open(running_name, "w")
    sess = None
    try:
        sess = Session()
        caches = {}
        supplies = sess.query(Supply).join(Era).filter(
            Era.start_date <= finish_date, or_(
                Era.finish_date == null(),
                Era.finish_date >= start_date)).order_by(
            Era.supply_id, Era.start_date).distinct()
        if supply_id is not None:
            sup = Supply.get_by_id(sess, supply_id)
            supplies = supplies.filter(Era.supply == sup)

        if mpan_cores is not None:
            supplies = supplies.filter(
                or_(
                    Era.imp_mpan_core.in_(mpan_cores),
                    Era.exp_mpan_core.in_(mpan_cores)))

        if not is_zipped:
            tmp_file.write(titles)

        for supply in supplies:
            site, era = sess.query(
                Site, Era).join(Era.site_eras).filter(
                Era.supply == supply, Era.start_date <= finish_date,
                SiteEra.site_id == Site.id, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= start_date),
                SiteEra.is_physical == true()).order_by(Era.id).first()

            outs = []
            data = iter(
                sess.execute("""
select hh_base.start_date,
    max(imp_active.value), max(imp_active.status),
    max(imp_active.last_modified),
    max(imp_reactive_imp.value), max(imp_reactive_imp.status),
    max(imp_reactive_imp.last_modified),
    max(imp_reactive_exp.value), max(imp_reactive_exp.status),
    max(imp_reactive_exp.last_modified),
    max(exp_active.value), max(exp_active.status),
    max(exp_active.last_modified),
    max(exp_reactive_imp.value), max(imp_reactive_imp.status),
    max(exp_reactive_imp.last_modified),
    max(exp_reactive_exp.value), max(exp_reactive_exp.status),
    max(exp_reactive_exp.last_modified)
from hh_datum hh_base
    join channel on hh_base.channel_id = channel.id
    join era on channel.era_id = era.id
    left join hh_datum imp_active
        on (imp_active.id = hh_base.id and channel.imp_related is true and
            channel.channel_type = 'ACTIVE')
    left join hh_datum imp_reactive_imp
        on (imp_reactive_imp.id = hh_base.id
            and channel.imp_related is true and
            channel.channel_type = 'REACTIVE_IMP')
    left join hh_datum imp_reactive_exp
        on (imp_reactive_exp.id = hh_base.id
            and channel.imp_related is true and
            channel.channel_type = 'REACTIVE_EXP')
    left join hh_datum exp_active
        on (exp_active.id = hh_base.id and channel.imp_related is false and
            channel.channel_type = 'ACTIVE')
    left join hh_datum exp_reactive_imp
                on (exp_reactive_imp.id = hh_base.id
                    and channel.imp_related is
                false and channel.channel_type = 'REACTIVE_IMP')
    left join hh_datum exp_reactive_exp
                on (exp_reactive_exp.id = hh_base.id
                and channel.imp_related is false
                and channel.channel_type = 'REACTIVE_EXP')
where supply_id = :supply_id
    and hh_base.start_date between :start_date and :finish_date
group by hh_base.start_date
order by hh_base.start_date
    """, params={
                    'supply_id': supply.id, 'start_date': start_date,
                    'finish_date': finish_date}))
            datum = next(data, None)

            for dt in hh_range(caches, start_date, finish_date):
                row = [site.code, era.imp_mpan_core, era.exp_mpan_core, dt]
                if datum is not None:
                    (
                        hh_start_date, imp_active, imp_active_status,
                        imp_active_modified, imp_reactive_imp,
                        imp_reactive_imp_status, imp_reactive_imp_modified,
                        imp_reactive_exp, imp_reactive_exp_status,
                        imp_reactive_exp_modified, exp_active,
                        exp_active_status, exp_active_modified,
                        exp_reactive_imp, exp_reactive_imp_status,
                        exp_reactive_imp_modified, exp_reactive_exp,
                        exp_reactive_exp_status, exp_reactive_exp_modified
                    ) = datum
                    if hh_start_date == dt:
                        datum = next(data, None)
                        row += [
                            imp_active, imp_active_status, imp_active_modified,
                            imp_reactive_imp, imp_reactive_imp_status,
                            imp_reactive_imp_modified, imp_reactive_exp,
                            imp_reactive_exp_status, imp_reactive_exp_modified,
                            exp_active, exp_active_status, exp_active_modified,
                            exp_reactive_imp, exp_reactive_imp_status,
                            exp_reactive_imp_modified, exp_reactive_exp,
                            exp_reactive_exp_status, exp_reactive_exp_modified]

                outs.append(csv_str(row))

            if is_zipped:
                zf.writestr(
                    (
                        "hh_data_row_" + str(era.id) + "_" +
                        str(era.imp_mpan_core) + "_" +
                        str(era.exp_mpan_core)).replace(' ', '') + '.csv',
                    titles + ''.join(outs))
            else:
                tmp_file.write(''.join(outs))

            # Avoid a long-running transaction
            sess.rollback()
    except BaseException:
        msg = "Problem " + traceback.format_exc()
        if is_zipped:
            zf.writestr('error.txt', msg)
        else:
            tmp_file.write(msg)
    finally:
        if sess is not None:
            sess.close()
        if is_zipped:
            zf.close()
        else:
            tmp_file.close()
        os.rename(running_name, finished_name)


def do_post(sess):
    start_date = req_date('start')
    finish_date = req_date('finish')
    supply_id = req_int('supply_id') if 'supply_id' in request.values else None

    if 'mpan_cores' in request.values:
        mpan_cores_str = req_str('mpan_cores')
        mpan_cores = mpan_cores_str.splitlines()
        if len(mpan_cores) == 0:
            mpan_cores = None
        else:
            for i in range(len(mpan_cores)):
                mpan_cores[i] = parse_mpan_core(mpan_cores[i])
    else:
        mpan_cores = None

    if finish_date < start_date:
        raise BadRequest("The finish date can't be before the start date.")

    is_zipped = req_bool('is_zipped')
    user = g.user

    threading.Thread(
        target=content, args=(
            start_date, finish_date, supply_id, mpan_cores, is_zipped, user)
        ).start()
    return chellow_redirect("/downloads", 303)
