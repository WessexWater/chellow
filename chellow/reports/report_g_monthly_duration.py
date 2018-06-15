import os
import traceback
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, true
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import joinedload
from chellow.models import (
    Session, GContract, Site, GEra, SiteGEra, GSupply, GBill)
from chellow.computer import contract_func
from chellow.g_engine import GDataSource
import chellow.computer
import chellow.dloads
import threading
import odio
import sys
from werkzeug.exceptions import BadRequest
from chellow.utils import (
    hh_format, HH, hh_max, hh_min, req_int, req_bool, make_val,
    utc_datetime_now, utc_datetime)
from flask import request, g
from chellow.views import chellow_redirect


CATEGORY_ORDER = {None: 0, 'unmetered': 1, 'nhh': 2, 'amr': 3, 'hh': 4}
meter_order = {'hh': 0, 'amr': 1, 'nhh': 2, 'unmetered': 3}


def write_spreadsheet(fl, compressed, site_rows, era_rows):
    fl.seek(0)
    fl.truncate()
    with odio.create_spreadsheet(fl, '1.2', compressed=compressed) as f:
        f.append_table("Site Level", site_rows)
        f.append_table("Era Level", era_rows)


def content(
        base_name, site_id, g_supply_id, user, compression, start_date,
        months):
    now = utc_datetime_now()
    report_context = {}
    sess = None

    try:
        sess = Session()
        base_name.append(
            hh_format(start_date).replace(' ', '_').replace(':', '').
            replace('-', ''))

        base_name.append('for')
        base_name.append(str(months))
        base_name.append('months')
        finish_date = start_date + relativedelta(months=months)

        forecast_from = chellow.computer.forecast_date()

        sites = sess.query(Site).distinct().order_by(Site.code)
        if site_id is not None:
            site = Site.get_by_id(sess, site_id)
            sites = sites.filter(Site.id == site.id)
            base_name.append('site')
            base_name.append(site.code)
        if g_supply_id is not None:
            g_supply = GSupply.get_by_id(sess, g_supply_id)
            base_name.append('g_supply')
            base_name.append(str(g_supply.id))
            sites = sites.join(SiteGEra).join(GEra).filter(
                GEra.g_supply == g_supply)

        running_name, finished_name = chellow.dloads.make_names(
            '_'.join(base_name) + '.ods', user)

        rf = open(running_name, "wb")
        site_rows = []
        g_era_rows = []

        era_header_titles = [
            'creation_date', 'mprn', 'supply_name', 'exit_zone', 'msn',
            'is_corrected', 'unit', 'contract', 'site_id', 'site_name',
            'associated_site_ids', 'month']
        site_header_titles = [
            'creation_date', 'site_id', 'site_name', 'associated_site_ids',
            'month']
        summary_titles = ['kwh', 'gbp', 'billed_kwh', 'billed_gbp']

        vb_titles = []
        conts = sess.query(GContract).join(GEra).join(GSupply).filter(
            GEra.start_date <= finish_date, or_(
                GEra.finish_date == null(),
                GEra.finish_date >= start_date)).distinct().order_by(
            GContract.id)
        if g_supply_id is not None:
            conts = conts.filter(GEra.g_supply_id == g_supply_id)
        for cont in conts:
            title_func = chellow.computer.contract_func(
                report_context, cont, 'virtual_bill_titles')
            if title_func is None:
                raise Exception(
                    "For the contract " + cont.name + " there doesn't seem " +
                    "to be a 'virtual_bill_titles' function.")
            for title in title_func():
                if title not in vb_titles:
                    vb_titles.append(title)

        g_era_rows.append(era_header_titles + summary_titles + vb_titles)
        site_rows.append(site_header_titles + summary_titles)

        sites = sites.all()
        month_start = start_date
        while month_start < finish_date:
            month_finish = month_start + relativedelta(months=1) - HH
            for site in sites:
                site_kwh = site_gbp = site_billed_kwh = site_billed_gbp = 0
                for g_era in sess.query(GEra).join(SiteGEra).filter(
                        SiteGEra.site == site, SiteGEra.is_physical == true(),
                        GEra.start_date <= month_finish, or_(
                            GEra.finish_date == null(),
                            GEra.finish_date >= month_start)).options(
                        joinedload(GEra.g_contract),
                        joinedload(GEra.g_supply),
                        joinedload(GEra.g_supply).joinedload(
                            GSupply.g_exit_zone)).order_by(GEra.id):

                    g_supply = g_era.g_supply

                    if g_supply_id is not None and g_supply.id != g_supply_id:
                        continue

                    ss_start = hh_max(g_era.start_date, month_start)
                    ss_finish = hh_min(g_era.finish_date, month_finish)

                    ss = GDataSource(
                        sess, ss_start, ss_finish, forecast_from, g_era,
                        report_context, None)

                    contract = g_era.g_contract
                    vb_function = contract_func(
                        report_context, contract, 'virtual_bill')
                    if vb_function is None:
                        raise BadRequest(
                            "The contract " + contract.name +
                            " doesn't have the virtual_bill() function.")
                    vb_function(ss)
                    bill = ss.bill

                    try:
                        gbp = bill['net_gbp']
                    except KeyError:
                        gbp = 0
                        bill['problem'] += 'For the supply ' + ss.mprn + \
                            ' the virtual bill ' + str(bill) + \
                            ' from the contract ' + contract.name + \
                            ' does not contain the net_gbp key.'
                    try:
                        kwh = bill['kwh']
                    except KeyError:
                        kwh = 0
                        bill['problem'] += "For the supply " + ss.mprn + \
                            " the virtual bill " + str(bill) + \
                            " from the contract " + contract.name + \
                            " does not contain the 'kwh' key."

                    billed_kwh = billed_gbp = 0

                    g_era_associates = {
                        s.site.code for s in g_era.site_g_eras
                        if not s.is_physical}

                    for g_bill in sess.query(GBill).filter(
                            GBill.g_supply == g_supply,
                            GBill.start_date <= ss_finish,
                            GBill.finish_date >= ss_start):
                        bill_start = g_bill.start_date
                        bill_finish = g_bill.finish_date
                        bill_duration = (
                            bill_finish - bill_start).total_seconds() + \
                            (30 * 60)
                        overlap_duration = (
                            min(bill_finish, ss_finish) -
                            max(bill_start, ss_start)
                            ).total_seconds() + (30 * 60)
                        overlap_proportion = overlap_duration / bill_duration
                        billed_kwh += overlap_proportion * float(g_bill.kwh)
                        billed_gbp += overlap_proportion * float(g_bill.net)

                    associated_site_ids = ','.join(sorted(g_era_associates))
                    g_era_rows.append(
                        [
                            now, g_supply.mprn, g_supply.name,
                            g_supply.g_exit_zone.code, g_era.msn,
                            g_era.is_corrected, g_era.g_unit.code,
                            contract.name, site.code, site.name,
                            associated_site_ids, month_finish, kwh, gbp,
                            billed_kwh, billed_gbp, None] +
                        [make_val(bill.get(t)) for t in vb_titles])

                    site_kwh += kwh
                    site_gbp += gbp
                    site_billed_kwh += billed_kwh
                    site_billed_gbp += billed_gbp

                linked_sites = ', '.join(
                    s.code for s in site.find_linked_sites(
                        sess, month_start, month_finish))

                site_rows.append(
                    [
                        now, site.code, site.name, linked_sites,
                        month_finish, site_kwh, site_gbp, site_billed_kwh,
                        site_billed_gbp])
                sess.rollback()
            write_spreadsheet(rf, compression, site_rows, g_era_rows)
            month_start += relativedelta(months=1)
    except BadRequest as e:
        msg = e.description + traceback.format_exc()
        sys.stderr.write(msg + '\n')
        site_rows.append(["Problem " + msg])
        write_spreadsheet(rf, compression, site_rows, g_era_rows)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + '\n')
        site_rows.append(["Problem " + msg])
        write_spreadsheet(rf, compression, site_rows, g_era_rows)
    finally:
        if sess is not None:
            sess.close()
        try:
            rf.close()
            os.rename(running_name, finished_name)
        except BaseException:
            msg = traceback.format_exc()
            r_name, f_name = chellow.dloads.make_names('error.txt', user)
            ef = open(r_name, "w")
            ef.write(msg + '\n')
            ef.close()


def do_get(sess):
    base_name = []
    year = req_int("finish_year")
    month = req_int("finish_month")
    months = req_int("months")
    start_date = utc_datetime(year, month, 1) - relativedelta(
        months=months - 1)
    base_name.append('g_monthly_duration')

    site_id = req_int('site_id') if 'site_id' in request.values else None

    if 'g_supply_id' in request.values:
        g_supply_id = req_int('g_supply_id')
    else:
        g_supply_id = None

    if 'compression' in request.values:
        compression = req_bool('compression')
    else:
        compression = True

    user = g.user

    threading.Thread(
        target=content, args=(
            base_name, site_id, g_supply_id, user, compression, start_date,
            months)).start()
    return chellow_redirect("/downloads", 303)