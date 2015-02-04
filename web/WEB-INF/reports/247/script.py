from net.sf.chellow.monad import Monad
import datetime
import traceback
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from collections import defaultdict
import db
import utils
import computer
import csv
import StringIO
Monad.getUtils()['impt'](
    globals(), 'templater', 'db', 'utils', 'computer', 'bsuos', 'aahedc',
    'ccl', 'system_price_bmreports', 'system_price_elexon')
Site, Era, Bill, SiteEra = db.Site, db.Era, db.Bill, db.SiteEra
Contract, Supply, Source = db.Contract, db.Supply, db.Source
HH, hh_after, hh_format = utils.HH, utils.hh_after, utils.hh_format
totalseconds, UserException = utils.totalseconds, utils.UserException
hh_before, form_int = utils.hh_before, utils.form_int
SupplySource = computer.SupplySource
inv = globals()['inv']

now = datetime.datetime.now(pytz.utc)
file_name = 'scenario_' + now.strftime("%Y%m%d%H%M") + '.csv'

report_context = {}
future_funcs = {}
report_context['future_funcs'] = future_funcs
scenario_id = form_int(inv, 'scenario_id')
if inv.hasParameter('site_id'):
    site_id = inv.getLong('site_id')
else:
    site_id = None


meter_order = {'hh': 0, 'amr': 1, 'nhh': 2, 'unmetered': 3}


def create_future_func(cname, fname, props):
    def future_func(ns):
        try:
            val = ns[fname]() * props['multiplier'] + props['constant']
        except KeyError:
            raise UserException(
                "Can't find " + fname + " in rate script " + str(ns) +
                " for contract name " + cname + " .")

        def rate_func():
            return val
        return {fname: rate_func}
    return future_func


def create_monthly_func(cname, fnames, props):
    def future_func(ns):
        new_ns = {}
        for fname in fnames:
            old_result = ns[fname]()
            last_value = old_result[sorted(old_result.keys())[-1]]
            new_result = defaultdict(
                lambda: last_value, [
                    (k, v * props['multiplier'] + props['constant'])
                    for k, v in old_result.iteritems()])

            def rate_func():
                return new_result

            new_ns[fname] = rate_func
        return new_ns
    return future_func


def content():
    sess = None
    try:
        sess = db.session()
        scenario_contract = Contract.get_supplier_by_id(sess, scenario_id)
        scenario_props = scenario_contract.make_properties()

        for cname, fnames in (
                ('bsuos', ['rates_gbp_per_mwh']),
                ('system_price_bmreports', ['ssps', 'sbps']),
                ('system_price_elexon', ['ssps', 'sbps'])):

            try:
                props = scenario_props[cname]
            except KeyError:
                props = {'start_date': None, 'multiplier': 1, 'constant': 0}

            try:
                rate_start = props['start_date']
            except KeyError:
                raise UserException(
                    "In " + scenario_contract.name + " for the rate " + cname +
                    " the start_date is missing.")
            if rate_start is not None:
                rate_start = rate_start.replace(tzinfo=pytz.utc)
            future_funcs[globals()[cname].db_id] = {
                'start_date': rate_start,
                'func': create_monthly_func(cname, fnames, props)}

        for cname, fname in (
                ('ccl', 'ccl_rate'), ('aahedc', 'aahedc_gbp_per_gsp_kwh')):
            props = scenario_props[cname]

            rate_start = props['start_date']
            if rate_start is not None:
                rate_start = rate_start.replace(tzinfo=pytz.utc)
            future_funcs[globals()[cname].db_id] = {
                'start_date': rate_start,
                'func': create_future_func(cname, fname, props)}

        start_date = scenario_props['scenario_start']
        if start_date is None:
            start_date = datetime.datetime(
                now.year, now.month, 1, tzinfo=pytz.utc)
        else:
            start_date = start_date.replace(tzinfo=pytz.utc)

        months = scenario_props['scenario_duration']
        finish_date = start_date + relativedelta(months=months)
        sites = sess.query(Site).join(SiteEra).join(Era).filter(
            Era.start_date <= start_date,
            or_(
                Era.finish_date == null(),
                Era.finish_date >= start_date)).distinct()
        if site_id is not None:
            sites = sites.filter(Site.id == site_id)

        changes = defaultdict(list, {})
        for row in csv.reader(StringIO.StringIO(scenario_props['kw_changes'])):
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

        forecast_date = computer.forecast_date()

        header_titles = [
            'imp-mpan-core', 'exp-mpan-core', 'type', 'site-id', 'site-name',
            'month']
        summary_titles = [
            'import-net-kwh', 'export-net-kwh', 'import-gen-kwh',
            'export-gen-kwh', 'import-3rd-party-kwh', 'export-3rd-party-kwh',
            'displaced-kwh', 'used-kwh', 'used-3rd-party-kwh',
            'import-net-gbp', 'export-net-gbp', 'import-gen-gbp',
            'export-gen-gbp', 'import-3rd-party-gbp', 'export-3rd-party-gbp',
            'displaced-gbp', 'used-gbp', 'used-3rd-party-gbp']

        title_dict = {}
        for cont_type, con_attr in (
                ('mop', Era.mop_contract), ('dc', Era.hhdc_contract),
                ('imp-supplier', Era.imp_supplier_contract),
                ('exp-supplier', Era.exp_supplier_contract)):
            titles = []
            title_dict[cont_type] = titles
            for cont in sess.query(Contract).join(con_attr) \
                    .join(Era.supply).join(Source).filter(
                        Era.start_date <= start_date,
                        or_(
                            Era.finish_date == null(),
                            Era.finish_date >= start_date),
                        Source.code.in_(('net', '3rd-party'))
                    ).distinct().order_by(Contract.id):
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

        yield ','.join(
            header_titles + summary_titles + [''] +
            ['mop-' + t for t in title_dict['mop']] +
            [''] + ['dc-' + t for t in title_dict['dc']] + [''] +
            ['imp-supplier-' + t for t in title_dict['imp-supplier']] + [''] +
            ['exp-supplier-' + t for t in title_dict['exp-supplier']]) + '\n'
        sites = sites.all()
        month_start = start_date
        while month_start < finish_date:
            month_finish = month_start + relativedelta(months=1) - HH
            month_str = month_finish.strftime("%Y-%m-%d %H:%M")
            for site in sites:
                site_changes = changes[site.code]
                for group in site.groups(
                        sess, month_start, month_finish, True):
                    calcs = []
                    deltas = defaultdict(int)
                    for supply in group.supplies:
                        for era in sess.query(Era).join(Supply) \
                                .join(Source).filter(
                                Era.supply == supply,
                                Era.start_date <= group.finish_date, or_(
                                Era.finish_date == null(),
                                Era.finish_date >= group.start_date),
                                Source.code.in_(
                                    (
                                        'net', 'gen-net', '3rd-party',
                                        '3rd-party-reverse'))):

                            if era.start_date > group.start_date:
                                ss_start = era.start_date
                            else:
                                ss_start = group.start_date

                            if hh_before(era.finish_date, group.finish_date):
                                ss_finish = era.finish_date
                            else:
                                ss_finish = group.finish_date

                            imp_ss = SupplySource(
                                sess, ss_start, ss_finish, forecast_date,
                                era, True, None, report_context)
                            if era.exp_mpan_core is None:
                                exp_ss = None
                            else:
                                exp_ss = SupplySource(
                                    sess, ss_start, ss_finish, forecast_date,
                                    era, False, None, report_context)
                            order = meter_order[imp_ss.measurement_type]
                            calcs.append(
                                (
                                    order, era.imp_mpan_core,
                                    era.exp_mpan_core, imp_ss, exp_ss))

                            if len(era.channels) == 0:
                                for hh in imp_ss.hh_data:
                                    deltas[hh['start-date']] += hh['msp-kwh']

                    imp_delts = defaultdict(int)
                    exp_delts = defaultdict(int)
                    displaced_era = computer.displaced_era(
                        sess, group, group.start_date, group.finish_date)
                    site_ds = computer.SiteSource(
                        sess, site, group.start_date, group.finish_date,
                        forecast_date, None, report_context, displaced_era)

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
                                exp_delt = exp_net - hh['export-net-kwh']
                                exp_delts[hh['start-date']] += exp_delt
                                displaced = hh['import-gen-kwh'] - \
                                    hh['export-gen-kwh'] - exp_net
                                imp_net = used - displaced
                                imp_delt = imp_net - hh['import-net-kwh']
                                imp_delts[hh['start-date']] += imp_delt

                                hh['import-net-kwh'] = imp_net
                                hh['used-kwh'] = used
                                hh['export-net-kwh'] = exp_net
                                hh['msp-kwh'] = displaced
                            elif change['type'] == 'generated' and \
                                    change['date'] <= hh['start-date']:
                                imp_gen = change['multiplier'] * \
                                    hh['import-gen-kwh']
                                exp_net = max(
                                    0, imp_gen - hh['export-gen-kwh'] -
                                    hh['used-kwh'])
                                exp_delt = exp_net - hh['export-net-kwh']
                                exp_delts[hh['start-date']] += exp_delt
                                displaced = imp_gen - hh['export-gen-kwh'] - \
                                    exp_net
                                imp_net = hh['used-kwh'] - displaced
                                imp_delt = imp_net - hh['import-net-kwh']
                                imp_delts[hh['start-date']] += imp_delt

                                hh['import-net-kwh'] = imp_net
                                hh['export-net-kwh'] = exp_net
                                hh['import-gen-kwh'] = imp_gen
                                hh['msp-kwh'] = displaced

                    if displaced_era is not None:
                        month_data = {}
                        for sname in (
                                'import-net', 'export-net', 'import-gen',
                                'export-gen', 'import-3rd-party',
                                'export-3rd-party', 'msp', 'used',
                                'used-3rd-party'):
                            for xname in ('kwh', 'gbp'):
                                month_data[sname + '-' + xname] = 0

                        month_data['used-kwh'] = \
                            month_data['displaced-kwh'] = \
                            sum(hh['msp-kwh'] for hh in site_ds.hh_data)

                        month_data['displaced-gbp'] = 0

                        out = [
                            '', '', 'displaced', site.code, site.name,
                            month_str] + \
                            [month_data[t] for t in summary_titles]
                        yield ','.join(
                            '"' + str('' if v is None else v) +
                            '"' for v in out) + '\n'
                    for i, (
                            order, imp_mpan_core, exp_mpan_core, imp_ss,
                            exp_ss) in enumerate(sorted(calcs)):
                        era = imp_ss.era
                        supply = era.supply
                        source = supply.source
                        source_code = source.code

                        month_data = {}
                        for name in (
                                'import-net', 'export-net', 'import-gen',
                                'export-gen', 'import-3rd-party',
                                'export-3rd-party', 'displaced', 'used',
                                'used-3rd-party'):
                            for sname in ('kwh', 'gbp'):
                                month_data[name + '-' + sname] = 0

                        if len(imp_delts) > 0:
                            for hh in imp_ss.hh_data:
                                diff = hh['msp-kwh'] + \
                                    imp_delts[hh['start-date']]
                                if diff < 0:
                                    hh['msp-kwh'] = 0
                                    hh['msp-kw'] = 0
                                    imp_delts[hh['start-date']] -= \
                                        hh['msp-kwh']
                                else:
                                    hh['msp-kwh'] += \
                                        imp_delts[hh['start-date']]
                                    hh['msp-kw'] += hh['msp-kwh'] / 2
                                    del imp_delts[hh['start-date']]

                            left_kwh = sum(imp_delts.values())
                            if left_kwh > 0:
                                first_hh = imp_ss.hh_data[0]
                                first_hh['msp-kwh'] += left_kwh
                                first_hh['msp-kw'] += left_kwh / 2

                        kwh = sum(
                            hh['msp-kwh'] for hh in imp_ss.hh_data)

                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-kwh'] += kwh
                            month_data['used-kwh'] += kwh
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-kwh'] += kwh
                            month_data['used-kwh'] += kwh

                        imp_supplier_contract = era.imp_supplier_contract
                        if imp_supplier_contract is not None:
                            import_vb_function = computer.contract_func(
                                report_context, imp_supplier_contract,
                                'virtual_bill', None)
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
                            elif source_code in (
                                    '3rd-party', '3rd-party-reverse'):
                                month_data['import-3rd-party-gbp'] += gbp
                                month_data['used-gbp'] += gbp

                        dc_contract = era.hhdc_contract
                        imp_ss.contract_func(
                            dc_contract, 'virtual_bill')(imp_ss)
                        dc_bill = imp_ss.dc_bill
                        gbp = dc_bill['net-gbp']
                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-gbp'] += gbp
                            month_data['used-gbp'] += gbp
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-gbp'] += gbp
                            month_data['used-gbp'] += gbp

                        mop_contract = era.mop_contract
                        mop_bill_function = imp_ss.contract_func(
                            mop_contract, 'virtual_bill')
                        mop_bill_function(imp_ss)
                        mop_bill = imp_ss.mop_bill
                        gbp = mop_bill['net-gbp']
                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-gbp'] += gbp
                            month_data['used-gbp'] += gbp
                            type = 'net'
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-gbp'] += gbp
                            month_data['used-gbp'] += gbp
                            type = '3rd-party'

                        exp_supplier_contract = era.exp_supplier_contract
                        if exp_supplier_contract is not None:
                            export_vb_function = computer.contract_func(
                                report_context, exp_supplier_contract,
                                'virtual_bill', None)
                            export_vb_function(exp_ss)

                            exp_supplier_bill = exp_ss.supplier_bill

                            kwh = sum(
                                hh['msp-kwh'] for hh in exp_ss.hh_data)

                            if source_code in ('net', 'gen-net'):
                                month_data['export-net-kwh'] += kwh
                                month_data['export-net-gbp'] += gbp
                            elif source_code in \
                                    ('3rd-party', '3rd-party-reverse'):
                                month_data['export-3rd-party-kwh'] += kwh
                                month_data['export-3rd-party-gbp'] += gbp
                                month_data['used-kwh'] -= kwh
                                month_data['used-gbp'] -= gbp

                        out = [
                            era.imp_mpan_core, era.exp_mpan_core, type,
                            site.code, site.name, month_str] + [
                            month_data[t] for t in summary_titles] + [''] + [
                            (mop_bill[t] if t in mop_bill else '')
                            for t in title_dict['mop']] + [''] + \
                            [(dc_bill[t] if t in dc_bill else '')
                                for t in title_dict['dc']] + [''] + \
                            [(imp_supplier_bill[t]
                                if t in imp_supplier_bill else '')
                                for t in title_dict['imp-supplier']]
                        if exp_supplier_contract is not None:
                            out += [''] + [
                                (
                                    exp_supplier_bill[t]
                                    if t in exp_supplier_bill else '')
                                for t in title_dict['exp-supplier']]

                        yield ','.join('"' + str(v) + '"' for v in out) + '\n'

                    sess.rollback()
            month_start += relativedelta(months=1)
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name=file_name)
