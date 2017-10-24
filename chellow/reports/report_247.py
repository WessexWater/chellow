import importlib
import os
from datetime import datetime as Datetime
import traceback
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, true
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import joinedload
from collections import defaultdict
from chellow.models import (
    Session, Contract, Site, Era, SiteEra, Supply, Source, Bill, Mtc, Llfc,
    MeasurementRequirement, Ssc, Tpr)
from chellow.computer import SupplySource, contract_func
import chellow.computer
import csv
import chellow.dloads
import io
import threading
import odio
import sys
from werkzeug.exceptions import BadRequest
from chellow.utils import (
    hh_format, HH, hh_before, req_int, req_bool, make_val, utc_datetime_now,
    to_utc, utc_datetime)
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


def make_bill_row(titles, bill):
    return [make_val(bill.get(t)) for t in titles]


def content(
        scenario_props, scenario_id, base_name, site_id, supply_id, user,
        compression):
    now = utc_datetime_now()
    report_context = {}
    future_funcs = {}
    report_context['future_funcs'] = future_funcs

    sess = None
    try:
        sess = Session()
        if scenario_props is None:
            scenario_contract = Contract.get_supplier_by_id(sess, scenario_id)
            scenario_props = scenario_contract.make_properties()
            base_name.append(scenario_contract.name)

        for cname, cprops in scenario_props.get('rates', {}).items():
            try:
                rate_start = cprops['start_date']
            except KeyError:
                raise BadRequest(
                    "In " + scenario_contract.name + " for the rate " +
                    cname + " the start_date is missing.")

            if rate_start is not None:
                rate_start = to_utc(rate_start)

            lib = importlib.import_module('chellow.' + cname)

            if hasattr(lib, 'create_future_func'):
                future_funcs[cname] = {
                    'start_date': rate_start,
                    'func': lib.create_future_func(
                        cprops['multiplier'], cprops['constant'])}

        era_maps = scenario_props.get('era_maps', {})

        start_date = scenario_props['scenario_start']
        if start_date is None:
            start_date = utc_datetime(now.year, now.month, 1)
        else:
            start_date = to_utc(start_date)

        base_name.append(
            hh_format(start_date).replace(' ', '_').replace(':', '').
            replace('-', ''))
        months = scenario_props['scenario_duration']
        base_name.append('for')
        base_name.append(str(months))
        base_name.append('months')
        finish_date = start_date + relativedelta(months=months)

        if 'kwh_start' in scenario_props:
            kwh_start = scenario_props['kwh_start']
        else:
            kwh_start = None

        if kwh_start is None:
            kwh_start = chellow.computer.forecast_date()
        else:
            kwh_start = to_utc(kwh_start)

        sites = sess.query(Site).distinct().order_by(Site.code)
        if site_id is not None:
            site = Site.get_by_id(sess, site_id)
            sites = sites.filter(Site.id == site.id)
            base_name.append('site')
            base_name.append(site.code)
        if supply_id is not None:
            supply = Supply.get_by_id(sess, supply_id)
            base_name.append('supply')
            base_name.append(str(supply.id))
            sites = sites.join(SiteEra).join(Era).filter(Era.supply == supply)

        running_name, finished_name = chellow.dloads.make_names(
            '_'.join(base_name) + '.ods', user)

        rf = open(running_name, "wb")
        site_rows = []
        era_rows = []
        changes = defaultdict(list, {})

        try:
            kw_changes = scenario_props['kw_changes']
        except KeyError:
            kw_changes = ''

        for row in csv.reader(io.StringIO(kw_changes)):
            if len(''.join(row).strip()) == 0:
                continue
            if len(row) != 4:
                raise BadRequest(
                    "Can't interpret the row " + str(row) + " it should be of "
                    "the form SITE_CODE, USED / GENERATED, DATE, MULTIPLIER")
            site_code, typ, date_str, kw_str = row
            date = to_utc(Datetime.strptime(date_str.strip(), "%Y-%m-%d"))
            changes[site_code.strip()].append(
                {
                    'type': typ.strip(), 'date': date,
                    'multiplier': float(kw_str)})

        era_header_titles = [
            'creation-date', 'imp-mpan-core', 'imp-supplier-contract',
            'exp-mpan-core', 'exp-supplier-contract', 'metering-type',
            'source', 'generator-type', 'supply-name', 'msn', 'pc', 'site-id',
            'site-name', 'associated-site-ids', 'month']
        site_header_titles = [
            'creation-date', 'site-id', 'site-name', 'associated-site-ids',
            'month', 'metering-type', 'sources', 'generator-types']
        summary_titles = [
            'import-net-kwh', 'export-net-kwh', 'import-gen-kwh',
            'export-gen-kwh', 'import-3rd-party-kwh', 'export-3rd-party-kwh',
            'displaced-kwh', 'used-kwh', 'used-3rd-party-kwh',
            'import-net-gbp', 'export-net-gbp', 'import-gen-gbp',
            'export-gen-gbp', 'import-3rd-party-gbp', 'export-3rd-party-gbp',
            'displaced-gbp', 'used-gbp', 'used-3rd-party-gbp',
            'billed-import-net-kwh', 'billed-import-net-gbp']

        title_dict = {}
        for cont_type, con_attr in (
                ('mop', Era.mop_contract), ('dc', Era.hhdc_contract),
                ('imp-supplier', Era.imp_supplier_contract),
                ('exp-supplier', Era.exp_supplier_contract)):
            titles = []
            title_dict[cont_type] = titles
            conts = sess.query(Contract).join(con_attr).join(Era.supply). \
                join(Source).filter(
                    Era.start_date <= finish_date, or_(
                        Era.finish_date == null(),
                        Era.finish_date >= start_date),
                    Source.code.in_(('net', '3rd-party'))
                ).distinct().order_by(Contract.id)
            if supply_id is not None:
                conts = conts.filter(Era.supply_id == supply_id)
            for cont in conts:
                title_func = chellow.computer.contract_func(
                    report_context, cont, 'virtual_bill_titles')
                if title_func is None:
                    raise Exception(
                        "For the contract " + cont.name +
                        " there doesn't seem to be a "
                        "'virtual_bill_titles' function.")
                for title in title_func():
                    if title not in titles:
                        titles.append(title)

        tpr_query = sess.query(Tpr).join(MeasurementRequirement).join(Ssc). \
            join(Era).filter(
                Era.start_date <= finish_date, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= start_date)
            ).order_by(Tpr.code).distinct()
        for tpr in tpr_query.filter(Era.imp_supplier_contract != null()):
            for suffix in ('-kwh', '-rate', '-gbp'):
                title_dict['imp-supplier'].append(tpr.code + suffix)
        for tpr in tpr_query.filter(Era.exp_supplier_contract != null()):
            for suffix in ('-kwh', '-rate', '-gbp'):
                title_dict['exp-supplier'].append(tpr.code + suffix)

        era_rows.append(
            era_header_titles + summary_titles + [None] +
            ['mop-' + t for t in title_dict['mop']] +
            [None] + ['dc-' + t for t in title_dict['dc']] + [None] +
            ['imp-supplier-' + t for t in title_dict['imp-supplier']] +
            [None] + ['exp-supplier-' + t for t in title_dict['exp-supplier']])
        site_rows.append(site_header_titles + summary_titles)

        sites = sites.all()
        month_start = start_date
        while month_start < finish_date:
            month_finish = month_start + relativedelta(months=1) - HH
            for site in sites:
                site_changes = changes[site.code]

                site_category = None
                site_sources = set()
                site_gen_types = set()
                site_month_data = defaultdict(int)
                calcs = []
                deltas = defaultdict(int)
                for era in sess.query(Era).join(SiteEra).filter(
                        SiteEra.site == site, SiteEra.is_physical == true(),
                        Era.start_date <= month_finish, or_(
                            Era.finish_date == null(),
                            Era.finish_date >= month_start)).options(
                        joinedload(Era.ssc),
                        joinedload(Era.hhdc_contract),
                        joinedload(Era.mop_contract),
                        joinedload(Era.imp_supplier_contract),
                        joinedload(Era.exp_supplier_contract),
                        joinedload(Era.channels),
                        joinedload(Era.imp_llfc).joinedload(
                            Llfc.voltage_level),
                        joinedload(Era.exp_llfc).joinedload(
                            Llfc.voltage_level),
                        joinedload(Era.cop),
                        joinedload(Era.supply).joinedload(Supply.dno),
                        joinedload(Era.supply).joinedload(Supply.gsp_group),
                        joinedload(Era.mtc).joinedload(Mtc.meter_type),
                        joinedload(Era.pc), joinedload(Era.site_eras)):

                    supply = era.supply
                    if supply.generator_type is not None:
                        site_gen_types.add(supply.generator_type.code)

                    if supply_id is not None and supply.id != supply_id:
                        continue

                    if era.start_date > month_start:
                        ss_start = era.start_date
                    else:
                        ss_start = month_start

                    if hh_before(era.finish_date, month_finish):
                        ss_finish = era.finish_date
                    else:
                        ss_finish = month_finish

                    if era.imp_mpan_core is None:
                        imp_ss = None
                    else:
                        imp_ss = SupplySource(
                            sess, ss_start, ss_finish, kwh_start, era, True,
                            report_context, era_maps=era_maps)

                    if era.exp_mpan_core is None:
                        exp_ss = None
                        measurement_type = imp_ss.measurement_type
                    else:
                        exp_ss = SupplySource(
                            sess, ss_start, ss_finish, kwh_start, era, False,
                            report_context, era_maps=era_maps)
                        measurement_type = exp_ss.measurement_type

                    order = meter_order[measurement_type]
                    calcs.append(
                        (
                            order, era.imp_mpan_core, era.exp_mpan_core,
                            imp_ss, exp_ss))

                    if imp_ss is not None and len(era.channels) == 0:
                        for hh in imp_ss.hh_data:
                            deltas[hh['start-date']] += hh['msp-kwh']

                imp_net_delts = defaultdict(int)
                exp_net_delts = defaultdict(int)
                imp_gen_delts = defaultdict(int)

                displaced_era = chellow.computer.displaced_era(
                    sess, report_context, site, month_start, month_finish,
                    kwh_start)
                site_ds = chellow.computer.SiteSource(
                    sess, site, month_start, month_finish, kwh_start,
                    report_context, displaced_era)

                for hh in site_ds.hh_data:
                    try:
                        delta = deltas[hh['start-date']]
                        hh['import-net-kwh'] += delta
                        hh['used-kwh'] += delta
                    except KeyError:
                        pass

                for hh in site_ds.hh_data:
                    for change in site_changes:
                        if change['type'] == 'used' and \
                                change['date'] <= hh['start-date']:
                            used = change['multiplier'] * hh['used-kwh']
                            exp_net = max(
                                0, hh['import-gen-kwh'] -
                                hh['export-gen-kwh'] - used)
                            exp_net_delt = exp_net - hh['export-net-kwh']
                            exp_net_delts[hh['start-date']] += exp_net_delt
                            displaced = hh['import-gen-kwh'] - \
                                hh['export-gen-kwh'] - exp_net
                            imp_net = used - displaced
                            imp_delt = imp_net - hh['import-net-kwh']
                            imp_net_delts[hh['start-date']] += imp_delt

                            hh['import-net-kwh'] = imp_net
                            hh['used-kwh'] = used
                            hh['export-net-kwh'] = exp_net
                            hh['msp-kwh'] = displaced
                        elif change['type'] == 'generated' and \
                                change['date'] <= hh['start-date']:
                            imp_gen = change['multiplier'] * \
                                hh['import-gen-kwh']
                            imp_gen_delt = imp_gen - hh['import-gen-kwh']
                            exp_net = max(
                                0, imp_gen - hh['export-gen-kwh'] -
                                hh['used-kwh'])
                            exp_net_delt = exp_net - hh['export-net-kwh']
                            exp_net_delts[hh['start-date']] += exp_net_delt

                            displaced = imp_gen - hh['export-gen-kwh'] - \
                                exp_net

                            imp_net = hh['used-kwh'] - displaced
                            imp_net_delt = imp_net - hh['import-net-kwh']
                            imp_net_delts[hh['start-date']] += imp_net_delt

                            imp_gen_delts[hh['start-date']] += imp_gen_delt

                            hh['import-net-kwh'] = imp_net
                            hh['export-net-kwh'] = exp_net
                            hh['import-gen-kwh'] = imp_gen
                            hh['msp-kwh'] = displaced

                if displaced_era is not None and supply_id is None:
                    month_data = {}
                    for sname in (
                            'import-net', 'export-net', 'import-gen',
                            'export-gen', 'import-3rd-party',
                            'export-3rd-party', 'msp', 'used',
                            'used-3rd-party', 'billed-import-net'):
                        for xname in ('kwh', 'gbp'):
                            month_data[sname + '-' + xname] = 0

                    month_data['used-kwh'] = \
                        month_data['displaced-kwh'] = \
                        sum(hh['msp-kwh'] for hh in site_ds.hh_data)

                    disp_supplier_contract = \
                        displaced_era.imp_supplier_contract
                    disp_vb_function = chellow.computer.contract_func(
                        report_context, disp_supplier_contract,
                        'displaced_virtual_bill')
                    if disp_vb_function is None:
                        raise BadRequest(
                            "The supplier contract " +
                            disp_supplier_contract.name +
                            " doesn't have the displaced_virtual_bill() "
                            "function.")
                    disp_vb_function(site_ds)
                    disp_supplier_bill = site_ds.supplier_bill

                    try:
                        gbp = disp_supplier_bill['net-gbp']
                    except KeyError:
                        disp_supplier_bill['problem'] += 'For the supply ' + \
                            site_ds.mpan_core + ' the virtual bill ' + \
                            str(disp_supplier_bill) + ' from the contract ' + \
                            disp_supplier_contract.name + \
                            ' does not contain the net-gbp key.'

                    month_data['used-gbp'] = month_data['displaced-gbp'] = \
                        site_ds.supplier_bill['net-gbp']

                    out = [
                        now, None, disp_supplier_contract.name, None, None,
                        displaced_era.make_meter_category(), 'displaced', None,
                        None, None, None, site.code, site.name, '',
                        month_finish] + [
                            month_data[t] for t in summary_titles] + [None] + [
                        None] * len(title_dict['mop']) + [None] + [
                        None] * len(title_dict['dc']) + [None] + make_bill_row(
                            title_dict['imp-supplier'], disp_supplier_bill)

                    era_rows.append(out)
                    for k, v in month_data.items():
                        site_month_data[k] += v

                for i, (
                        order, imp_mpan_core, exp_mpan_core, imp_ss,
                        exp_ss) in enumerate(sorted(calcs, key=str)):
                    if imp_ss is None:
                        era = exp_ss.era
                    else:
                        era = imp_ss.era
                    supply = era.supply
                    source = supply.source
                    source_code = source.code
                    site_sources.add(source_code)
                    month_data = {}
                    for name in (
                            'import-net', 'export-net', 'import-gen',
                            'export-gen', 'import-3rd-party',
                            'export-3rd-party', 'displaced', 'used',
                            'used-3rd-party', 'billed-import-net'):
                        for sname in ('kwh', 'gbp'):
                            month_data[name + '-' + sname] = 0

                    if source_code == 'net':
                        delts = imp_net_delts
                    elif source_code == 'gen':
                        delts = imp_gen_delts
                    else:
                        delts = []

                    if len(delts) > 0 and imp_ss is not None:
                        for hh in imp_ss.hh_data:
                            diff = hh['msp-kwh'] + delts[hh['start-date']]
                            if diff < 0:
                                hh['msp-kwh'] = 0
                                hh['msp-kw'] = 0
                                delts[hh['start-date']] -= hh['msp-kwh']
                            else:
                                hh['msp-kwh'] += delts[hh['start-date']]
                                hh['msp-kw'] += hh['msp-kwh'] / 2
                                del delts[hh['start-date']]

                        left_kwh = sum(delts.values())
                        if left_kwh > 0:
                            first_hh = imp_ss.hh_data[0]
                            first_hh['msp-kwh'] += left_kwh
                            first_hh['msp-kw'] += left_kwh / 2

                    imp_supplier_contract = era.imp_supplier_contract
                    if imp_supplier_contract is not None:
                        kwh = sum(hh['msp-kwh'] for hh in imp_ss.hh_data)
                        import_vb_function = contract_func(
                            report_context, imp_supplier_contract,
                            'virtual_bill')
                        if import_vb_function is None:
                            raise BadRequest(
                                "The supplier contract " +
                                imp_supplier_contract.name +
                                " doesn't have the virtual_bill() "
                                "function.")
                        import_vb_function(imp_ss)
                        imp_supplier_bill = imp_ss.supplier_bill

                        try:
                            gbp = imp_supplier_bill['net-gbp']
                        except KeyError:
                            gbp = 0
                            imp_supplier_bill['problem'] += \
                                'For the supply ' + \
                                imp_ss.mpan_core + \
                                ' the virtual bill ' + \
                                str(imp_supplier_bill) + \
                                ' from the contract ' + \
                                imp_supplier_contract.name + \
                                ' does not contain the net-gbp key.'

                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-gbp'] += gbp
                            month_data['import-net-kwh'] += kwh
                            month_data['used-gbp'] += gbp
                            month_data['used-kwh'] += kwh
                            if source_code == 'gen-net':
                                month_data['export-gen-kwh'] += kwh
                        elif source_code == '3rd-party':
                            month_data['import-3rd-party-gbp'] += gbp
                            month_data['import-3rd-party-kwh'] += kwh
                            month_data['used-3rd-party-gbp'] += gbp
                            month_data['used-3rd-party-kwh'] += kwh
                            month_data['used-gbp'] += gbp
                            month_data['used-kwh'] += kwh
                        elif source_code == '3rd-party-reverse':
                            month_data['export-3rd-party-gbp'] += gbp
                            month_data['export-3rd-party-kwh'] += kwh
                            month_data['used-3rd-party-gbp'] -= gbp
                            month_data['used-3rd-party-kwh'] -= kwh
                            month_data['used-gbp'] -= gbp
                            month_data['used-kwh'] -= kwh
                        elif source_code == 'gen':
                            month_data['import-gen-kwh'] += kwh

                    exp_supplier_contract = era.exp_supplier_contract
                    if exp_supplier_contract is not None:
                        kwh = sum(hh['msp-kwh'] for hh in exp_ss.hh_data)
                        export_vb_function = contract_func(
                            report_context, exp_supplier_contract,
                            'virtual_bill')
                        export_vb_function(exp_ss)

                        exp_supplier_bill = exp_ss.supplier_bill
                        try:
                            gbp = exp_supplier_bill['net-gbp']
                        except KeyError:
                            exp_supplier_bill['problem'] += \
                                'For the supply ' + imp_ss.mpan_core + \
                                ' the virtual bill ' + \
                                str(imp_supplier_bill) + \
                                ' from the contract ' + \
                                imp_supplier_contract.name + \
                                ' does not contain the net-gbp key.'

                        if source_code in ('net', 'gen-net'):
                            month_data['export-net-gbp'] += gbp
                            month_data['export-net-kwh'] += kwh
                            if source_code == 'gen-net':
                                month_data['import-gen-kwh'] += kwh

                        elif source_code == '3rd-party':
                            month_data['export-3rd-party-gbp'] += gbp
                            month_data['export-3rd-party-kwh'] += kwh
                            month_data['used-3rd-party-gbp'] -= gbp
                            month_data['used-3rd-party-kwh'] -= kwh
                            month_data['used-gbp'] -= gbp
                            month_data['used-kwh'] -= kwh
                        elif source_code == '3rd-party-reverse':
                            month_data['import-3rd-party-gbp'] += gbp
                            month_data['import-3rd-party-kwh'] += kwh
                            month_data['used-3rd-party-gbp'] += gbp
                            month_data['used-3rd-party-kwh'] += kwh
                            month_data['used-gbp'] += gbp
                            month_data['used-kwh'] += kwh
                        elif source_code == 'gen':
                            month_data['export-gen-kwh'] += kwh

                    sss = exp_ss if imp_ss is None else imp_ss
                    dc_contract = era.hhdc_contract
                    sss.contract_func(dc_contract, 'virtual_bill')(sss)
                    dc_bill = sss.dc_bill
                    gbp = dc_bill['net-gbp']

                    mop_contract = era.mop_contract
                    mop_bill_function = sss.contract_func(
                        mop_contract, 'virtual_bill')
                    mop_bill_function(sss)
                    mop_bill = sss.mop_bill
                    gbp += mop_bill['net-gbp']

                    if source_code in ('3rd-party', '3rd-party-reverse'):
                        month_data['import-3rd-party-gbp'] += gbp
                        month_data['used-3rd-party-gbp'] += gbp
                    else:
                        month_data['import-net-gbp'] += gbp
                    month_data['used-gbp'] += gbp

                    if source_code in ('gen', 'gen-net'):
                        generator_type = supply.generator_type.code
                        site_gen_types.add(generator_type)
                    else:
                        generator_type = None

                    era_category = era.make_meter_category()
                    if CATEGORY_ORDER[site_category] < \
                            CATEGORY_ORDER[era_category]:
                        site_category = era_category
                    era_associates = {
                        s.site.code for s in era.site_eras
                        if not s.is_physical}

                    for bill in sess.query(Bill).filter(
                            Bill.supply == supply,
                            Bill.start_date <= sss.finish_date,
                            Bill.finish_date >= sss.start_date):
                        bill_start = bill.start_date
                        bill_finish = bill.finish_date
                        bill_duration = (
                            bill_finish - bill_start).total_seconds() + \
                            (30 * 60)
                        overlap_duration = (
                            min(bill_finish, sss.finish_date) -
                            max(bill_start, sss.start_date)
                            ).total_seconds() + (30 * 60)
                        overlap_proportion = overlap_duration / bill_duration
                        month_data['billed-import-net-kwh'] += \
                            overlap_proportion * float(bill.kwh)
                        month_data['billed-import-net-gbp'] += \
                            overlap_proportion * float(bill.net)

                    out = [
                        now, era.imp_mpan_core, (
                            None if imp_supplier_contract is None else
                            imp_supplier_contract.name),
                        era.exp_mpan_core, (
                            None if exp_supplier_contract is None else
                            exp_supplier_contract.name),
                        era_category, source_code, generator_type, supply.name,
                        era.msn, era.pc.code, site.code, site.name,
                        ','.join(sorted(list(era_associates))),
                        month_finish] + [
                        month_data[t] for t in summary_titles] + [None] + \
                        make_bill_row(title_dict['mop'], mop_bill) + [None] + \
                        make_bill_row(title_dict['dc'], dc_bill)
                    if imp_supplier_contract is None:
                        out += [None] * (len(title_dict['imp-supplier']) + 1)
                    else:
                        out += [None] + make_bill_row(
                            title_dict['imp-supplier'], imp_supplier_bill)
                    if exp_supplier_contract is not None:
                        out += [None] + make_bill_row(
                            title_dict['exp-supplier'], exp_supplier_bill)

                    for k, v in month_data.items():
                        site_month_data[k] += v
                    era_rows.append(out)

                site_rows.append(
                    [
                        now, site.code, site.name, ', '.join(
                            s.code for s in site.find_linked_sites(
                                sess, month_start, month_finish)),
                        month_finish, site_category,
                        ', '.join(sorted(list(site_sources))),
                        ', '.join(sorted(list(site_gen_types)))] +
                    [site_month_data[k] for k in summary_titles])
                sess.rollback()
            write_spreadsheet(rf, compression, site_rows, era_rows)
            month_start += relativedelta(months=1)
    except BadRequest as e:
        msg = e.description + traceback.format_exc()
        sys.stderr.write(msg + '\n')
        site_rows.append(["Problem " + msg])
        write_spreadsheet(rf, compression, site_rows, era_rows)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + '\n')
        site_rows.append(["Problem " + msg])
        write_spreadsheet(rf, compression, site_rows, era_rows)
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

    if 'scenario_id' in request.values:
        scenario_id = req_int('scenario_id')
        scenario_props = None
    else:
        year = req_int("finish_year")
        month = req_int("finish_month")
        months = req_int("months")
        start_date = Datetime(year, month, 1) - \
            relativedelta(months=months - 1)
        scenario_props = {
            'scenario_start': start_date, 'scenario_duration': months}
        scenario_id = None
        base_name.append('monthly_duration')

    site_id = req_int('site_id') if 'site_id' in request.values else None
    supply_id = req_int('supply_id') if 'supply_id' in request.values else None
    if 'compression' in request.values:
        compression = req_bool('compression')
    else:
        compression = True
    user = g.user

    threading.Thread(
        target=content, args=(
            scenario_props, scenario_id, base_name, site_id, supply_id,
            user, compression)).start()
    return chellow_redirect("/downloads", 303)
