from datetime import datetime as Datetime
import os
import traceback
import threading
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import joinedload
import chellow.computer
import chellow.dloads
import sys
from chellow.models import Era, Bill, Session, Site
from chellow.utils import hh_after, hh_format, HH, req_int
from flask import request, g
from chellow.views import chellow_redirect


def process_site(
        sess, site, month_start, month_finish, forecast_date, tmp_file,
        start_date, finish_date, caches):
    site_code = site.code
    associates = []
    sources = set()
    generator_types = set()
    metering_type = 'no-supply'
    problem = ''
    month_data = {}

    for stream_name in [
            'import-net', 'export-net', 'import-gen', 'export-gen',
            'import-3rd-party', 'export-3rd-party', 'msp', 'used',
            'used-3rd-party']:
        month_data[stream_name + '-kwh'] = 0
        month_data[stream_name + '-gbp'] = 0

    billed_gbp = 0
    billed_kwh = 0

    for group in site.groups(sess, month_start, month_finish, False):
        for cand_site in group.sites:
            cand_site_code = cand_site.code
            if cand_site_code != site_code and \
                    cand_site_code not in associates:
                associates.append(cand_site_code)
        for cand_supply in group.supplies:
            sources.add(cand_supply.source.code)
            if cand_supply.generator_type is not None:
                generator_types.add(cand_supply.generator_type.code)
            for cand_era in cand_supply.find_eras(
                    sess, group.start_date, group.finish_date):
                if metering_type != 'hh':
                    if cand_era.pc.code == '00':
                        metering_type = 'hh'
                    elif metering_type != 'amr':
                        if len(cand_era.channels) > 0:
                            metering_type = 'amr'
                        elif metering_type != 'nhh':
                            if cand_era.mtc.meter_type.code not in [
                                    'UM', 'PH']:
                                metering_type = 'nhh'
                            else:
                                metering_type = 'unmetered'

    for group in site.groups(sess, month_start, month_finish, True):
        if group.start_date > start_date:
            chunk_start = group.start_date
        else:
            chunk_start = start_date

        if group.finish_date > finish_date:
            chunk_finish = finish_date
        else:
            chunk_finish = group.finish_date

        for supply in group.supplies:
            source_code = supply.source.code

            for era in sess.query(Era).filter(
                    Era.supply == supply, Era.start_date <= chunk_finish,
                    or_(
                        Era.finish_date == null(),
                        Era.finish_date >= chunk_start)).options(
                            joinedload(Era.mop_contract),
                            joinedload(Era.hhdc_contract),
                            joinedload(Era.imp_supplier_contract),
                            joinedload(Era.exp_supplier_contract)):
                tmp_file.write(' ')

                # GBP

                if era.start_date > chunk_start:
                    bill_start = era.start_date
                else:
                    bill_start = chunk_start
                if hh_after(era.finish_date, chunk_finish):
                    bill_finish = chunk_finish
                else:
                    bill_finish = era.finish_date

                supply_source = None
                supplier_contract = era.imp_supplier_contract
                if supplier_contract is not None:
                    supply_source = chellow.computer.SupplySource(
                        sess, bill_start, bill_finish, forecast_date, era,
                        True, tmp_file, caches)
                    if supply_source.measurement_type not in ['hh', 'amr']:
                        kwh = sum(
                            hh['msp-kwh'] for hh in supply_source.hh_data)
                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-kwh'] += kwh
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-kwh'] += kwh

                    import_vb_function = chellow.computer.contract_func(
                        caches, supplier_contract, 'virtual_bill', tmp_file)
                    if import_vb_function is None:
                        problem += "Can't find the virtual_bill function in " \
                            "the supplier contract. "
                    else:
                        import_vb_function(supply_source)
                        v_bill = supply_source.supplier_bill

                        if 'problem' in v_bill and len(v_bill['problem']) > 0:
                            problem += 'Supplier Problem: ' + v_bill['problem']

                        try:
                            gbp = v_bill['net-gbp']
                        except KeyError:
                            problem += 'For the supply ' + \
                                supply_source.mpan_core + \
                                ' the virtual bill ' + str(v_bill) + \
                                ' from the contract ' + \
                                supplier_contract.getName() + \
                                ' does not contain the net-gbp key.'
                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-gbp'] += gbp
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-gbp'] += gbp

                if supply_source is None:
                    supply_source = chellow.computer.SupplySource(
                        sess, bill_start, bill_finish, forecast_date, era,
                        False, tmp_file, caches)
                dc_contract = era.hhdc_contract
                supply_source.contract_func(
                    dc_contract, 'virtual_bill')(supply_source)
                dc_bill = supply_source.dc_bill
                dc_gbp = dc_bill['net-gbp']
                if 'problem' in dc_bill and len(dc_bill['problem']) > 0:
                    problem += 'DC Problem: ' + dc_bill['problem']

                mop_contract = era.mop_contract
                mop_bill_function = supply_source.contract_func(
                    mop_contract, 'virtual_bill')
                mop_bill_function(supply_source)
                mop_bill = supply_source.mop_bill
                mop_gbp = mop_bill['net-gbp']
                if 'problem' in mop_bill and len(mop_bill['problem']) > 0:
                    problem += 'MOP Problem: ' + mop_bill['problem']

                if source_code in ('3rd-party', '3rd-party-reverse'):
                    month_data['import-3rd-party-gbp'] += dc_gbp + mop_gbp
                else:
                    month_data['import-net-gbp'] += dc_gbp + mop_gbp

            for bill in sess.query(Bill).filter(
                    Bill.supply == supply, Bill.start_date <= chunk_finish,
                    Bill.finish_date >= chunk_start):
                bill_start = bill.start_date
                bill_finish = bill.finish_date
                bill_duration = (bill_finish - bill_start).total_seconds() + \
                    (30 * 60)
                overlap_duration = (
                    min(bill_finish, chunk_finish) -
                    max(bill_start, chunk_start)).total_seconds() + (30 * 60)
                overlap_proportion = float(overlap_duration) / bill_duration
                billed_gbp += overlap_proportion * float(bill.net)
                billed_kwh += overlap_proportion * float(bill.kwh)

        displaced_era = chellow.computer.displaced_era(
            sess, group, chunk_start, chunk_finish)
        site_ds = chellow.computer.SiteSource(
            sess, site, chunk_start, chunk_finish, forecast_date, tmp_file,
            caches, displaced_era)
        if displaced_era is not None:
            chellow.computer.contract_func(
                caches, displaced_era.imp_supplier_contract,
                'displaced_virtual_bill', tmp_file)(site_ds)
            month_data['msp-gbp'] += site_ds.supplier_bill['net-gbp']

        for stream_name in (
                'import-3rd-party', 'export-3rd-party', 'import-net',
                'export-net', 'import-gen', 'export-gen', 'msp'):
            name = stream_name + '-kwh'
            month_data[name] += sum(hh[name] for hh in site_ds.hh_data)

    month_data['used-3rd-party-kwh'] = \
        month_data['import-3rd-party-kwh'] - \
        month_data['export-3rd-party-kwh']
    month_data['used-3rd-party-gbp'] = month_data['import-3rd-party-gbp']
    month_data['used-gbp'] += \
        month_data['import-net-gbp'] + month_data['msp-gbp'] + \
        month_data['used-3rd-party-gbp']

    month_data['used-kwh'] += month_data['msp-kwh'] + \
        month_data['used-3rd-party-kwh'] + month_data['import-net-kwh']

    result = [
        site.code, site.name, ','.join(associates),
        ','.join(sorted(list(sources))),
        '.'.join(sorted(list(generator_types))),
        hh_format(month_finish), month_data['import-net-kwh'],
        month_data['msp-kwh'], month_data['export-net-kwh'],
        month_data['used-kwh'], month_data['export-gen-kwh'],
        month_data['import-gen-kwh'], month_data['import-3rd-party-kwh'],
        month_data['export-3rd-party-kwh'], month_data['import-net-gbp'],
        month_data['msp-gbp'], 0, month_data['used-gbp'],
        month_data['used-3rd-party-gbp'], billed_kwh, billed_gbp,
        metering_type, problem]
    return result


def long_process(start_date, finish_date, st_id, months, year, month, user):
    caches = {}
    sess = None
    tmp_file = None
    try:
        sess = Session()
        if st_id is None:
            st = None
            base_name = "site_monthly_duration_for_all_site_for_" + \
                str(months) + "_to_" + str(year) + "_" + str(month) + ".csv"
        else:
            st = Site.get_by_id(sess, st_id)
            base_name = "site_monthly_duration_for_" + st.code + "_" + \
                str(months) + "_to_" + str(year) + "_" + str(month) + ".csv"
        running_name, finished_name = chellow.dloads.make_names(
            base_name, user)
        tmp_file = open(running_name, "w")

        forecast_date = chellow.computer.forecast_date()

        tmp_file.write(
            "Site Id,Site Name,Associated Site Ids,Sources,"
            "Generator Types,Month,Metered Imported kWh,"
            "Metered Displaced kWh,Metered Exported kWh,Metered Used kWh,"
            "Metered Parasitic kWh,Metered Generated kWh,"
            "Metered 3rd Party Import kWh,Metered 3rd Party Export kWh,"
            "Metered Imported GBP,Metered Displaced GBP,Metered Exported GBP,"
            "Metered Used GBP,Metered 3rd Party Import GBP,"
            "Billed Imported kWh,Billed Imported GBP,Metering Type,Problem")

        for i in range(months):
            sites = sess.query(Site).order_by(Site.code)
            if st is not None:
                sites = sites.filter(Site.id == st.id)
            for site in sites:
                month_start = start_date + relativedelta(months=i)
                month_finish = month_start + relativedelta(months=1) - HH
                tmp_file.write(
                    '\r\n' + ','.join(
                        '"' + str(value) + '"' for value in process_site(
                            sess, site, month_start, month_finish,
                            forecast_date, tmp_file, start_date, finish_date,
                            caches)))
                tmp_file.flush()

    except:
        msg = traceback.format_exc()
        sys.stderr.write(msg + '\n')
        tmp_file.write("Problem " + msg)
    finally:
        try:
            if sess is not None:
                sess.close()
        except:
            tmp_file.write("\nProblem closing session.")
        finally:
            tmp_file.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    year = req_int("finish_year")
    month = req_int("finish_month")
    months = req_int("months")

    st_id = req_int('site_id') if 'site_id' in request.values else None

    finish_date = Datetime(year, month, 1, tzinfo=pytz.utc) + \
        relativedelta(months=1) - HH
    start_date = Datetime(year, month, 1, tzinfo=pytz.utc) - \
        relativedelta(months=months-1)
    user = g.user
    threading.Thread(
        target=long_process, args=(
            start_date, finish_date, st_id, months, year, month, user)).start()
    return chellow_redirect("/downloads", 303)
