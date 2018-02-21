import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import joinedload
from chellow.models import Session, GEra, GSupply
from chellow.utils import hh_format, req_date, req_int
import chellow.dloads
import sys
import os
import threading
from flask import g, request
import csv
from chellow.views import chellow_redirect


def content(running_name, finished_name, date, g_supply_id):
    sess = None
    try:
        sess = Session()
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        writer.writerow(
            (
                'Date', 'Physical Site Id', 'Physical Site Name',
                'Other Site Ids', 'Other Site Names', 'MPRN', 'Exit Zone',
                'Meter Serial Number', 'Is Corrected?', 'Unit', 'Contract',
                'Account', 'Supply Start', 'Supply Finish'))

        g_eras = sess.query(GEra, GSupply).join(GSupply).filter(
            GEra.start_date <= date,
            or_(
                GEra.finish_date == null(),
                GEra.finish_date >= date)).order_by(
            GSupply.mprn).options(joinedload(GEra.site_g_eras))

        if g_supply_id is not None:
            g_supply = GSupply.get_by_id(sess, g_supply_id)

            g_eras = g_eras.filter(GEra.g_supply == g_supply)

        for g_era, g_supply in g_eras:
            site_codes = []
            site_names = []
            for site_g_era in g_era.site_g_eras:
                if site_g_era.is_physical:
                    physical_site = site_g_era.site
                else:
                    site = site_g_era.site
                    site_codes.append(site.code)
                    site_names.append(site.name)

            sup_g_eras = sess.query(GEra).filter(
                GEra.g_supply == g_supply).order_by(GEra.start_date).all()
            g_supply_start_date = sup_g_eras[0].start_date
            g_supply_finish_date = sup_g_eras[-1].finish_date

            is_corrected = 'yes' if g_era.is_corrected else 'no'
            writer.writerow(
                ('' if value is None else str(value)) for value in [
                    hh_format(date), physical_site.code, physical_site.name,
                    ', '.join(site_codes), ', '.join(site_names),
                    g_supply.mprn, g_supply.g_exit_zone.code, g_era.msn,
                    is_corrected, g_era.g_unit.code, g_era.g_contract.name,
                    g_era.account, hh_format(g_supply_start_date),
                    hh_format(g_supply_finish_date, ongoing_str='')])
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(session):
    user = g.user
    date = req_date('date')
    if 'g_supply_id' in request.values:
        g_supply_id = req_int('g_supply_id')
    else:
        g_supply_id = None

    running_name, finished_name = chellow.dloads.make_names(
        'g_supplies_snapshot.csv', user)

    args = (running_name, finished_name, date, g_supply_id)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
