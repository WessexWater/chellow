import os
from net.sf.chellow.monad import Monad
import datetime
import traceback
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, Float
from sqlalchemy.sql.expression import null, false, cast
from sqlalchemy.sql import func
from collections import defaultdict
import db
import utils
import computer
import csv
import dloads
import StringIO
import threading
import odswriter

CATEGORY_ORDER = {
    None: 0, 'unmetered': 1, 'nhh': 2, 'amr': 3, 'hh': 4}


Monad.getUtils()['impt'](
    globals(), 'templater', 'db', 'utils', 'computer', 'bsuos', 'aahedc',
    'ccl', 'system_price_bmreports', 'system_price_elexon', 'dloads')
Site, Era, Bill, SiteEra = db.Site, db.Era, db.Bill, db.SiteEra
Contract, Supply, Source = db.Contract, db.Supply, db.Source
HhDatum, Channel = db.HhDatum, db.Channel
MarketRole = db.MarketRole
HH, hh_after, hh_format = utils.HH, utils.hh_after, utils.hh_format
totalseconds, UserException = utils.totalseconds, utils.UserException
hh_before, form_int = utils.hh_before, utils.form_int
SupplySource = computer.SupplySource
inv = globals()['inv']

base_name = []

now = datetime.datetime.now(pytz.utc)

report_context = {}
future_funcs = {}
report_context['future_funcs'] = future_funcs

if inv.hasParameter('scenario_id'):
    scenario_id = form_int(inv, 'scenario_id')
    scenario_props = None
else:
    year = form_int(inv, "finish_year")
    month = form_int(inv, "finish_month")
    months = form_int(inv, "months")
    start_date = datetime.datetime(year, month, 1) - \
        relativedelta(months=months - 1)
    scenario_props = {
        'scenario_start': start_date, 'scenario_duration': months}
    scenario_id = None
    base_name.append('unified_supplies_monthly_duration')

if inv.hasParameter('site_id'):
    site_id = inv.getLong('site_id')
else:
    site_id = None

if inv.hasParameter('supply_id'):
    supply_id = inv.getLong('supply_id')
else:
    supply_id = None

meter_order = {'hh': 0, 'amr': 1, 'nhh': 2, 'unmetered': 3}
user = inv.getUser()


def content():
    global scenario_props
    sess = None
    try:
        sess = db.session()
        if scenario_props is None:
            scenario_contract = Contract.get_supplier_by_id(sess, scenario_id)
            scenario_props = scenario_contract.make_properties()
            base_name.append(scenario_contract.name)

        for contract in sess.query(Contract).join(MarketRole).filter(
                MarketRole.code == 'Z'):
            try:
                props = scenario_props[contract.name]
            except KeyError:
                continue

            try:
                rate_start = props['start_date']
            except KeyError:
                raise UserException(
                    "In " + scenario_contract.name + " for the rate " +
                    contract.name + " the start_date is missing.")

            if rate_start is not None:
                rate_start = rate_start.replace(tzinfo=pytz.utc)

            try:
                lib = globals()[contract.name]
            except KeyError:
                continue

            if hasattr(lib, 'create_future_func'):
                future_funcs[contract.id] = {
                    'start_date': rate_start,
                    'func': lib.create_future_func(
                        props['multiplier'], props['constant'])}

        start_date = scenario_props['scenario_start']
        if start_date is None:
            start_date = datetime.datetime(
                now.year, now.month, 1, tzinfo=pytz.utc)
        else:
            start_date = start_date.replace(tzinfo=pytz.utc)

        months = scenario_props['scenario_duration']
        finish_date = start_date + relativedelta(months=months)

        if 'kwh_start' in scenario_props:
            kwh_start = scenario_props['kwh_start']
        else:
            kwh_start = None

        if kwh_start is None:
            kwh_start = computer.forecast_date()
        else:
            kwh_start = kwh_start.replace(tzinfo=pytz.utc)

        sites = sess.query(Site).join(SiteEra).join(Era).filter(
            Era.start_date <= start_date,
            or_(
                Era.finish_date == null(),
                Era.finish_date >= start_date)).distinct()
        if site_id is not None:
            site = Site.get_by_id(sess, site_id)
            sites = sites.filter(Site.id == site.id)
            base_name.append('site')
            base_name.append(site.code)
        if supply_id is not None:
            supply = Supply.get_by_id(sess, supply_id)
            base_name.append('supply')
            base_name.append(str(supply.id))
            sites = sites.filter(Era.supply == supply)

        running_name, finished_name = dloads.make_names(
            '_'.join(base_name) + '.ods', user)

        rf = open(running_name, "wb")
        f = odswriter.writer(rf, '1.1')
        group_tab = f.new_sheet("Site Level")
        sup_tab = f.new_sheet("Supply Level")
        changes = defaultdict(list, {})

        try:
            kw_changes = scenario_props['kw_changes']
        except KeyError:
            kw_changes = ''

        for row in csv.reader(StringIO.StringIO(kw_changes)):
            if len(''.join(row).strip()) == 0:
                continue
            if len(row) != 4:
                raise UserException(
                    "Can't interpret the row " + str(row) + " it should be of "
                    "the form SITE_CODE, USED / GENERATED, DATE, MULTIPLIER")
            site_code, typ, date_str, kw_str = row
            date = datetime.datetime.strptime(
                date_str.strip(), "%Y-%m-%d").replace(tzinfo=pytz.utc)
            changes[site_code.strip()].append(
                {
                    'type': typ.strip(), 'date': date,
                    'multiplier': float(kw_str)})

        sup_header_titles = [
            'imp-mpan-core', 'exp-mpan-core', 'metering-type', 'source',
            'generator-type', 'supply-name', 'msn', 'pc', 'site-id',
            'site-name', 'associated-site-ids', 'month']
        site_header_titles = [
            'site-id', 'site-name', 'associated-site-ids', 'month',
            'metering-type', 'sources', 'generator-types']
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
            conts = sess.query(Contract).join(con_attr) \
                .join(Era.supply).join(Source).filter(
                    Era.start_date <= start_date,
                    or_(
                        Era.finish_date == null(),
                        Era.finish_date >= start_date),
                    Source.code.in_(('net', '3rd-party'))
                ).distinct().order_by(Contract.id)
            if supply_id is not None:
                conts = conts.filter(Era.supply_id == supply_id)
            for cont in conts:
                title_func = computer.contract_func(
                    report_context, cont, 'virtual_bill_titles', None)
                if title_func is None:
                    raise Exception(
                        "For the contract " + cont.name +
                        " there doesn't seem to be a "
                        "'virtual_bill_titles' function.")
                for title in title_func():
                    if title not in titles:
                        titles.append(title)

        sup_tab.writerow(
            sup_header_titles + summary_titles + [None] +
            ['mop-' + t for t in title_dict['mop']] +
            [None] + ['dc-' + t for t in title_dict['dc']] + [None] +
            ['imp-supplier-' + t for t in title_dict['imp-supplier']] +
            [None] + ['exp-supplier-' + t for t in title_dict['exp-supplier']])
        group_tab.writerow(site_header_titles + summary_titles)

        sites = sites.all()
        month_start = start_date
        while month_start < finish_date:
            month_finish = month_start + relativedelta(months=1) - HH
            for site in sites:
                site_changes = changes[site.code]
                for group in site.groups(
                        sess, month_start, month_finish, True):
                    calcs = []
                    deltas = defaultdict(int)
                    associated_site_codes = ','.join(
                        s.code for s in group.sites[1:])
                    group_category = None
                    group_sources = set()
                    group_gen_types = set()
                    group_month_data = defaultdict(int)
                    for supply in group.supplies:
                        if supply_id is not None and supply.id != supply_id:
                            continue
                        for era in sess.query(Era).join(Supply) \
                                .join(Source).filter(
                                    Era.supply == supply,
                                    Era.start_date <= group.finish_date, or_(
                                        Era.finish_date == null(),
                                        Era.finish_date >= group.start_date)):

                            if era.start_date > group.start_date:
                                ss_start = era.start_date
                            else:
                                ss_start = group.start_date

                            if hh_before(era.finish_date, group.finish_date):
                                ss_finish = era.finish_date
                            else:
                                ss_finish = group.finish_date

                            if era.imp_mpan_core is None:
                                imp_ss = None
                            else:
                                imp_ss = SupplySource(
                                    sess, ss_start, ss_finish, kwh_start, era,
                                    True, None, report_context)

                            if era.exp_mpan_core is None:
                                exp_ss = None
                                measurement_type = imp_ss.measurement_type
                            else:
                                exp_ss = SupplySource(
                                    sess, ss_start, ss_finish, kwh_start, era,
                                    False, None, report_context)
                                measurement_type = exp_ss.measurement_type

                            order = meter_order[measurement_type]
                            calcs.append(
                                (
                                    order, era.imp_mpan_core,
                                    era.exp_mpan_core, imp_ss, exp_ss))

                            if imp_ss is not None and len(era.channels) == 0:
                                for hh in imp_ss.hh_data:
                                    deltas[hh['start-date']] += hh['msp-kwh']

                    imp_net_delts = defaultdict(int)
                    exp_net_delts = defaultdict(int)
                    imp_gen_delts = defaultdict(int)

                    displaced_era = computer.displaced_era(
                        sess, group, group.start_date, group.finish_date)
                    site_ds = computer.SiteSource(
                        sess, site, group.start_date, group.finish_date,
                        kwh_start, None, report_context, displaced_era)

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
                                    hh['export-gen-kwh'] -
                                    used)
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
                        disp_vb_function = computer.contract_func(
                            report_context, disp_supplier_contract,
                            'displaced_virtual_bill', None)
                        if disp_vb_function is None:
                            raise UserException(
                                "The supplier contract " +
                                disp_supplier_contract.name +
                                " doesn't have the displaced_virtual_bill() "
                                "function.")
                        disp_vb_function(site_ds)
                        disp_supplier_bill = site_ds.supplier_bill

                        try:
                            gbp = disp_supplier_bill['net-gbp']
                        except KeyError:
                            disp_supplier_bill['problem'] += \
                                'For the supply ' + \
                                site_ds.mpan_core + \
                                ' the virtual bill ' + \
                                str(disp_supplier_bill) + \
                                ' from the contract ' + \
                                disp_supplier_contract.name + \
                                ' does not contain the net-gbp key.'

                        month_data['used-gbp'] = \
                            month_data['displaced-gbp'] = \
                            site_ds.supplier_bill['net-gbp']

                        out = [
                            None, None, displaced_era.make_meter_category(),
                            'displaced', None, None, None, None, site.code,
                            site.name, associated_site_codes, month_finish] + \
                            [month_data[t] for t in summary_titles]

                        sup_tab.writerow(out)
                    for i, (
                            order, imp_mpan_core, exp_mpan_core, imp_ss,
                            exp_ss) in enumerate(sorted(calcs)):
                        if imp_ss is None:
                            era = exp_ss.era
                        else:
                            era = imp_ss.era
                        supply = era.supply
                        source = supply.source
                        source_code = source.code
                        group_sources.add(source_code)
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
                            import_vb_function = computer.contract_func(
                                report_context, imp_supplier_contract,
                                'virtual_bill', None)
                            if import_vb_function is None:
                                raise UserException(
                                    "The supplier contract " +
                                    imp_supplier_contract.name +
                                    " doesn't have the virtual_bill() "
                                    "function.")
                            import_vb_function(imp_ss)
                            imp_supplier_bill = imp_ss.supplier_bill

                            try:
                                gbp = imp_supplier_bill['net-gbp']
                            except KeyError:
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
                                month_data['used-gbp'] += gbp
                            elif source_code == '3rd-party':
                                month_data['import-3rd-party-gbp'] += gbp
                                month_data['used-gbp'] += gbp
                            elif source_code == '3rd-party-reverse':
                                month_data['export-3rd-party-gbp'] += gbp
                                month_data['used-gbp'] -= gbp

                            kwh = sum(
                                hh['msp-kwh'] for hh in imp_ss.hh_data)

                            if source_code in ('net', 'gen-net'):
                                month_data['import-net-kwh'] += kwh
                                month_data['used-kwh'] += kwh
                            elif source_code == '3rd-party':
                                month_data['import-3rd-party-kwh'] += kwh
                                month_data['used-kwh'] += kwh
                            elif source_code == '3rd-party-reverse':
                                month_data['export-3rd-party-kwh'] += kwh
                                month_data['used-kwh'] -= kwh
                            elif source_code in ('gen', 'gen-net'):
                                month_data['import-gen-kwh'] += kwh

                            for bill in sess.query(Bill).filter(
                                    Bill.supply == supply,
                                    Bill.start_date <= imp_ss.finish_date,
                                    Bill.finish_date >= imp_ss.start_date):
                                bill_start = bill.start_date
                                bill_finish = bill.finish_date
                                bill_duration = totalseconds(
                                    bill_finish - bill_start) + (30 * 60)
                                overlap_duration = totalseconds(
                                    min(bill_finish, imp_ss.finish_date) -
                                    max(bill_start, imp_ss.start_date)) + \
                                    (30 * 60)
                                overlap_proportion = \
                                    float(overlap_duration) / bill_duration
                                month_data['billed-import-net-kwh'] += \
                                    overlap_proportion * float(bill.kwh)
                                month_data['billed-import-net-gbp'] += \
                                    overlap_proportion * float(bill.net)

                        exp_supplier_contract = era.exp_supplier_contract
                        if exp_supplier_contract is None:
                            kwh = sess.query(
                                func.coalesce(
                                    func.sum(
                                        cast(HhDatum.value, Float)), 0)). \
                                join(Channel).filter(
                                    Channel.era == era,
                                    Channel.channel_type == 'ACTIVE',
                                    Channel.imp_related == false()).scalar()
                            if source_code == 'gen':
                                month_data['export-net-kwh'] += kwh
                        else:
                            export_vb_function = computer.contract_func(
                                report_context, exp_supplier_contract,
                                'virtual_bill', None)
                            export_vb_function(exp_ss)

                            exp_supplier_bill = exp_ss.supplier_bill
                            try:
                                gbp = exp_supplier_bill['net-gbp']
                            except KeyError:
                                exp_supplier_bill['problem'] += \
                                    'For the supply ' + \
                                    imp_ss.mpan_core + \
                                    ' the virtual bill ' + \
                                    str(imp_supplier_bill) + \
                                    ' from the contract ' + \
                                    imp_supplier_contract.name + \
                                    ' does not contain the net-gbp key.'

                            kwh = sum(hh['msp-kwh'] for hh in exp_ss.hh_data)

                            if source_code in ('net', 'gen-net'):
                                month_data['export-net-kwh'] += kwh
                                month_data['export-net-gbp'] += gbp
                            elif source_code in \
                                    ('3rd-party', '3rd-party-reverse'):
                                month_data['export-3rd-party-kwh'] += kwh
                                month_data['export-3rd-party-gbp'] += gbp
                                month_data['used-kwh'] -= kwh
                                month_data['used-gbp'] -= gbp
                            elif source_code == 'gen':
                                month_data['export-gen-kwh'] += kwh

                        sss = exp_ss if imp_ss is None else imp_ss
                        dc_contract = era.hhdc_contract
                        sss.contract_func(
                            dc_contract, 'virtual_bill')(sss)
                        dc_bill = sss.dc_bill
                        gbp = dc_bill['net-gbp']

                        mop_contract = era.mop_contract
                        mop_bill_function = sss.contract_func(
                            mop_contract, 'virtual_bill')
                        mop_bill_function(sss)
                        mop_bill = sss.mop_bill
                        gbp += mop_bill['net-gbp']

                        if source_code in ('net', 'gen', 'gen-net', 'sub'):
                            month_data['import-net-gbp'] += gbp
                            month_data['used-gbp'] += gbp
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-gbp'] += gbp
                            month_data['used-gbp'] += gbp

                        if source_code == 'gen':
                            generator_type = supply.generator_type.code
                            group_gen_types.add(generator_type)
                        else:
                            generator_type = None

                        sup_category = era.make_meter_category()
                        if CATEGORY_ORDER[group_category] < \
                                CATEGORY_ORDER[sup_category]:
                            group_category = sup_category

                        out = [
                            era.imp_mpan_core, era.exp_mpan_core,
                            sup_category, source_code,
                            generator_type, supply.name, era.msn, era.pc.code,
                            site.code, site.name, associated_site_codes,
                            month_finish] + [
                            month_data[t] for t in summary_titles] + [None] + [
                            (mop_bill[t] if t in mop_bill else None)
                            for t in title_dict['mop']] + [None] + \
                            [(dc_bill[t] if t in dc_bill else None)
                                for t in title_dict['dc']]
                        if imp_supplier_contract is None:
                            out += [None] * \
                                (len(title_dict['imp-supplier']) + 1)
                        else:
                            out += [None] + [
                                (
                                    imp_supplier_bill[t]
                                    if t in imp_supplier_bill else None)
                                for t in title_dict['imp-supplier']]
                        if exp_supplier_contract is not None:
                            out += [None] + [
                                (
                                    exp_supplier_bill[t]
                                    if t in exp_supplier_bill else None)
                                for t in title_dict['exp-supplier']]

                        for k, v in month_data.iteritems():
                            group_month_data[k] += v
                        sup_tab.writerow(out)

                    sess.rollback()

                    group_tab.writerow(
                        [
                            site.code, site.name, associated_site_codes,
                            month_finish, group_category,
                            ', '.join(sorted(list(group_sources))),
                            ', '.join(sorted(list(group_gen_types)))] +
                        [group_month_data[k] for k in summary_titles])

            month_start += relativedelta(months=1)
    except:
        msg = traceback.format_exc()
        group_tab.writerow(["Problem " + msg])
    finally:
        f.close()
        rf.close()
        os.rename(running_name, finished_name)
        if sess is not None:
            sess.close()

threading.Thread(target=content).start()
inv.sendSeeOther("/reports/251/output/")
