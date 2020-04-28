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
    ClockInterval, Mtc, Llfc, hh_before, hh_after, Ssc)
from chellow.utils import (
    HH, hh_format, hh_max, hh_range, hh_min, utc_datetime, utc_datetime_now,
    to_tz, to_ct, loads, PropDict, YEAR, ct_datetime, ct_datetime_now, to_utc,
    c_months_u)
import chellow.utils
import chellow.bank_holidays
from itertools import combinations, count
from types import MappingProxyType
from functools import lru_cache
from zish import dumps


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
            year_after = date + YEAR
            year_before = date - YEAR

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
                    cstart = year_before
                    cfinish = min(year_after, rs.start_date - HH)
                else:
                    cstart = max(rs.finish_date + HH, year_before)
                    cfinish = year_after
            else:
                cstart = max(rs.start_date, year_before)
                if rs.finish_date is None:
                    cfinish = year_after
                else:
                    cfinish = min(rs.finish_date, year_after)

            market_role_code = rs.contract.market_role.code
            if market_role_code == "M":
                seg = 'mop_rate_scripts/'
            elif market_role_code == "C":
                seg = 'dc_rate_scripts/'
            elif market_role_code == "X":
                seg = 'supplier_rate_scripts/'
            elif market_role_code == "Z":
                seg = 'non_core_rate_scripts/'
            else:
                raise Exception(
                    "The market role code " + market_role_code +
                    " isn't recognized.")

            vals = PropDict(
                "the rate script " + chellow.utils.url_root + seg +
                str(rs.id) + " ", loads(rs.script), [])
            for dt in hh_range(caches, cstart, cfinish):
                if dt not in cont_cache:
                    cont_cache[dt] = vals

            return vals


def forecast_date():
    now = ct_datetime_now()
    return to_utc(ct_datetime(now.year, now.month, 1))


def displaced_era(
        sess, caches, site, start_date, finish_date, forecast_date,
        has_scenario_generation=False):
    start_date_ct = to_ct(start_date)
    finish_date_ct = to_ct(finish_date)
    if (start_date_ct.year, start_date_ct.month) != \
            (finish_date_ct.year, finish_date_ct.month):
        raise BadRequest(
            "The start and end dates of a displaced period must be within the "
            "same month")
    t = get_times(start_date, finish_date, forecast_date)
    hs = to_ct(t['history-start'])
    month_start, month_finish = next(
        c_months_u(start_year=hs.year, start_month=hs.month))
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
                '_'.join(
                    (
                        era.pc.code, str(era.exp_mpan_core is None),
                        hh_format(era.start_date), era.imp_mpan_core))] = era

    if (has_displaced or has_scenario_generation) and len(eras) > 0:
        era = eras[sorted(eras.keys())[0]]
    else:
        era = None
    return era


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
        self.full_channels = True
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
        self.supplier_bill_hhs = {}
        self.mop_bill_hhs = {}
        self.dc_bill_hhs = {}

        self.era_maps = {} if era_maps is None else era_maps
        era_map = {}
        for em_start, em in sorted(self.era_maps.items()):
            if em_start <= start_date:
                era_map = em
                break
        self.era_map = PropDict("scenario properties", era_map)
        self.era_map_llfcs = self.era_map.get('llfcs', {})
        self.era_map_pcs = self.era_map.get('pcs', {})
        self.era_map_sscs = self.era_map.get('sscs', {})
        self.era_map_supplier_contracts = self.era_map.get(
            'supplier_contracts', {})
        self.era_map_dc_contracts = self.era_map.get('dc_contracts', {})
        self.era_map_mop_contracts = self.era_map.get('mop_contracts', {})
        self.era_map_cops = self.era_map.get('cops', {})

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

            era_ssc_code = None if era.ssc is None else era.ssc.code
            if era_ssc_code in self.era_map_sscs:
                self.ssc_code = self.era_map_sscs[era_ssc_code]
            else:
                self.ssc_code = era_ssc_code

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

            if 'sc' in self.era_map:
                self.sc = self.era_map['sc']
            else:
                self.sc = era.imp_sc

            self.properties = self.era_map.get('properties_overwritten', {})
            self.properties.update(era.props)
            self.properties.update(
                self.era_map.get('properties_overwrite', {}))

            self.is_import = True
            self.voltage_level_code = self.llfc.voltage_level.code
            self.is_substation = self.llfc.is_substation
            self.gsp_group_code = self.supply.gsp_group.code
            self.ssc = self.era.ssc
            self.ssc_code = None if self.ssc is None else self.ssc.code

        self.era_ids = set(
            s.id for s in sess.query(Era).join(SiteEra).join(Supply).
            join(Source).filter(
                SiteEra.site == site, Era.start_date <= self.history_finish,
                SiteEra.is_physical, Source.code != 'sub', or_(
                    Era.finish_date == null(),
                    Era.finish_date >= self.history_start)).all())
        if len(self.era_ids) == 0:
            rs = iter([])
        else:
            rs = iter(
                sess.query(
                    cast(HhDatum.value, Float), HhDatum.start_date,
                    HhDatum.status, Channel.imp_related,
                    Source.code).join(Channel).join(Era).join(Supply).join(
                    Source).filter(
                    Channel.channel_type == 'ACTIVE',
                    HhDatum.start_date >= self.history_start,
                    HhDatum.start_date <= self.history_finish,
                    Era.id.in_(list(self.era_ids))).order_by(
                        HhDatum.start_date))

        hh_value, hh_start_date, status, imp_related, source_code = next(
            rs, (None, None, None, None, None))
        hist_map = {}

        for hist_date in hh_range(
                self.caches, self.history_start, self.history_finish):
            export_net_kwh = 0
            import_net_kwh = 0
            export_gen_kwh = 0
            import_gen_kwh = 0
            import_3rd_party_kwh = 0
            statuses = set()
            export_3rd_party_kwh = 0
            while hh_start_date == hist_date:
                statuses.add(status)
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

                hh_value, hh_start_date, status, imp_related, source_code = \
                    next(rs, (None, None, None, None, None))

            if len(statuses) == 1 and statuses.pop() == 'A':
                status = 'A'
            else:
                status = 'E'

            hh_values = {
                'status': status, 'hist-import-net-kwh': import_net_kwh,
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
            self.supplier_bill_hhs[dtm['start-date']] = {}
            self.mop_bill_hhs[dtm['start-date']] = {}
            self.dc_bill_hhs[dtm['start-date']] = {}

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

    def get_data_sources(self, start_date, finish_date, forecast_date=None):
        if forecast_date is None:
            forecast_date = self.forecast_date

        if all(
                (
                    self.start_date == start_date,
                    self.finish_date == finish_date,
                    forecast_date == self.forecast_date)):
            yield self
        else:
            month_start = utc_datetime(start_date.year, start_date.month)
            while month_start <= finish_date:
                month_finish = month_start + relativedelta(months=1) - HH
                chunk_start = hh_max(month_start, start_date)
                chunk_finish = hh_min(month_finish, finish_date)
                if self.stream_focus == 'gen-used' and \
                        self.era is not None and (
                        self.deltas is None or len(self.deltas['hhs']) == 0):
                    era = displaced_era(
                        self.sess, self.caches, self.site, chunk_start,
                        chunk_finish, forecast_date)
                    if era is None:
                        return
                else:
                    era = self.era

                site_ds = SiteSource(
                    self.sess, self.site, chunk_start, chunk_finish,
                    forecast_date, self.caches, era, self.era_maps,
                    self.deltas)
                if self.stream_focus == '3rd-party-used':
                    site_ds.revolve_to_3rd_party_used()
                month_start += relativedelta(months=1)
                yield site_ds


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
        self.supply_name = self.supply.name
        self.source_code = self.supply.source.code
        self.dno = self.supply.dno
        self.dno_code = self.dno.dno_code
        self.era = era
        if self.supply.generator_type is None:
            self.generator_type_code = None
        else:
            self.generator_type_code = self.supply.generator_type.code

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
            if era.exp_llfc is None:
                self.mpan_core = llfc_key = "new_export"
                llfc_key = "new_export"
            else:
                self.mpan_core = era.exp_mpan_core
                llfc_key = era.exp_llfc.code
            if llfc_key in era_map_llfcs:
                llfc_code = era_map_llfcs[llfc_key]
                self.llfc = self.dno.get_llfc_by_code(
                    sess, llfc_code, start_date)
            else:
                self.llfc = era.exp_llfc

            self.sc = 0 if era.exp_sc is None else era.exp_sc
            self.supplier_account = era.exp_supplier_account

            if era.exp_supplier_contract is None:
                sup_key = "new_export"
            else:
                sup_key = era.exp_supplier_contract.id

            if sup_key in self.era_map_supplier_contracts:
                self.supplier_contract = Contract.get_supplier_by_id(
                    sess, self.era_map_supplier_contracts[sup_key])
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

        self.properties = dict(self.era_map.get('properties_overwritten', {}))
        self.properties.update(era.props)
        self.properties.update(
            self.era_map.get('properties_overwrite', {}))

        self.id = self.mpan_core
        self.msn = era.msn
        self.llfc_code = self.llfc.code
        self.voltage_level = self.llfc.voltage_level
        self.voltage_level_code = self.voltage_level.code
        self.is_substation = self.llfc.is_substation
        self.is_new = False
        self.mtc = self.era.mtc
        self.meter_type = self.mtc.meter_type
        self.meter_type_code = self.meter_type.code

        if era.pc.code in self.era_map_pcs:
            self.pc_code = self.era_map_pcs[era.pc.code]
        else:
            self.pc_code = era.pc.code

        era_ssc_code = None if era.ssc is None else era.ssc.code
        if era_ssc_code in self.era_map_sscs:
            ssc_code = self.era_map_sscs[era_ssc_code]
            if ssc_code is None:
                self.ssc = None
            else:
                self.ssc = Ssc.get_by_code(sess, ssc_code)
        else:
            self.ssc = era.ssc

        self.ssc_code = None if self.ssc is None else self.ssc.code

        self.gsp_group_code = self.supply.gsp_group.code

        self.measurement_type = era.meter_category

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

            hist_measurement_type = hist_era.meter_category

            if hist_measurement_type == 'amr' and self.era_map.get(
                    'use_amr_hh_data', False):
                hist_measurement_type = 'hh'

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
                                'exp-msp-kvar': 0, 'status': 'A',
                                'tpr': tpr.code
                            }

            elif self.bill is None and hist_measurement_type in ('nhh', 'amr'):
                self.consumption_info += _no_bill_nhh(
                    sess, caches, self.supply, chunk_start, chunk_finish,
                    hist_map, forecast_date)
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
                                    hhd_datum['tpr'] = tpr_code
                                    if hhd_datum['status'] in ('X', 'A'):
                                        hhd_datum['status'] = h['status']
                        elif kwh > 0:
                            self._add_problem(
                                "For the TPR code " + tpr_code +
                                " the bill says that there are " + str(kwh) +
                                " kWh, but the time of the TPR doesn't cover "
                                "the time between the register reads.")

                hist_map.update(hhd)
            elif hist_measurement_type == 'hh':
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
                    self.full_channels = False
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
                            hist_map[hh_date] = {
                                'status': status,
                                'imp-msp-kvarh': imp_kvarh,
                                'imp-msp-kvar': imp_kvarh * 2,
                                'exp-msp-kvarh': exp_kvarh,
                                'exp-msp-kvar': exp_kvarh * 2,
                                'msp-kw': msp_kwh * 2,
                                'msp-kwh': msp_kwh,
                                'anti-msp-kwh': anti_msp_kwh,
                                'hist-kwh': msp_kwh,
                            }
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
                            chunk_start.strftime("%Y-%m-%d %H:%M") + "+00'"
                            "    and hh_datum.start_date <= '" +
                            chunk_finish.strftime("%Y-%m-%d %H:%M") + "+00'"
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

        for d in datum_range(
                sess, self.caches, self.years_back, start_date, finish_date):
            datum = d.copy()
            datum.update(hist_map.get(d['hist-start'], {}))
            self.hh_data.append(datum)

            d_start = d['start-date']
            self.supplier_bill_hhs[d_start] = {}
            self.mop_bill_hhs[d_start] = {}
            self.dc_bill_hhs[d_start] = {}

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

    def get_data_sources(self, start_date, finish_date, forecast_date=None):
        if forecast_date is None:
            forecast_date = self.forecast_date

        if all(
                (
                    self.start_date == start_date,
                    self.finish_date == finish_date,
                    forecast_date == self.forecast_date)):
            yield self
        elif self.mpan_core in ("new_export", "new_import"):
            yield SupplySource(
                self.sess, start_date, finish_date, forecast_date, self.era,
                self.is_import, self.caches, self.bill, self.era_maps,
                self.deltas)
        else:
            if self.is_import:
                eras = self.sess.query(Era).filter(
                    Era.supply == self.supply,
                    Era.imp_mpan_core != null(),
                    Era.start_date <= finish_date, or_(
                        Era.finish_date == null(),
                        Era.finish_date >= start_date))
            else:
                eras = self.sess.query(Era).filter(
                    Era.supply == self.supply, Era.exp_mpan_core != null(),
                    Era.start_date <= finish_date, or_(
                        Era.finish_date == null(),
                        Era.finish_date >= start_date))
            eras = eras.options(
                joinedload(Era.ssc),
                joinedload(Era.dc_contract),
                joinedload(Era.mop_contract),
                joinedload(Era.imp_supplier_contract),
                joinedload(Era.exp_supplier_contract),
                joinedload(Era.channels),
                joinedload(Era.imp_llfc).joinedload(Llfc.voltage_level),
                joinedload(Era.exp_llfc).joinedload(Llfc.voltage_level),
                joinedload(Era.cop),
                joinedload(Era.supply).joinedload(Supply.dno),
                joinedload(Era.supply).joinedload(Supply.gsp_group),
                joinedload(Era.supply).joinedload(Supply.source),
                joinedload(Era.mtc).joinedload(Mtc.meter_type),
                joinedload(Era.pc), joinedload(Era.site_eras))

            for era in eras:
                chunk_start = hh_max(era.start_date, start_date)
                chunk_finish = hh_min(era.finish_date, finish_date)

                ds = SupplySource(
                    self.sess, chunk_start, chunk_finish, forecast_date, era,
                    self.is_import, self.caches, self.bill, self.era_maps,
                    self.deltas)
                yield ds


def _find_pair(sess, caches, is_forwards, read_list):
    if len(read_list) < 2:
        return

    if is_forwards:
        back, front = read_list[-2], read_list[-1]
    else:
        back, front = read_list[-1], read_list[-2]

    back_reads = back['reads']
    front_reads = front['reads']
    back_date = back['date']
    front_date = front['date']

    if back['msn'] == front['msn'] and back_reads.keys() == front_reads.keys():
        r = hh_range(caches, back_date, front_date - HH)

        tprs = {}
        for tpr_code, initial_val in back_reads.items():
            end_val = front_reads[tpr_code]
            num_hh = len([d for d in r if is_tpr(sess, caches, tpr_code, d)])

            # Clocked?
            if end_val - initial_val < 0:
                digits = int(log10(initial_val)) + 1
                end_val += 10 ** digits

            kwh = end_val * front['coefficients'][tpr_code] - \
                initial_val * back['coefficients'][tpr_code]

            tprs[tpr_code] = kwh / num_hh if num_hh > 0 else 0

        return {
            'start-date': back_date,
            'tprs': tprs
        }


def _find_hhs(caches, sess, pairs, chunk_start, chunk_finish):
    if len(pairs) == 0:
        pairs.append(
            {
                'start-date': chunk_start,
                'tprs': {'00001': 0}
            })

    # set finish dates
    for i in range(1, len(pairs)):
        pairs[i - 1]['finish-date'] = pairs[i]['start-date'] - HH
    pairs[-1]['finish-date'] = None

    # stretch
    if hh_after(pairs[0]['start-date'], chunk_start):
        pairs[0]['start-date'] = chunk_start

    # chop
    if hh_before(pairs[0]['finish-date'], chunk_start):
        del pairs[0]
    if hh_after(pairs[-1]['start-date'], chunk_finish):
        del pairs[-1]

    # squash
    if hh_before(pairs[0]['start-date'], chunk_start):
        pairs[0]['start-date'] = chunk_start
    if hh_after(pairs[-1]['finish-date'], chunk_finish):
        pairs[-1]['finish-date'] = chunk_finish

    hhs = {}
    for pair in pairs:
        d_range = hh_range(caches, pair['start-date'], pair['finish-date'])
        for tpr_code, kwh in pair['tprs'].items():
            dates = [d for d in d_range if is_tpr(sess, caches, tpr_code, d)]

            for date in dates:
                hhs[date] = {
                    'msp-kw': kwh * 2, 'msp-kwh': kwh, 'hist-kwh': kwh,
                    'imp-msp-kvar': 0, 'imp-msp-kvarh': 0, 'exp-msp-kvar': 0,
                    'exp-msp-kvarh': 0, 'tpr': tpr_code
                }
    return hhs


def _set_status(hhs, read_list, forecast_date):
    THRESHOLD = 31 * 48 * 30 * 60
    rl = [r for r in read_list if r['date'] <= forecast_date]
    for k, v in hhs.items():
        try:
            periods = (abs(r['date'] - k).total_seconds() for r in rl)
            next(p for p in periods if p <= THRESHOLD)
            v['status'] = 'A'
        except StopIteration:
            v['status'] = 'E'


def _read_generator(sess, supply, start, is_forwards, is_prev):
    if is_prev:
        r_typ = RegisterRead.previous_type
        r_dt = RegisterRead.previous_date
        r_vl = RegisterRead.previous_value
    else:
        r_typ = RegisterRead.present_type
        r_dt = RegisterRead.present_date
        r_vl = RegisterRead.present_value

    q = sess.query(RegisterRead).join(Bill).join(BillType).join(r_typ).filter(
        RegisterRead.units == 0, ReadType.code.in_(ACTUAL_READ_TYPES),
        Bill.supply == supply, BillType.code != 'W').options(
            joinedload(RegisterRead.bill))

    if is_forwards:
        q = q.filter(r_dt >= start).order_by(r_dt, RegisterRead.id)
    else:
        q = q.filter(r_dt < start).order_by(r_dt.desc(), RegisterRead.id)

    for offset in count():
        r = q.offset(offset).first()
        if r is None:
            break

        if is_prev:
            dt = r.previous_date
        else:
            dt = r.present_date

        bill = sess.query(Bill).join(BillType).filter(
            Bill.supply == supply, Bill.reads.any(),
            Bill.finish_date >= r.bill.start_date,
            Bill.start_date <= r.bill.finish_date,
            BillType.code != 'W').order_by(
            Bill.issue_date.desc(), BillType.code).first()

        if bill.id != r.bill.id:
            continue

        era = supply.find_era_at(sess, dt)
        if era is None:
            era_coeff = None
        else:
            era_properties = PropDict(
                chellow.utils.url_root + 'eras/' + str(era.id),
                loads(era.properties))
            try:
                era_coeff = float(era_properties['coefficient'])
            except KeyError:
                era_coeff = None

        reads = {}
        coeffs = {}
        for coeff, value, tpr_code in sess.query(
                cast(RegisterRead.coefficient, Float), cast(r_vl, Float),
                Tpr.code).filter(
                RegisterRead.units == 0, RegisterRead.bill == r.bill,
                RegisterRead.msn == r.msn, RegisterRead.tpr_id == Tpr.id,
                r_dt == dt):
            reads[tpr_code] = value
            coeffs[tpr_code] = coeff if era_coeff is None else era_coeff

        yield {
            'date': dt, 'reads': reads, 'coefficients': coeffs, 'msn': r.msn
        }


def _no_bill_nhh(sess, caches, supply, start, finish, hist_map, forecast_date):
    read_list = []
    pairs = []
    read_keys = set()

    for is_forwards in (False, True):
        prev_reads = iter(
            _read_generator(sess, supply, start, is_forwards, True))
        pres_reads = iter(
            _read_generator(sess, supply, start, is_forwards, False))
        if is_forwards:
            read_list.reverse()

        for read in _make_reads(is_forwards, prev_reads, pres_reads):
            read_key = read['date'], read['msn']
            if read_key in read_keys:
                continue
            read_keys.add(read_key)

            read_list.append(read)
            pair = _find_pair(sess, caches, is_forwards, read_list)
            if pair is not None:
                pairs.append(pair)
                if not is_forwards or (
                        is_forwards and read_list[-1]['date'] > finish):
                    break

    consumption_info = 'read list - \n' + dumps(read_list) + "\n"
    hhs = _find_hhs(caches, sess, pairs, start, finish)
    _set_status(hhs, read_list, forecast_date)
    hist_map.update(hhs)
    return consumption_info + 'pairs - \n' + dumps(pairs)


def _make_reads(forwards, prev_reads, pres_reads):
    prev_read = next(prev_reads, None)
    pres_read = next(pres_reads, None)
    while prev_read is not None or pres_read is not None:

        if prev_read is None:
            yield pres_read
            pres_read = next(pres_reads, None)

        elif pres_read is None:
            yield prev_read
            prev_read = next(prev_reads, None)

        else:
            if (forwards and prev_read['date'] < pres_read['date']) or (
                    not forwards and prev_read['date'] >= pres_read['date']):
                yield prev_read
                prev_read = next(prev_reads, None)
            else:
                yield pres_read
                pres_read = next(pres_reads, None)
