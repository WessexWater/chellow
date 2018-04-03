from collections import defaultdict
from datetime import datetime as Datetime
from pytz import utc, timezone
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, cast, Float
from sqlalchemy.sql.expression import null, false
from sqlalchemy.orm import joinedload, aliased
from math import log10
from werkzeug.exceptions import BadRequest
from chellow.models import (
    RateScript, Channel, Era, Tpr, MeasurementRequirement, RegisterRead, Bill,
    BillType, ReadType, SiteEra, Supply, Source, HhDatum, Contract,
    ClockInterval, Mtc)
from chellow.utils import (
    HH, hh_format, hh_max, hh_range, hh_min, utc_datetime, utc_datetime_now,
    to_tz, to_ct, loads, PropDict)
import chellow.bank_holidays
from itertools import combinations
from types import MappingProxyType
from functools import lru_cache


cons_types = ['construction', 'commissioning', 'operation']
lec_cats = list(
    (v + '-kwh', 'hist-' + v + '-kwh') for v in [
        'import-net', 'export-net', 'import-gen', 'export-gen',
        'import-3rd-party', 'export-3rd-party'])


@lru_cache()
def get_times(start_date, finish_date, forecast_date):
    if start_date > finish_date:
        raise BadRequest('The start date is after the finish date.')
    hist_start = start_date
    hist_finish = finish_date
    years_back = 0
    while hist_finish > forecast_date:
        hist_start -= relativedelta(years=1)
        hist_finish -= relativedelta(years=1)
        years_back += 1

    return MappingProxyType(
        {
            'history-finish': hist_finish,
            'history-start': hist_start,
            'years-back': years_back})


def contract_func(caches, contract, func_name):
    try:
        ns = caches['computer']['funcs'][contract.id]
    except KeyError:
        try:
            ccache = caches['computer']
        except KeyError:
            ccache = caches['computer'] = {}

        try:
            contr_func_cache = ccache['funcs']
        except KeyError:
            contr_func_cache = ccache['funcs'] = {}

        try:
            ns = contr_func_cache[contract.id]
        except KeyError:
            ns = {
                'db_id': contract.id, 'properties': contract.make_properties()}
            exec(contract.charge_script, ns)
            contr_func_cache[contract.id] = ns

    return ns.get(func_name, None)


def hh_rate(sess, caches, contract_id, date):
    try:
        return caches['computer']['rates'][contract_id][date]
    except KeyError:
        try:
            ccache = caches['computer']
        except KeyError:
            ccache = caches['computer'] = {}

        try:
            rss_cache = ccache['rates']
        except KeyError:
            rss_cache = ccache['rates'] = {}

        try:
            cont_cache = rss_cache[contract_id]
        except KeyError:
            cont_cache = rss_cache[contract_id] = {}

        try:
            return cont_cache[date]
        except KeyError:
            month_after = date + relativedelta(months=1) + relativedelta(
                days=1)
            month_before = date - relativedelta(months=1) - relativedelta(
                days=1)

            rs = sess.query(RateScript).filter(
                RateScript.contract_id == contract_id,
                RateScript.start_date <= date, or_(
                    RateScript.finish_date == null(),
                    RateScript.finish_date >= date)).first()

            if rs is None:
                rs = sess.query(RateScript).filter(
                    RateScript.contract_id == contract_id).order_by(
                    RateScript.start_date.desc()).first()
                if date < rs.start_date:
                    cstart = month_before
                    cfinish = min(month_after, rs.start_date - HH)
                else:
                    cstart = max(rs.finish_date + HH, month_before)
                    cfinish = month_after
            else:
                cstart = max(rs.start_date, month_before)
                if rs.finish_date is None:
                    cfinish = month_after
                else:
                    cfinish = min(rs.finish_date, month_after)

            vals = PropDict(
                "the local rate script for contract " + str(contract_id) +
                " at " + hh_format(cstart) + ".", loads(rs.script), [])
            for dt in hh_range(caches, cstart, cfinish):
                if dt not in cont_cache:
                    cont_cache[dt] = vals

            return vals


def forecast_date():
    now = utc_datetime_now()
    return utc_datetime(now.year, now.month, 1)


def displaced_era(sess, caches, site, start_date, finish_date, forecast_date):
    if (start_date.year, start_date.month) != \
            (finish_date.year, finish_date.month):
        raise BadRequest(
            "The start and end dates of a displaced period must be within the "
            "same month")
    t = get_times(start_date, finish_date, forecast_date)
    hist_start = t['history-start']
    month_start = utc_datetime(hist_start.year, hist_start.month)
    month_finish = month_start + relativedelta(months=1) - HH
    has_displaced = False
    eras = {}
    for site_era in sess.query(SiteEra).join(Era).join(Supply).join(Source). \
            filter(
                SiteEra.site == site, Era.start_date <= month_finish, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= month_start)).options(
                        joinedload(SiteEra.era).joinedload(Era.supply).
                        joinedload(Supply.source)):
        era = site_era.era
        source_code = era.supply.source.code
        if site_era.is_physical and (
                source_code in ('gen', 'gen-net') or (
                    source_code == 'net' and sess.query(Channel).filter(
                        Channel.era == era, Channel.imp_related == false(),
                        Channel.channel_type == 'ACTIVE').first()
                    is not None)):
            has_displaced = True

        if source_code in ('net', 'gen-net') and era.imp_mpan_core is not None:
            eras[
                era.pc.code + hh_format(era.start_date) +
                era.imp_mpan_core] = era

    if has_displaced and len(eras) > 0:
        era = eras[sorted(eras.keys())[0]]
    else:
        era = None
    return era


def get_data_sources(data_source, start_date, finish_date, forecast_date=None):
    if forecast_date is None:
        forecast_date = data_source.forecast_date

    if data_source.start_date == start_date and \
            data_source.finish_date == finish_date \
            and forecast_date == data_source.forecast_date:
        yield data_source
    elif data_source.site is None:
        if data_source.is_import:
            eras = data_source.sess.query(Era).filter(
                Era.supply == data_source.supply,
                Era.imp_mpan_core != null(), Era.start_date <= finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= start_date))
        else:
            eras = data_source.sess.query(Era).filter(
                Era.supply == data_source.supply, Era.exp_mpan_core != null(),
                Era.start_date <= finish_date,
                or_(Era.finish_date == null(), Era.finish_date >= start_date))

        for era in eras:
            chunk_start = hh_max(era.start_date, start_date)
            chunk_finish = hh_min(era.finish_date, finish_date)

            ds = SupplySource(
                data_source.sess, chunk_start, chunk_finish, forecast_date,
                era, data_source.is_import, data_source.caches,
                data_source.bill, data_source.era_maps, data_source.deltas)
            yield ds

    else:
        month_start = utc_datetime(start_date.year, start_date.month)
        while month_start <= finish_date:
            month_finish = month_start + relativedelta(months=1) - HH
            chunk_start = hh_max(month_start, start_date)
            chunk_finish = hh_min(month_finish, finish_date)
            if data_source.stream_focus == 'gen-used' and \
                    data_source.era is not None:
                era = displaced_era(
                    data_source.sess, data_source.caches, data_source.site,
                    chunk_start, chunk_finish, forecast_date)
                if era is None:
                    return
            else:
                era = data_source.era

            site_ds = SiteSource(
                data_source.sess, data_source.site, chunk_start, chunk_finish,
                forecast_date, data_source.caches, era, data_source.era_maps,
                data_source.deltas)
            if data_source.stream_focus == '3rd-party-used':
                site_ds.revolve_to_3rd_party_used()
            month_start += relativedelta(months=1)
            yield site_ds


def _tpr_dict(sess, caches, tpr_code):
    try:
        return caches['computer']['tprs'][tpr_code]
    except KeyError:
        try:
            ccache = caches['computer']
        except KeyError:
            ccache = caches['computer'] = {}

        try:
            tpr_cache = ccache['tprs']
        except KeyError:
            tpr_cache = ccache['tprs'] = {}

        tpr = Tpr.get_by_code(sess, tpr_code)
        days_of_week = dict([i, []] for i in range(7))
        tpr_dict = {
            'days-of-week': days_of_week, 'is-gmt': tpr.is_gmt,
            'datum-cache': {}}
        if tpr.is_teleswitch:
            contract = Contract.find_supplier_by_name(sess, 'teleswitch')
            if contract is None:
                cis = []
            else:
                tprs = hh_rate(
                    sess, caches, contract.id, utc_datetime_now())['tprs']
                try:
                    cis = tprs[tpr_code]
                except KeyError:
                    raise BadRequest(
                        "Can't find the TPR " + tpr_code +
                        " in the rate script of the 'teleswitch' supplier "
                        "contract.")
        else:
            cis = [
                {
                    'day_of_week': ci.day_of_week,
                    'start_month': ci.start_month,
                    'start_day': ci.start_day,
                    'start_hour': ci.start_hour,
                    'start_minute': ci.start_minute,
                    'end_month': ci.end_month,
                    'end_day': ci.end_day,
                    'end_hour': ci.end_hour,
                    'end_minute': ci.end_minute}
                for ci in sess.query(ClockInterval).filter(
                    ClockInterval.tpr == tpr)]

        for ci in cis:
            days_of_week[ci['day_of_week'] - 1].append(
                {
                    'start-month': ci['start_month'] * 100 + ci['start_day'],
                    'start-hour': ci['start_hour'] + ci['start_minute'] / 60,
                    'end-month': ci['end_month'] * 100 + ci['end_day'],
                    'end-hour': ci['end_hour'] + ci['end_minute'] / 60})

        tpr_cache[tpr_code] = tpr_dict
        return tpr_dict


def is_tpr(sess, caches, tpr_code, hh_date):
    try:
        return _tpr_dict(sess, caches, tpr_code)['datum-cache'][hh_date]
    except KeyError:
        tpr_dict = _tpr_dict(sess, caches, tpr_code)
        datum_cache = tpr_dict['datum-cache']

        days_of_week = tpr_dict['days-of-week']
        datum = datum_range(sess, caches, 0, hh_date, hh_date)[0]
        pref = 'utc-' if tpr_dict['is-gmt'] else 'ct-'

        decimal_hour = datum[pref + 'decimal-hour']
        fractional_month = datum[pref + 'month'] * 100 + \
            datum[pref + 'day']

        result = False

        for ci in days_of_week[datum[pref + 'day-of-week']]:
            if (
                    (
                        ci['start-hour'] < ci['end-hour'] and
                        ci['start-hour'] <= decimal_hour < ci['end-hour']
                    ) or (
                        ci['start-hour'] >= ci['end-hour'] and (
                            ci['start-hour'] <= decimal_hour or
                            decimal_hour < ci['end-hour']))) and \
                    ci['start-month'] <= fractional_month \
                    <= ci['end-month']:
                result = True
                break
        datum_cache[hh_date] = result
        return result


def cache_level(cache, key):
    try:
        return cache[key]
    except BaseException:
        cache[key] = new_cache = {}
        return new_cache


def datum_range(sess, caches, years_back, start_date, finish_date):
    try:
        return caches['computer']['datum_range'][years_back][start_date][
            finish_date]
    except KeyError:
        computer_cache = cache_level(caches, 'computer')
        range_cache = cache_level(computer_cache, 'datum_range')
        yb_range_cache = cache_level(range_cache, years_back)
        start_range_cache = cache_level(yb_range_cache, start_date)
        datum_cache = cache_level(computer_cache, 'datum')
        yb_datum_cache = cache_level(datum_cache, years_back)

        datum_list = []
        for dt in hh_range(caches, start_date, finish_date):
            try:
                datum = yb_datum_cache[dt]
            except KeyError:
                hist_date = dt - relativedelta(years=years_back)
                ct_dt = to_ct(dt)

                utc_is_month_end = (dt + HH).day == 1 and dt.day != 1
                ct_is_month_end = (ct_dt + HH).day == 1 and ct_dt.day != 1

                utc_decimal_hour = dt.hour + dt.minute / 60
                ct_decimal_hour = ct_dt.hour + ct_dt.minute / 60

                bhs = hh_rate(
                    sess, caches, chellow.bank_holidays.get_db_id(),
                    dt)['bank_holidays']

                bank_holidays = [b[5:] for b in bhs]
                utc_is_bank_holiday = dt.strftime("%m-%d") in bank_holidays
                ct_is_bank_holiday = ct_dt.strftime("%m-%d") in bank_holidays

                datum = MappingProxyType(
                    {
                        'hist-start': hist_date, 'start-date': dt,
                        'ct-day': ct_dt.day, 'utc-month': dt.month,
                        'utc-day': dt.day,
                        'utc-decimal-hour': utc_decimal_hour,
                        'utc-year': dt.year, 'utc-hour': dt.hour,
                        'utc-minute': dt.minute, 'ct-year': ct_dt.year,
                        'ct-month': ct_dt.month,
                        'ct-decimal-hour': ct_decimal_hour,
                        'ct-day-of-week': ct_dt.weekday(),
                        'utc-day-of-week': dt.weekday(),
                        'utc-is-bank-holiday': utc_is_bank_holiday,
                        'ct-is-bank-holiday': ct_is_bank_holiday,
                        'utc-is-month-end': utc_is_month_end,
                        'ct-is-month-end': ct_is_month_end,
                        'status': 'X', 'imp-msp-kvarh': 0,
                        'imp-msp-kvar': 0, 'exp-msp-kvarh': 0,
                        'exp-msp-kvar': 0, 'msp-kw': 0, 'msp-kwh': 0,
                        'hist-import-net-kvarh': 0,
                        'hist-export-net-kvarh': 0,
                        'anti-msp-kwh': 0, 'anti-msp-kw': 0,
                        'imp-msp-kvarh': 0, 'exp-msp-kvarh': 0,
                        'imp-msp-kvar': 0, 'exp-msp-kvar': 0,
                        'hist-imp-msp-kvarh': 0, 'hist-kwh': 0})
                yb_datum_cache[dt] = datum
            datum_list.append(datum)
        datum_tuple = start_range_cache[finish_date] = tuple(datum_list)
        return datum_tuple


class DataSource():
    def __init__(
            self, sess, start_date, finish_date, forecast_date, caches,
            era_maps, deltas=None):
        self.sess = sess
        self.caches = caches
        self.forecast_date = forecast_date
        self.start_date = start_date
        self.finish_date = finish_date
        self.deltas = deltas
        times = get_times(start_date, finish_date, forecast_date)
        self.years_back = times['years-back']
        self.history_start = times['history-start']
        self.history_finish = times['history-finish']

        self.is_green = False
        self.supplier_bill = defaultdict(int, {'problem': ''})
        self.mop_bill = defaultdict(int, {'problem': ''})
        self.dc_bill = defaultdict(int, {'problem': ''})
        self.hh_data = []
        self.supplier_rate_sets = defaultdict(set)
        self.mop_rate_sets = defaultdict(set)
        self.dc_rate_sets = defaultdict(set)

        self.era_maps = {} if era_maps is None else era_maps
        era_map = {}
        for em_start, em in sorted(self.era_maps.items()):
            if em_start <= start_date:
                era_map = em
                break
        era_map = PropDict("scenario properties", era_map)
        self.era_map_llfcs = era_map.get('llfcs', {})
        self.era_map_pcs = era_map.get('pcs', {})
        self.era_map_supplier_contracts = era_map.get('supplier_contracts', {})
        self.era_map_dc_contracts = era_map.get('dc_contracts', {})
        self.era_map_mop_contracts = era_map.get('mop_contracts', {})
        self.era_map_cops = era_map.get('cops', {})

    def contract_func(self, contract, func_name):
        return contract_func(self.caches, contract, func_name)

    def hh_rate(self, contract_id, date):
        try:
            return self.rate_cache[contract_id][date]
        except KeyError:
            return hh_rate(self.sess, self.caches, contract_id, date)
        except AttributeError:
            val = hh_rate(self.sess, self.caches, contract_id, date)
            self.rate_cache = self.caches['computer']['rates']
            return val

    def _add_problem(self, problem):
        self.supplier_bill['problem'] += problem
        self.mop_bill['problem'] += problem
        self.dc_bill['problem'] += problem


class SiteSource(DataSource):
    def __init__(
            self, sess, site, start_date, finish_date, forecast_date, caches,
            era=None, era_maps=None, deltas=None):
        DataSource.__init__(
            self, sess, start_date, finish_date, forecast_date, caches,
            era_maps, deltas=deltas)
        self.site = site
        self.bill = None
        self.stream_focus = 'gen-used'
        if era is None:
            self.is_displaced = False
        else:
            self.era = era
            self.is_displaced = True
            self.supply = self.era.supply
            self.mpan_core = era.imp_mpan_core
            self.dno = self.supply.dno
            self.dno_code = self.dno.dno_code

            if era.imp_llfc.code in self.era_map_llfcs:
                self.llfc_code = self.era_map_llfcs[era.imp_llfc.code]
                self.llfc = self.dno.get_llfc_by_code(sess, self.llfc_code)
            else:
                self.llfc = era.imp_llfc
                self.llfc_code = self.llfc.code

            if era.pc.code in self.era_map_pcs:
                self.pc_code = self.era_map_pcs[era.pc.code]
            else:
                self.pc_code = era.pc.code

            if era.cop.code in self.era_map_cops:
                self.cop_code = self.era_map_cops[era.cop.code]
            else:
                self.cop_code = era.cop.code

            if era.imp_supplier_contract.id in self.era_map_supplier_contracts:
                self.supplier_contract = Contract.get_supplier_by_id(
                    sess,
                    self.era_map_supplier_contracts[
                        era.imp_supplier_contract.id])
            else:
                self.supplier_contract = era.imp_supplier_contract

            if era.dc_contract.id in self.era_map_dc_contracts:
                self.dc_contract = Contract.get_dc_by_id(
                    sess, self.era_map_dc_contracts[era.dc_contract.id])
            else:
                self.dc_contract = era.dc_contract

            if era.mop_contract.id in self.era_map_mop_contracts:
                self.mop_contract = Contract.get_mop_by_id(
                    sess, self.era_map_mop_contracts[era.mop_contract.id])
            else:
                self.mop_contract = era.mop_contract

            self.is_import = True
            self.voltage_level_code = self.llfc.voltage_level.code
            self.is_substation = self.llfc.is_substation
            self.sc = era.imp_sc
            self.gsp_group_code = self.supply.gsp_group.code

        supply_ids = set(
            s.id for s in sess.query(Supply).join(Era).join(SiteEra).
            join(Source).filter(
                SiteEra.site == site, Era.start_date <= self.history_finish,
                SiteEra.is_physical, Source.code != 'sub', or_(
                    Era.finish_date == null(),
                    Era.finish_date >= self.history_start)).distinct().all())
        if len(supply_ids) == 0:
            rs = iter([])
        else:
            rs = iter(
                sess.query(
                    cast(HhDatum.value, Float), HhDatum.start_date,
                    Channel.imp_related, Source.code).join(Channel).join(Era).
                join(Supply).join(Source).filter(
                    Channel.channel_type == 'ACTIVE',
                    HhDatum.start_date >= self.history_start,
                    HhDatum.start_date <= self.history_finish,
                    Supply.id.in_(list(supply_ids))).order_by(
                        HhDatum.start_date))

        hh_value, hh_start_date, imp_related, source_code = next(
            rs, (None, None, None, None))
        hist_map = {}

        for hist_date in hh_range(
                self.caches, self.history_start, self.history_finish):
            export_net_kwh = 0
            import_net_kwh = 0
            export_gen_kwh = 0
            import_gen_kwh = 0
            import_3rd_party_kwh = 0
            export_3rd_party_kwh = 0
            while hh_start_date == hist_date:
                if not imp_related and source_code in ('net', 'gen-net'):
                    export_net_kwh += hh_value
                if imp_related and source_code in ('net', 'gen-net'):
                    import_net_kwh += hh_value
                if (imp_related and source_code == 'gen') or \
                        (not imp_related and source_code == 'gen-net'):
                    import_gen_kwh += hh_value
                if (not imp_related and source_code == 'gen') or \
                        (imp_related and source_code == 'gen-net'):
                    export_gen_kwh += hh_value
                if (imp_related and source_code == '3rd-party') or (
                        not imp_related and
                        source_code == '3rd-party-reverse'):
                    import_3rd_party_kwh += hh_value
                if (not imp_related and source_code == '3rd-party') or (
                        imp_related and
                        source_code == '3rd-party-reverse'):
                    export_3rd_party_kwh += hh_value

                hh_value, hh_start_date, imp_related, source_code = next(
                    rs, (None, None, None, None))

            hh_values = {
                'status': 'E', 'hist-import-net-kwh': import_net_kwh,
                'hist-export-net-kwh': export_net_kwh,
                'hist-import-gen-kwh': import_gen_kwh,
                'hist-export-gen-kwh': export_gen_kwh,
                'hist-import-3rd-party-kwh': import_3rd_party_kwh,
                'hist-export-3rd-party-kwh': export_3rd_party_kwh,
                'hist-used-3rd-party-kwh':
                    import_3rd_party_kwh - export_3rd_party_kwh}

            hh_values['used-3rd-party-kwh'] = \
                hh_values['hist-used-3rd-party-kwh']
            hh_values['hist-kwh'] = hh_values['hist-used-gen-msp-kwh'] = \
                hh_values['hist-import-gen-kwh'] - \
                hh_values['hist-export-gen-kwh'] - \
                hh_values['hist-export-net-kwh']

            hh_values['msp-kwh'] = hh_values['used-gen-msp-kwh'] \
                = hh_values['hist-used-gen-msp-kwh']
            for cat_kwh, hist_cat_kwh in lec_cats:
                hh_values[cat_kwh] = hh_values[hist_cat_kwh]

            hh_values['hist-used-kwh'] = \
                hh_values['hist-used-gen-msp-kwh'] + \
                hh_values['hist-import-net-kwh'] + \
                hh_values['hist-used-3rd-party-kwh']

            hh_values['used-kwh'] = hh_values['hist-used-kwh']
            hh_values['import-net-kwh'] = hh_values['hist-import-net-kwh']
            hh_values['msp-kw'] = hh_values['used-gen-msp-kw'] = \
                hh_values['used-gen-msp-kwh'] * 2

            hist_map[hist_date] = hh_values

        for dtm in datum_range(
                sess, self.caches, self.years_back, start_date, finish_date):
            datum = dtm.copy()
            datum.update(hist_map[datum['hist-start']])
            self.hh_data.append(datum)

        if self.deltas is not None:
            for hh in self.hh_data:
                try:
                    delt_hh = self.deltas['hhs'][hh['start-date']]
                    hh['import-net-kwh'] = delt_hh['import-net-kwh']
                    hh['export-net-kwh'] = delt_hh['export-net-kwh']
                    hh['import-gen-kwh'] = delt_hh['import-gen-kwh']
                    hh['msp-kwh'] = delt_hh['msp-kwh']
                    hh['used-kwh'] = delt_hh['used-kwh']
                    hh['msp-kw'] = hh['msp-kwh'] * 2
                except KeyError:
                    pass

    def revolve_to_3rd_party_used(self):
        for hh in self.hh_data:
            hh['msp-kwh'] = hh['used-3rd-party-kwh']
            hh['msp-kw'] = hh['msp-kwh'] * 2
            hh['hist-kwh'] = hh['hist-import-3rd-party-kwh'] - \
                hh['hist-export-3rd-party-kwh']
            hh['hist-kw'] = hh['hist-kwh'] * 2
        self.stream_focus = '3rd-party-used'

    def revolve_to_gen_used(self):
        for hh in self.hh_data:
            hh['msp-kwh'] = hh['used-gen-msp-kwh']
            hh['msp-kw'] = hh['msp-kwh'] * 2
            hh['hist-kwh'] = hh['hist-used-gen-msp-kwh']
            hh['hist-kw'] = hh['hist-kwh'] * 2
        self.stream_focus = 'gen-used'


ACTUAL_READ_TYPES = ['N', 'N3', 'C', 'X', 'CP']


class SupplySource(DataSource):
    def __init__(
            self, sess, start_date, finish_date, forecast_date, era, is_import,
            caches, bill=None, era_maps=None, deltas=None):
        DataSource.__init__(
            self, sess, start_date, finish_date, forecast_date, caches,
            era_maps, deltas=deltas)

        self.is_displaced = False
        self.bill = bill
        if self.bill is not None:
            self.bill_start = bill.start_date
            self.bill_finish = bill.finish_date
            self.is_last_bill_gen = \
                not self.bill_finish < self.start_date and not \
                self.bill_finish > self.finish_date

        self.site = None
        self.supply = era.supply
        self.source_code = self.supply.source.code
        self.dno = self.supply.dno
        self.dno_code = self.dno.dno_code
        self.era = era

        era_map_llfcs = self.era_map_llfcs.get(self.dno_code, {})
        self.is_import = is_import
        if is_import:
            self.mpan_core = era.imp_mpan_core

            if era.imp_llfc.code in era_map_llfcs:
                llfc_code = era_map_llfcs[era.imp_llfc.code]
                self.llfc = self.dno.get_llfc_by_code(
                    sess, llfc_code, start_date)
            else:
                self.llfc = era.imp_llfc

            self.sc = era.imp_sc
            self.supplier_account = era.imp_supplier_account

            if era.imp_supplier_contract.id in self.era_map_supplier_contracts:
                self.supplier_contract = Contract.get_supplier_by_id(
                    sess,
                    self.era_map_supplier_contracts[
                        era.imp_supplier_contract.id])
            else:
                self.supplier_contract = era.imp_supplier_contract
        else:
            self.mpan_core = era.exp_mpan_core

            if era.exp_llfc.code in era_map_llfcs:
                llfc_code = era_map_llfcs[era.exp_llfc.code]
                self.llfc = self.dno.get_llfc_by_code(
                    sess, llfc_code, start_date)
            else:
                self.llfc = era.exp_llfc

            self.sc = era.exp_sc
            self.supplier_account = era.exp_supplier_account

            if era.exp_supplier_contract.id in self.era_map_supplier_contracts:
                self.supplier_contract = Contract.get_supplier_by_id(
                    sess,
                    self.era_map_supplier_contracts[
                        era.exp_supplier_contract.id])
            else:
                self.supplier_contract = era.exp_supplier_contract

        if era.dc_contract.id in self.era_map_dc_contracts:
            self.dc_contract = Contract.get_dc_by_id(
                sess, self.era_map_dc_contracts[era.dc_contract.id])
        else:
            self.dc_contract = era.dc_contract

        if era.mop_contract.id in self.era_map_mop_contracts:
            self.mop_contract = Contract.get_mop_by_id(
                sess, self.era_map_mop_contracts[era.mop_contract.id])
        else:
            self.mop_contract = era.mop_contract

        if era.cop.code in self.era_map_cops:
            self.cop_code = self.era_map_cops[era.cop.code]
        else:
            self.cop_code = era.cop.code

        self.id = self.mpan_core
        self.llfc_code = self.llfc.code
        self.voltage_level = self.llfc.voltage_level
        self.voltage_level_code = self.voltage_level.code
        self.is_substation = self.llfc.is_substation
        self.is_new = False
        self.mtc = self.era.mtc
        self.meter_type = self.mtc.meter_type
        self.meter_type_code = self.meter_type.code
        self.ssc = self.era.ssc

        self.ssc_code = None if self.ssc is None else self.ssc.code

        if era.pc.code in self.era_map_pcs:
            self.pc_code = self.era_map_pcs[era.pc.code]
        else:
            self.pc_code = era.pc.code

        self.gsp_group_code = self.supply.gsp_group.code

        self.measurement_type = era.make_meter_category()

        self.consumption_info = ''
        hist_map = {}

        if self.years_back == 0:
            hist_eras = [self.era]
        else:
            hist_eras = sess.query(Era).filter(
                Era.supply == self.supply,
                Era.start_date <= self.history_finish,
                or_(
                    Era.finish_date == null(),
                    Era.finish_date >= self.history_start)).order_by(
                Era.start_date)
            if self.is_import:
                hist_eras = hist_eras.filter(Era.imp_mpan_core != null())
            else:
                hist_eras = hist_eras.filter(Era.exp_mpan_core != null())
            hist_eras = hist_eras.options(
                joinedload(Era.pc), joinedload(Era.channels),
                joinedload(Era.mtc).joinedload(Mtc.meter_type)).all()
            if len(hist_eras) == 0:
                hist_eras = sess.query(Era).filter(
                    Era.supply == self.supply).order_by(Era.start_date)
                if self.is_import:
                    hist_eras = hist_eras.filter(Era.imp_mpan_core != null())
                else:
                    hist_eras = hist_eras.filter(Era.exp_mpan_core != null())
                hist_eras = hist_eras.limit(1).all()

        for i, hist_era in enumerate(hist_eras):
            if self.is_import:
                hist_mpan_core = hist_era.imp_mpan_core
            else:
                hist_mpan_core = hist_era.exp_mpan_core

            if hist_mpan_core is None:
                continue

            if self.history_start > hist_era.start_date:
                chunk_start = self.history_start
            else:
                if i == 0:
                    chunk_start = self.history_start
                else:
                    chunk_start = hist_era.start_date

            chunk_finish = hh_min(self.history_finish, hist_era.finish_date)

            hist_measurement_type = hist_era.make_meter_category()
            if hist_measurement_type == 'unmetered':

                kwh = hist_era.imp_sc * 60 * 30 / (
                    Datetime(chunk_start.year + 1, 1, 1) -
                    Datetime(chunk_start.year, 1, 1)).total_seconds()

                for tpr in sess.query(Tpr).join(MeasurementRequirement).filter(
                        MeasurementRequirement.ssc == hist_era.ssc):
                    for hist_date in hh_range(
                            self.caches, chunk_start, chunk_finish):
                        if is_tpr(sess, self.caches, tpr.code, hist_date):
                            hist_map[hist_date] = {
                                'msp-kw': kwh * 2, 'msp-kwh': kwh,
                                'hist-kwh': kwh, 'imp-msp-kvarh': 0,
                                'imp-msp-kvar': 0, 'exp-msp-kvarh': 0,
                                'exp-msp-kvar': 0}
            elif self.bill is None and hist_measurement_type == 'nhh':
                read_list = []
                read_keys = {}
                pairs = []

                prior_pres_reads = iter(
                    sess.query(RegisterRead).join(Bill).join(BillType)
                    .join(RegisterRead.present_type).filter(
                        RegisterRead.units == 0,
                        ReadType.code.in_(ACTUAL_READ_TYPES),
                        Bill.supply == self.supply,
                        RegisterRead.present_date < chunk_start,
                        BillType.code != 'W').order_by(
                        RegisterRead.present_date.desc()).options(
                            joinedload(RegisterRead.bill)))
                prior_prev_reads = iter(
                    sess.query(RegisterRead).join(Bill).join(BillType)
                    .join(RegisterRead.previous_type).filter(
                        RegisterRead.units == 0,
                        ReadType.code.in_(ACTUAL_READ_TYPES),
                        Bill.supply == self.supply,
                        RegisterRead.previous_date < chunk_start,
                        BillType.code != 'W').order_by(
                        RegisterRead.previous_date.desc()).options(
                            joinedload(RegisterRead.bill)))
                next_pres_reads = iter(
                    sess.query(RegisterRead).join(Bill).join(BillType)
                    .join(RegisterRead.present_type).filter(
                        RegisterRead.units == 0,
                        ReadType.code.in_(ACTUAL_READ_TYPES),
                        Bill.supply == self.supply,
                        RegisterRead.present_date >= chunk_start,
                        BillType.code != 'W').order_by(
                        RegisterRead.present_date).options(
                            joinedload(RegisterRead.bill)))
                next_prev_reads = iter(
                    sess.query(RegisterRead).join(Bill).join(BillType)
                    .join(RegisterRead.previous_type).filter(
                        RegisterRead.units == 0,
                        ReadType.code.in_(ACTUAL_READ_TYPES),
                        Bill.supply == self.supply,
                        RegisterRead.previous_date >= chunk_start,
                        BillType.code != 'W').order_by(
                        RegisterRead.previous_date).options(
                            joinedload(RegisterRead.bill)))

                for is_forwards in [False, True]:
                    if is_forwards:
                        pres_reads = next_pres_reads
                        prev_reads = next_prev_reads
                        read_list.reverse()
                    else:
                        pres_reads = prior_pres_reads
                        prev_reads = prior_prev_reads

                    prime_pres_read = None
                    prime_prev_read = None
                    while True:

                        while prime_pres_read is None:
                            try:
                                pres_read = next(pres_reads)
                            except StopIteration:
                                break

                            pres_date = pres_read.present_date
                            pres_msn = pres_read.msn
                            read_key = '_'.join([str(pres_date), pres_msn])
                            if read_key in read_keys:
                                continue

                            pres_bill = sess.query(Bill).join(BillType).filter(
                                Bill.supply == self.supply, Bill.reads.any(),
                                Bill.finish_date >= pres_read.bill.start_date,
                                Bill.start_date <= pres_read.bill.finish_date,
                                BillType.code != 'W').order_by(
                                Bill.issue_date.desc(),
                                BillType.code).first()

                            if pres_bill.id != pres_read.bill_id:
                                continue

                            reads = dict(
                                (
                                    read.tpr.code,
                                    float(read.present_value) *
                                    float(read.coefficient))
                                for read in sess.query(RegisterRead).filter(
                                    RegisterRead.units == 0,
                                    RegisterRead.bill == pres_bill,
                                    RegisterRead.present_date == pres_date,
                                    RegisterRead.msn == pres_msn).options(
                                    joinedload('tpr')))

                            prime_pres_read = {
                                'date': pres_date, 'reads': reads,
                                'msn': pres_msn}
                            read_keys[read_key] = None

                        while prime_prev_read is None:

                            try:
                                prev_read = next(prev_reads)
                            except StopIteration:
                                break

                            prev_date = prev_read.previous_date
                            prev_msn = prev_read.msn
                            read_key = '_'.join([str(prev_date), prev_msn])
                            if read_key in read_keys:
                                continue

                            prev_bill = sess.query(Bill).join(BillType).filter(
                                Bill.supply == self.supply, Bill.reads.any(),
                                Bill.finish_date >= prev_read.bill.start_date,
                                Bill.start_date <= prev_read.bill.finish_date,
                                BillType.code != 'W').order_by(
                                Bill.issue_date.desc(), BillType.code).first()
                            if prev_bill.id != prev_read.bill_id:
                                continue

                            reads = dict(
                                (
                                    read.tpr.code,
                                    float(read.previous_value) *
                                    float(read.coefficient))
                                for read in sess.query(RegisterRead).filter(
                                    RegisterRead.units == 0,
                                    RegisterRead.bill == prev_bill,
                                    RegisterRead.previous_date == prev_date,
                                    RegisterRead.msn == prev_msn).options(
                                    joinedload('tpr')))

                            prime_prev_read = {
                                'date': prev_date, 'reads': reads,
                                'msn': prev_msn}
                            read_keys[read_key] = None

                        if prime_pres_read is None and prime_prev_read is None:
                            break
                        elif prime_pres_read is None:
                            read_list.append(prime_prev_read)
                            prime_prev_read = None
                        elif prime_prev_read is None:
                            read_list.append(prime_pres_read)
                            prime_pres_read = None
                        else:
                            if is_forwards:
                                if prime_prev_read['date'] == \
                                        prime_pres_read['date'] or \
                                        prime_pres_read['date'] < \
                                        prime_prev_read['date']:
                                    read_list.append(prime_pres_read)
                                    prime_pres_read = None
                                else:
                                    read_list.append(prime_prev_read)
                                    prime_prev_read = None
                            else:
                                if prime_prev_read['date'] == \
                                        prime_pres_read['date'] or \
                                        prime_prev_read['date'] > \
                                        prime_pres_read['date']:
                                    read_list.append(prime_prev_read)
                                    prime_prev_read = None
                                else:
                                    read_list.append(prime_pres_read)
                                    prime_pres_read = None

                        if len(read_list) > 1:
                            if is_forwards:
                                aft_read = read_list[-2]
                                fore_read = read_list[-1]
                            else:
                                aft_read = read_list[-1]
                                fore_read = read_list[-2]

                            if aft_read['msn'] == fore_read['msn'] and \
                                    aft_read['reads'].keys() == \
                                    fore_read['reads'].keys():
                                num_hh = (
                                    fore_read['date'] - aft_read['date']
                                    ).total_seconds() / (30 * 60)

                                tprs = {}
                                for tpr_code, initial_val in \
                                        aft_read['reads'].items():
                                    end_val = fore_read['reads'][tpr_code]
                                    kwh = end_val - initial_val

                                    if kwh < 0:
                                        digits = int(log10(initial_val)) + 1
                                        kwh = 10 ** digits + kwh

                                    tprs[tpr_code] = kwh / num_hh

                                pairs.append(
                                    {
                                        'start-date': aft_read['date'],
                                        'finish-date': fore_read['date'] + HH,
                                        'tprs': tprs})

                                if len(pairs) > 0 and (
                                        not is_forwards or (
                                            is_forwards and
                                            read_list[-1]['date'] >
                                            chunk_finish)):
                                        break

                self.consumption_info += 'read list - \n' + \
                    str(list(list(sorted(r.items())) for r in read_list)) \
                    + "\n"
                if len(pairs) == 0:
                    pairs.append(
                        {
                            'start-date': chunk_start,
                            'finish-date': chunk_finish,
                            'tprs': {'00001': 0}})

                # smooth
                for i in range(1, len(pairs)):
                    pairs[i - 1]['finish-date'] = pairs[i]['start-date'] - HH

                # stretch
                if pairs[0]['start-date'] > chunk_start:
                    pairs[0]['start-date'] = chunk_start

                if pairs[-1]['finish-date'] < chunk_finish:
                    pairs[-1]['finish-date'] = chunk_finish

                # chop
                pairs = [
                    pair for pair in pairs
                    if not pair['start-date'] > chunk_finish and not
                    pair['finish-date'] < chunk_start]

                # squash
                if pairs[0]['start-date'] < chunk_start:
                    pairs[0]['start-date'] = chunk_start

                if pairs[-1]['finish-date'] > chunk_finish:
                    pairs[-1]['finish-date'] = chunk_finish

                self.consumption_info += 'pairs - \n' + \
                    str(list(list(sorted(p.items())) for p in pairs))

                for pair in pairs:
                    pair_hhs = (
                        pair['finish-date'] + HH - pair['start-date']
                        ).total_seconds() / (60 * 30)
                    for tpr_code, pair_kwh in pair['tprs'].items():
                        hh_part = {}

                        for hh_date in hh_range(
                                self.caches, pair['start-date'],
                                pair['finish-date']):
                            if is_tpr(sess, self.caches, tpr_code, hh_date):
                                hh_part[hh_date] = {}

                        kwh = pair_kwh * pair_hhs / len(hh_part) \
                            if len(hh_part) > 0 else 0

                        for datum in hh_part.values():
                            datum.update(
                                {
                                    'msp-kw': kwh * 2, 'msp-kwh': kwh,
                                    'hist-kwh': kwh, 'imp-msp-kvar': 0,
                                    'imp-msp-kvarh': 0, 'exp-msp-kvar': 0,
                                    'exp-msp-kvarh': 0})
                        hist_map.update(hh_part)
            elif self.bill is not None and hist_measurement_type in (
                    'nhh', 'amr'):
                hhd = {}
                for hh_date in hh_range(
                        self.caches, chunk_start, chunk_finish):
                    hhd[hh_date] = {
                        'status': 'X', 'imp-msp-kvarh': 0,
                        'imp-msp-kvar': 0, 'exp-msp-kvarh': 0,
                        'exp-msp-kvar': 0, 'msp-kw': 0, 'msp-kwh': 0,
                        'hist-kwh': 0}

                tpr_codes = [
                    t[0] for t in sess.query(Tpr.code).
                    join(MeasurementRequirement).filter(
                        MeasurementRequirement.ssc == self.ssc)]

                bills = dict(
                    (b.id, b) for b in sess.query(Bill).filter(
                        Bill.supply == self.supply, Bill.reads.any(),
                        Bill.start_date <= chunk_finish,
                        Bill.finish_date >= chunk_start).order_by(
                        Bill.issue_date.desc(), Bill.start_date))
                while True:
                    to_del = None
                    for a, b in combinations(bills.values(), 2):
                        if all(
                                (
                                    a.start_date == b.start_date,
                                    a.finish_date == b.finish_date,
                                    a.kwh == -1 * b.kwh, a.net == -1 * b.net,
                                    a.vat == -1 * b.vat,
                                    a.gross == -1 * b.gross)):
                            to_del = (a.id, b.id)
                            break
                    if to_del is None:
                        break
                    else:
                        for k in to_del:
                            del bills[k]

                prev_type_alias = aliased(ReadType)
                pres_type_alias = aliased(ReadType)
                ct_tz = timezone('Europe/London')
                for bill in bills.values():
                    kws = defaultdict(int)
                    for coefficient, previous_date, previous_value, \
                            previous_type, present_date, present_value, \
                            present_type, tpr_code in sess.query(
                            cast(RegisterRead.coefficient, Float),
                            RegisterRead.previous_date,
                            cast(RegisterRead.previous_value, Float),
                            prev_type_alias.code,
                            RegisterRead.present_date,
                            cast(RegisterRead.present_value, Float),
                            pres_type_alias.code, Tpr.code).join(Tpr).join(
                                prev_type_alias,
                                RegisterRead.previous_type_id ==
                                prev_type_alias.id).join(
                            pres_type_alias,
                            RegisterRead.present_type_id ==
                            pres_type_alias.id).filter(
                            RegisterRead.bill == bill,
                            RegisterRead.units == 0).order_by(
                                RegisterRead.present_date):

                        if tpr_code not in tpr_codes:
                            self._add_problem(
                                "The TPR " + str(tpr_code) +
                                " from the register read does not match any " +
                                "of the TPRs (" + ', '.join(tpr_codes) +
                                ") associated with the MPAN.")

                        if present_date > bill.finish_date:
                            self._add_problem(
                                "There's a read after the end of the bill!")
                        advance = present_value - previous_value
                        if advance < 0:
                            self._add_problem("Clocked?")
                            digits = int(log10(previous_value)) + 1
                            advance = 10 ** digits - previous_value + \
                                present_value

                        kwh = advance * coefficient
                        self.consumption_info += "dumb nhh kwh for " + \
                            tpr_code + " is " + str(kwh) + "\n"

                        kws[tpr_code] += kwh

                    for tpr_code, kwh in kws.items():
                        tpr_dict = _tpr_dict(sess, self.caches, tpr_code)
                        days_of_week = tpr_dict['days-of-week']

                        tz = utc if tpr_dict['is-gmt'] else ct_tz

                        if present_type in ACTUAL_READ_TYPES \
                                and previous_type in ACTUAL_READ_TYPES:
                            status = 'A'
                        else:
                            status = 'E'

                        year_delta = relativedelta(years=self.years_back)
                        hh_part = {}
                        for hh_date in hh_range(
                                self.caches, bill.start_date,
                                bill.finish_date):
                            dt = to_tz(tz, hh_date) + year_delta
                            decimal_hour = dt.hour + dt.minute / 60
                            fractional_month = dt.month * 100 + dt.day
                            for ci in days_of_week[dt.weekday()]:

                                if (
                                        (
                                            ci['start-hour'] <
                                            ci['end-hour'] and
                                            ci['start-hour'] <=
                                            decimal_hour < ci['end-hour']) or
                                        (
                                            ci['start-hour'] >=
                                            ci['end-hour'] and (
                                                ci['start-hour'] <=
                                                decimal_hour or
                                                decimal_hour <
                                                ci['end-hour']))) \
                                        and ci['start-month'] <= \
                                        fractional_month <= ci['end-month']:

                                    hh_part[hh_date] = {'status': status}
                                    break

                        num_hh = len(hh_part)
                        if num_hh > 0:
                            rate = kwh / num_hh
                            for d, h in hh_part.items():
                                if chunk_start <= d <= chunk_finish:
                                    hhd_datum = hhd[d]
                                    hhd_datum['msp-kw'] += rate * 2
                                    hhd_datum['msp-kwh'] += rate
                                    hhd_datum['hist-kwh'] += rate
                                    if hhd_datum['status'] in ('X', 'A'):
                                        hhd_datum['status'] = h['status']
                        elif kwh > 0:
                            self._add_problem(
                                "For the TPR code " + tpr_code +
                                " the bill says that there are " + str(kwh) +
                                " kWh, but the time of the TPR doesn't cover "
                                "the time between the register reads.")

                hist_map.update(hhd)
            elif hist_measurement_type in ('hh', 'amr'):
                has_exp_active = False
                has_imp_related_reactive = False
                has_exp_related_reactive = False
                for channel in hist_era.channels:
                    if not channel.imp_related \
                            and channel.channel_type == 'ACTIVE':
                        has_exp_active = True
                    if channel.imp_related and channel.channel_type in (
                            'REACTIVE_IMP', 'REACTIVE_EXP'):
                        has_imp_related_reactive = True
                    if not channel.imp_related and channel.channel_type in (
                            'REACTIVE_IMP', 'REACTIVE_EXP'):
                        has_exp_related_reactive = True

                if has_exp_active and not has_exp_related_reactive \
                        and has_imp_related_reactive:
                    #  old style
                    data = iter(sess.execute("""
select sum(cast(coalesce(kwh.value, 0) as double precision)),
    sum(cast(coalesce(anti_kwh.value, 0) as double precision)),
    max(kwh.status),
    sum(cast(coalesce(reactive_imp.value, 0) as double precision)),
    sum(cast(coalesce(reactive_exp.value, 0) as double precision)),
    hh_datum.start_date
from hh_datum
    join channel on (hh_datum.channel_id = channel.id)
    left join hh_datum as kwh
        on (hh_datum.id = kwh.id and channel.channel_type = 'ACTIVE'
            and channel.imp_related = :is_import)
    left join hh_datum as anti_kwh
        on (hh_datum.id = anti_kwh.id and channel.channel_type = 'ACTIVE'
            and channel.imp_related != :is_import)
    left join hh_datum as reactive_imp
        on (hh_datum.id = reactive_imp.id
            and channel.channel_type = 'REACTIVE_IMP'
            and channel.imp_related is true)
    left join hh_datum as reactive_exp
        on (hh_datum.id = reactive_exp.id
            and channel.channel_type = 'REACTIVE_EXP'
            and channel.imp_related is true)
where channel.era_id = :era_id and hh_datum.start_date >= :start_date
    and hh_datum.start_date <= :finish_date
group by hh_datum.start_date
order by hh_datum.start_date
""", params={
                        'era_id': hist_era.id,
                        'start_date': chunk_start,
                        'finish_date': chunk_finish,
                        'is_import': self.is_import}))
                    (
                        msp_kwh, anti_msp_kwh, status, imp_kvarh, exp_kvarh,
                        hist_start) = next(
                            data, (None, None, None, None, None, None))

                    for hh_date in hh_range(
                            self.caches, chunk_start, chunk_finish):
                        if hh_date == hist_start:
                            if not (msp_kwh > 0 and anti_msp_kwh == 0):
                                imp_kvarh = 0
                                exp_kvarh = 0

                            hist_map[hh_date] = {
                                'status': status,
                                'imp-msp-kvarh': imp_kvarh,
                                'imp-msp-kvar': imp_kvarh * 2,
                                'exp-msp-kvarh': exp_kvarh,
                                'exp-msp-kvar': exp_kvarh * 2,
                                'msp-kw': msp_kwh * 2, 'msp-kwh': msp_kwh,
                                'hist-kwh': msp_kwh}
                            (
                                msp_kwh, anti_msp_kwh, status, imp_kvarh,
                                exp_kvarh, hist_start) = next(
                                data, (None, None, None, None, None, None))
                else:
                    # new style
                    data = sess.execute(
                        "select "
                        "    start_date, "
                        "    status, "
                        "    active, "
                        "    coalesce(reactive_imp, 0) as reactive_imp, "
                        "    coalesce(reactive_exp, 0) as reactive_exp "
                        "from crosstab("
                        "    :sql, "
                        "    'SELECT unnest(enum_range(NULL::channel_type))') "
                        "as ct( "
                        "    start_date timestamp with time zone, "
                        "    status character varying, "
                        "    active double precision, "
                        "    reactive_imp double precision, "
                        "    reactive_exp double precision); ",
                        params={
                            'sql':
                            "select "
                            "    hh_datum.start_date, "
                            "    hh_datum.status, "
                            "    channel.channel_type, "
                            "    cast(hh_datum.value as double precision) "
                            "from hh_datum join channel "
                            "    on (hh_datum.channel_id = channel.id) "
                            "where channel.era_id = " + str(hist_era.id) +
                            "    and channel.imp_related = " +
                            str(self.is_import) +
                            "    and hh_datum.start_date >= '" +
                            hh_format(chunk_start) + "+00'"
                            "    and hh_datum.start_date <= '" +
                            hh_format(chunk_finish) + "+00'"
                            "    order by 1,3"})
                    for (
                            hist_start, status, msp_kwh, imp_kvarh,
                            exp_kvarh) in data:

                        datum = {
                            'imp-msp-kvarh': imp_kvarh,
                            'imp-msp-kvar': imp_kvarh * 2,
                            'exp-msp-kvarh': exp_kvarh,
                            'exp-msp-kvar': exp_kvarh * 2}
                        if msp_kwh is not None:
                            datum['status'] = status
                            datum['hist-kwh'] = msp_kwh
                            datum['msp-kwh'] = msp_kwh
                            datum['msp-kw'] = msp_kwh * 2

                        hist_map[hist_start] = datum
            else:
                raise BadRequest("gen type not recognized")

        self.hh_data.extend(
            {**d, **hist_map.get(d['hist-start'], {})} for d in datum_range(
                sess, self.caches, self.years_back, start_date, finish_date))

        if self.deltas is not None:
            site_deltas = self.deltas['site']

            try:
                sup_deltas = self.deltas[self.supply.id]
            except KeyError:
                sup_deltas = self.deltas[self.supply.id] = {}

            for hh in self.hh_data:
                hh_start = hh['start-date']
                if hh_start in sup_deltas:
                    delt = sup_deltas[hh_start]
                elif hh_start in site_deltas:
                    delt = sup_deltas[hh_start] = site_deltas[hh_start]
                    del site_deltas[hh_start]
                else:
                    continue

                hh['msp-kwh'] += delt
                hh['msp-kw'] += delt * 2
