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
import bsuos
Monad.getUtils()['impt'](
    globals(), 'templater', 'db', 'utils', 'computer', 'bsuos', 'aahedc',
    'ccl')
Site, Era, Bill, SiteEra = db.Site, db.Era, db.Bill, db.SiteEra
Contract, Supply, Source = db.Contract, db.Supply, db.Source
HH, hh_after, hh_format = utils.HH, utils.hh_after, utils.hh_format
totalseconds, UserException = utils.totalseconds, utils.UserException
inv = globals()['inv']

now = datetime.datetime.now(pytz.utc)
file_name = 'scenario_' + now.strftime("%Y%m%d%H%M") + '.csv'

report_context = {}
future_funcs = {}
report_context['future_funcs'] = future_funcs
scenario_name = inv.getString('scenario')
if inv.hasParameter('site_id'):
    site_id = inv.getLong('site_id')
else:
    site_id = None


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


def content():
    sess = None
    try:
        sess = db.session()
        scenario_contract = Contract.get_supplier_by_name(sess, scenario_name)
        scenario_props = scenario_contract.make_properties()

        bsuos_props = scenario_props['bsuos']

        def bsuos_future(ns):
            old_result = ns['rates_gbp_per_mwh']()
            last_value = old_result[sorted(old_result.keys())[-1]]
            new_result = defaultdict(
                lambda: last_value, [
                    (
                        k, v * bsuos_props['multiplier'] +
                        bsuos_props['constant'])
                    for k, v in old_result.iteritems()])

            def rates_gbp_per_mwh():
                return new_result
            return {'rates_gbp_per_mwh': rates_gbp_per_mwh}

        base_date = bsuos_props['base_date']
        if base_date is not None:
            base_date = base_date.replace(tzinfo=pytz.utc)

        future_funcs[bsuos.db_id] = {
            'base_date': base_date,
            'func': bsuos_future}

        for cname, fname in (
                ('ccl', 'ccl_rate'), ('aahedc', 'aahedc_gbp_per_gsp_kwh')):
            props = scenario_props[cname]

            base_date = props['base_date']
            if base_date is not None:
                base_date = base_date.replace(tzinfo=pytz.utc)
            future_funcs[globals()[cname].db_id] = {
                'base_date': base_date,
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
                        Source.code.in_(('net', '3rd-party'))).distinct():
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
                for group in site.groups(sess, month_start, month_start, True):
                    for supply in group.supplies:
                        res = sess.query(Era, Source.code).join(Supply). \
                            join(Source).filter(
                                Era.supply == supply,
                                Era.start_date <= month_start,
                                or_(
                                    Era.finish_date == null(),
                                    Era.finish_date >= month_start),
                                Source.code.in_(
                                    (
                                        'net', 'gen-net', '3rd-party',
                                        '3rd-party-reverse'))).first()
                        if res is None:
                            continue

                        era, source_code = res

                        month_data = {}
                        for name in (
                                'import-net', 'export-net', 'import-gen',
                                'export-gen', 'import-3rd-party',
                                'export-3rd-party', 'displaced', 'used',
                                'used-3rd-party'):
                            for sname in ('kwh', 'gbp'):
                                month_data[name + '-' + sname] = 0

                        supply_source = computer.SupplySource(
                            sess, month_start, month_finish, forecast_date,
                            era, True, None, report_context)

                        kwh = sum(
                            hh['msp-kwh'] for hh in supply_source.hh_data)
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
                            import_vb_function(supply_source)
                            imp_supplier_bill = supply_source.supplier_bill

                            try:
                                gbp = imp_supplier_bill['net-gbp']
                            except KeyError:
                                imp_supplier_bill['problem'] += \
                                    'For the supply ' + \
                                    supply_source.mpan_core + \
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
                        supply_source.contract_func(
                            dc_contract, 'virtual_bill')(supply_source)
                        dc_bill = supply_source.dc_bill
                        gbp = dc_bill['net-gbp']
                        if source_code in ('net', 'gen-net'):
                            month_data['import-net-gbp'] += gbp
                            month_data['used-gbp'] += gbp
                        elif source_code in ('3rd-party', '3rd-party-reverse'):
                            month_data['import-3rd-party-gbp'] += gbp
                            month_data['used-gbp'] += gbp

                        mop_contract = era.mop_contract
                        mop_bill_function = supply_source.contract_func(
                            mop_contract, 'virtual_bill')
                        mop_bill_function(supply_source)
                        mop_bill = supply_source.mop_bill
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
                            supply_source = computer.SupplySource(
                                sess, month_start, month_finish, forecast_date,
                                era, False, None, report_context)
                            export_vb_function = computer.contract_func(
                                report_context, exp_supplier_contract,
                                'virtual_bill', None)
                            export_vb_function(supply_source)

                            exp_supplier_bill = supply_source.supplier_bill

                            kwh = sum(
                                hh['msp-kwh'] for hh in supply_source.hh_data)

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

                    displaced_era = computer.displaced_era(
                        sess, group, month_start, month_finish)
                    if displaced_era is not None:
                        site_ds = computer.SiteSource(
                            sess, site, month_start, month_finish,
                            forecast_date, None, report_context, displaced_era)
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
                    sess.rollback()
            month_start += relativedelta(months=1)
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name=file_name)
