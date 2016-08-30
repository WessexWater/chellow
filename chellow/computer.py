from collections import defaultdict
from datetime import datetime as Datetime
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, cast, Float
from sqlalchemy.sql.expression import null, false
from sqlalchemy.orm import joinedload, aliased
import math
import json
from werkzeug.exceptions import BadRequest
from chellow.models import (
    RateScript, Channel, Era, Pc, Tpr, MeasurementRequirement, RegisterRead,
    Bill, BillType, ReadType)
from chellow.utils import HH, hh_format, hh_after
import chellow.bank_holidays
from itertools import combinations


class imdict(dict):
    def __hash__(self):
        return id(self)

    def _immutable(self, *args, **kws):
        raise TypeError('object is immutable')

    __setitem__ = _immutable
    __delitem__ = _immutable
    clear = _immutable
    update = _immutable
    setdefault = _immutable
    pop = _immutable
    popitem = _immutable

cons_types = ['construction', 'commissioning', 'operation']
lec_cats = [
    'import-net', 'export-net', 'import-gen', 'export-gen', 'import-3rd-party',
    'export-3rd-party']


def get_times(sess, caches, start_date, finish_date, forecast_date, pw):
    times_cache = get_computer_cache(caches, 'times')
    try:
        s_cache = times_cache[start_date]
    except KeyError:
        s_cache = {}
        times_cache[start_date] = s_cache

    try:
        f_cache = s_cache[finish_date]
    except KeyError:
        f_cache = {}
        s_cache[finish_date] = f_cache

    try:
        return f_cache[forecast_date]
    except KeyError:
        if start_date > finish_date:
            raise BadRequest('The start date is after the finish date.')
        times_dict = defaultdict(int)
        dt = finish_date
        years_back = 0
        while dt > forecast_date:
            dt -= relativedelta(years=1)
            years_back += 1

        times_dict['history-finish'] = dt
        times_dict['history-start'] = dt - (finish_date - start_date)

        times_dict['years-back'] = years_back

        f_cache[forecast_date] = times_dict
        return times_dict


def get_computer_cache(caches, name):
    try:
        return caches['computer'][name]
    except KeyError:
        caches['computer'] = defaultdict(dict)
        return caches['computer'][name]


def contract_func(caches, contract, func_name, pw):
    try:
        ns = caches['computer']['funcs'][contract.id]
    except KeyError:
        try:
            contr_func_cache = caches['computer']['funcs']
        except KeyError:
            contr_func_cache = get_computer_cache(caches, 'funcs')

        try:
            ns = contr_func_cache[contract.id]
        except KeyError:
            ns = {
                'db_id': contract.id, 'properties': contract.make_properties()}
            exec(contract.charge_script, ns)
            contr_func_cache[contract.id] = ns

    return ns.get(func_name, None)


def identity_func(x):
    return x


def hh_rate(sess, caches, contract_id, date, name, pw):
    try:
        rate_cache = caches['computer']['rates']
    except KeyError:
        rate_cache = get_computer_cache(caches, 'rates')

    try:
        cont_cache = rate_cache[contract_id]
    except KeyError:
        cont_cache = {}
        rate_cache[contract_id] = cont_cache

    try:
        d_cache = cont_cache[date]
    except KeyError:
        month_after = date + relativedelta(months=1) + relativedelta(days=1)
        month_before = date - relativedelta(months=1) - relativedelta(days=1)

        try:
            future_funcs = caches['future_funcs']
        except KeyError:
            future_funcs = {}
            caches['future_funcs'] = future_funcs

        try:
            future_func = future_funcs[contract_id]
        except KeyError:
            future_func = {'start_date': None, 'func': identity_func}
            future_funcs[contract_id] = future_func

        start_date = future_func['start_date']
        ffunc = future_func['func']

        if start_date is None:
            rs = sess.query(RateScript).filter(
                RateScript.contract_id == contract_id,
                RateScript.start_date <= date,
                or_(
                    RateScript.finish_date == null(),
                    RateScript.finish_date >= date)).first()

            if rs is None:
                rs = sess.query(RateScript).filter(
                    RateScript.contract_id == contract_id). \
                    order_by(RateScript.start_date.desc()).first()
                func = ffunc
                if date < rs.start_date:
                    cstart = month_before
                    cfinish = min(month_after, rs.start_date - HH)
                else:
                    cstart = max(rs.finish_date + HH, month_before)
                    cfinish = month_after
            else:
                func = identity_func
                cstart = max(rs.start_date, month_before)
                if rs.finish_date is None:
                    cfinish = month_after
                else:
                    cfinish = min(rs.finish_date, month_after)
        else:
            if date < start_date:
                rs = sess.query(RateScript).filter(
                    RateScript.contract_id == contract_id,
                    RateScript.start_date <= date,
                    or_(
                        RateScript.finish_date == null(),
                        RateScript.finish_date >= date)).first()

                if rs is None:
                    rs = sess.query(RateScript).filter(
                        RateScript.contract_id == contract_id). \
                        order_by(RateScript.start_date.desc()).first()
                func = identity_func
                cstart = max(rs.start_date, month_before)
                cfinish = min(month_after, start_date - HH)
            else:
                rs = sess.query(RateScript).filter(
                    RateScript.contract_id == contract_id,
                    RateScript.start_date <= start_date,
                    or_(
                        RateScript.finish_date == null(),
                        RateScript.finish_date >= start_date)).first()
                if rs is None:
                    rs = sess.query(RateScript).filter(
                        RateScript.contract_id == contract_id). \
                        order_by(RateScript.start_date.desc()).first()
                func = ffunc
                cstart = max(start_date, month_before)
                cfinish = month_after

        is_json = rs.script.lstrip()[0] == '{'
        if is_json:
            ns = json.loads(rs.script)
        else:
            ns = {}
            exec(rs.script, ns)

        script_dict = {'is_json': is_json, 'ns': func(ns), 'rates': {}}
        script_dict['rates']['_script_dict'] = script_dict

        d_cache = script_dict['rates']

        dt = cstart
        while dt <= cfinish:
            cont_cache[dt] = d_cache
            dt += HH

    try:
        return d_cache[name]
    except KeyError:
        script_dict = d_cache['_script_dict']

        try:
            val = script_dict['ns'][name]
        except KeyError:
            raise BadRequest(
                "Can't find the rate " + name + " in the rate script at " +
                hh_format(date) + " of the contract " + str(contract_id) + ".")
        if not script_dict['is_json']:
            val = val()
        script_dict['rates'][name] = val
        return val


def forecast_date():
    now = Datetime.now(pytz.utc)
    return Datetime(now.year, now.month, 1, tzinfo=pytz.utc)


def displaced_era(sess, site_group, start_date, finish_date):
    has_displaced = False
    eras = {}
    for supply in site_group.supplies:
        source_code = supply.source.code
        if source_code in ('gen', 'gen-net'):
            has_displaced = True
        if source_code in ('net', 'gen-net'):
            export_channels = sess.query(Channel).join(Era).filter(
                Era.supply == supply, Channel.imp_related == false(),
                Channel.channel_type == 'ACTIVE',
                Era.start_date <= finish_date,
                or_(
                    Era.finish_date == null(),
                    Era.finish_date >= start_date)).count()
            if export_channels is not None and export_channels > 0:
                has_displaced = True

            for era in sess.query(Era).join(Pc).filter(
                    Era.imp_mpan_core != null(),
                    Era.supply == supply, Era.start_date <= finish_date,
                    or_(
                        Era.finish_date == null(),
                        Era.finish_date >= start_date)):
                eras[
                    era.pc.code + hh_format(era.start_date) +
                    era.imp_mpan_core] = era

    if has_displaced and len(eras) > 0:
        return eras[sorted(eras.keys())[0]]
    else:
        return None


def get_data_sources(data_source, start_date, finish_date, forecast_date=None):
    if forecast_date is None:
        forecast_date = data_source.forecast_date

    if data_source.start_date == start_date and \
            data_source.finish_date == finish_date \
            and forecast_date == data_source.forecast_date:
        yield data_source
        return
    elif data_source.site is None:
        if data_source.is_import:
            eras = data_source.sess.query(Era).filter(
                Era.supply == data_source.supply,
                Era.imp_mpan_core != null(), Era.start_date <= finish_date,
                or_(
                    Era.finish_date == null(), Era.finish_date >= start_date))
        else:
            eras = data_source.sess.query(Era).filter(
                Era.supply == data_source.supply, Era.exp_mpan_core != null(),
                Era.start_date <= finish_date,
                or_(
                    Era.finish_date == null(), Era.finish_date >= start_date))

        for era in eras:
            era_start = era.start_date

            chunk_start = era_start if start_date < era_start else start_date

            era_finish = era.finish_date

            chunk_finish = era_finish if \
                hh_after(finish_date, era_finish) else finish_date

            ds = SupplySource(
                data_source.sess, chunk_start, chunk_finish, forecast_date,
                era, data_source.is_import, data_source.pw, data_source.caches,
                data_source.bill)
            yield ds

    else:
        for group in data_source.site.groups(
                data_source.sess, start_date, finish_date, True):

            chunk_start = group.start_date if \
                group.start_date > start_date else start_date

            chunk_finish = finish_date if \
                group.finish_date > finish_date else group.finish_date

            if data_source.stream_focus == 'gen-used':
                eras = {}
                for supply in group.supplies:
                    for era in data_source.sess.query(Era).join(Pc).filter(
                            Era.imp_mpan_core != null(), Pc.code == '00',
                            Era.supply == supply,
                            Era.start_date <= finish_date,
                            or_(
                                Era.finish_date == null(),
                                Era.finish_date >= start_date)).order_by(
                            Era.start_date):
                        eras[era.imp_mpan_core] = era
                era = eras[sorted(eras.keys())[0]]
            else:
                era = data_source.era
            site_ds = SiteSource(
                data_source.sess, data_source.site, chunk_start, chunk_finish,
                forecast_date, data_source.pw, data_source.caches, era)
            if data_source.stream_focus == '3rd-party-used':
                site_ds.revolve_to_3rd_party_used()
            yield site_ds


def _tpr_dict(sess, caches, tpr_code, pw):
    try:
        return caches['computer']['tprs'][tpr_code]
    except KeyError:
        tpr_cache = get_computer_cache(caches, 'tprs')

        tpr_dict = {}
        days_of_week = dict([i, []] for i in range(7))
        tpr_dict['days-of-week'] = days_of_week
        tpr = Tpr.get_by_code(sess, tpr_code)
        for ci in sess.execute(
                "select ci.day_of_week - 1 as day_of_week, "
                "ci.start_month * 100 + ci.start_day as start_month, "
                "ci.start_hour + (ci.start_minute / 60.0) as start_hour, "
                "ci.end_month * 100 + ci.end_day as end_month, "
                "ci.end_hour + (ci.end_minute / 60.0) as end_hour "
                "from clock_interval ci where ci.tpr_id = :tpr_id",
                params={'tpr_id': tpr.id}):
            days_of_week[ci.day_of_week].append(
                {
                    'start-month': ci.start_month,
                    'start-hour': float(ci.start_hour),
                    'end-month': ci.end_month,
                    'end-hour': float(ci.end_hour)})

        tpr_dict['is-gmt'] = tpr.is_gmt

        tpr_dict['datum-cache'] = {}
        tpr_cache[tpr_code] = tpr_dict
        return tpr_dict


def _tpr_datum_generator(sess, caches, tpr_code, years_back, pw):
    tpr_dict = _tpr_dict(sess, caches, tpr_code, pw)
    datum_cache = tpr_dict['datum-cache']
    dgenerator = _datum_generator(sess, years_back, caches, pw)

    def _generator(sess2, hh_date):
        try:
            return datum_cache[hh_date]
        except KeyError:
            days_of_week = tpr_dict['days-of-week']
            datum = dgenerator(sess2, hh_date)
            pref = 'utc-' if tpr_dict['is-gmt'] else 'ct-'

            decimal_hour = datum[pref + 'decimal-hour']
            fractional_month = datum[pref + 'month'] * 100 + \
                datum[pref + 'day']

            result = None

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
                    result = datum
                    break
            datum_cache[hh_date] = result
            return result
    return _generator


def _datum_generator(sess, years_back, caches, pw):
    try:
        datum_cache = caches['computer']['datum'][years_back]
    except KeyError:
        try:
            computer_cache = caches['computer']
        except KeyError:
            caches['computer'] = {}
            computer_cache = caches['computer']

        try:
            d_cache = computer_cache['datum']
        except KeyError:
            computer_cache['datum'] = {}
            d_cache = computer_cache['datum']

        try:
            datum_cache = d_cache[years_back]
        except KeyError:
            d_cache[years_back] = {}
            datum_cache = d_cache[years_back]

    def _generator(sess2, hh_date):
        try:
            return datum_cache[hh_date]
        except KeyError:
            ct_tz = pytz.timezone('Europe/London')
            ct_dt = ct_tz.normalize(hh_date.astimezone(ct_tz))

            utc_is_month_end = (hh_date + HH).day == 1 and hh_date.day != 1
            ct_is_month_end = (ct_dt + HH).day == 1 and ct_dt.day != 1

            utc_decimal_hour = hh_date.hour + float(hh_date.minute) / 60
            ct_decimal_hour = ct_dt.hour + float(ct_dt.minute) / 60

            utc_bank_holidays = hh_rate(
                sess2, caches, chellow.bank_holidays.get_db_id(), hh_date,
                'bank_holidays', pw)
            if utc_bank_holidays is None:
                raise BadRequest(
                    "Can't find bank holidays for " + str(hh_date))
            utc_bank_holidays = utc_bank_holidays[:]
            for i in range(len(utc_bank_holidays)):
                utc_bank_holidays[i] = utc_bank_holidays[i][5:]
            utc_is_bank_holiday = hh_date.strftime("%m-%d") in \
                utc_bank_holidays

            hh = {
                'status': 'E',
                'hist-start': hh_date - relativedelta(years=years_back),
                'start-date': hh_date, 'ct-day': ct_dt.day,
                'utc-month': hh_date.month, 'utc-day': hh_date.day,
                'utc-decimal-hour': utc_decimal_hour,
                'utc-year': hh_date.year, 'utc-hour': hh_date.hour,
                'utc-minute': hh_date.minute, 'ct-year': ct_dt.year,
                'ct-month': ct_dt.month, 'ct-decimal-hour': ct_decimal_hour,
                'ct-day-of-week': ct_dt.weekday(),
                'utc-day-of-week': hh_date.weekday(),
                'utc-is-bank-holiday': utc_is_bank_holiday,
                'utc-is-month-end': utc_is_month_end,
                'ct-is-month-end': ct_is_month_end}

            datum_cache[hh_date] = imdict(hh)
            return datum_cache[hh_date]
    return _generator


class DataSource():
    def __init__(
            self, sess, start_date, finish_date, forecast_date, pw, caches):
        self.sess = sess
        self.caches = caches
        self.forecast_date = forecast_date
        self.start_date = start_date
        self.finish_date = finish_date
        self.pw = pw
        times = get_times(
            sess, caches, start_date, finish_date, forecast_date, pw)
        self.years_back = times['years-back']
        self.history_start = times['history-start']
        self.history_finish = times['history-finish']

        self.problem = ''
        self.is_green = False
        self.supplier_bill = defaultdict(int, {'problem': ''})
        self.mop_bill = defaultdict(int, {'problem': ''})
        self.dc_bill = defaultdict(int, {'problem': ''})
        self.hh_data = []
        self.supplier_rate_sets = defaultdict(set)
        self.mop_rate_sets = defaultdict(set, {'problem': ''})
        self.dc_rate_sets = defaultdict(set, {'problem': ''})

    def contract_func(self, contract, func_name):
        return contract_func(self.caches, contract, func_name, self.pw)

    def hh_rate(self, contract_id, date, name):
        try:
            return self.rate_cache[contract_id][date][name]
        except KeyError:
            return hh_rate(
                self.sess, self.caches, contract_id, date, name, self.pw)
        except AttributeError:
            val = hh_rate(
                self.sess, self.caches, contract_id, date, name, self.pw)
            self.rate_cache = self.caches['computer']['rates']
            return val


class SiteSource(DataSource):
    def __init__(
            self, sess, site, start_date, finish_date, forecast_date, pw,
            caches, era=None):
        DataSource.__init__(
            self, sess, start_date, finish_date, forecast_date, pw, caches)
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
            self.dno_contract = self.supply.dno_contract
            self.dno_code = self.dno_contract.name
            llfc = era.imp_llfc
            self.llfc_code = llfc.code
            self.is_import = True
            self.voltage_level_code = llfc.voltage_level.code
            self.is_substation = llfc.is_substation
            self.sc = era.imp_sc
            self.pc_code = era.pc.code
            self.gsp_group_code = self.supply.gsp_group.code
            self.supplier_contract = era.imp_supplier_contract

        datum_generator = _datum_generator(
            sess, self.years_back, self.caches, self.pw)

        hh_date = start_date
        for group in site.groups(
                sess, self.history_start, self.history_finish, True):
            supplies = group.supplies
            if len(supplies) == 0:
                continue
            hist_date = group.start_date
            group_finish = group.finish_date
            rs = iter(
                sess.execute(
                    "select hh_datum.value, hh_datum.start_date, "
                    "hh_datum.status, channel.imp_related, source.code "
                    "from hh_datum, channel, era, supply, source "
                    "where hh_datum.channel_id = channel.id "
                    "and channel.era_id = era.id "
                    "and era.supply_id = supply.id "
                    "and supply.source_id = source.id "
                    "and channel.channel_type = 'ACTIVE' "
                    "and hh_datum.start_date >= :group_start "
                    "and hh_datum.start_date <= :group_finish "
                    "and supply.id = any(:supply_ids) "
                    "order by hh_datum.start_date",
                    params={
                        'group_start': group.start_date,
                        'group_finish': group.finish_date,
                        'supply_ids': [sup.id for sup in supplies]}))
            try:
                row = next(rs)
                hh_value = float(row[0])
                hh_start_date = row[1]
                imp_related = row[3]
                source_code = row[4]
            except StopIteration:
                hh_start_date = None

            while not hist_date > group_finish:
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
                    try:
                        row = next(rs)
                        hh_value = float(row[0])
                        hh_start_date = row[1]
                        imp_related = row[3]
                        source_code = row[4]
                    except StopIteration:
                        hh_start_date = None

                hh_values = datum_generator(sess, hh_date).copy()
                hh_values.update(
                    {
                        'status': 'E', 'hist-import-net-kwh': import_net_kwh,
                        'hist-import-net-kvarh': 0,
                        'hist-export-net-kwh': export_net_kwh,
                        'hist-export-net-kvarh': 0,
                        'hist-import-gen-kwh': import_gen_kwh,
                        'hist-export-gen-kwh': export_gen_kwh,
                        'anti-msp-kwh': 0, 'anti-msp-kw': 0,
                        'hist-import-3rd-party-kwh': import_3rd_party_kwh,
                        'hist-export-3rd-party-kwh': export_3rd_party_kwh})
                hh_values['hist-used-3rd-party-kwh'] = \
                    hh_values['hist-import-3rd-party-kwh'] - \
                    hh_values['hist-export-3rd-party-kwh']
                hh_values['used-3rd-party-kwh'] = \
                    hh_values['hist-used-3rd-party-kwh']
                hh_values['hist-kwh'] = hh_values['hist-used-gen-msp-kwh'] = \
                    hh_values['hist-import-gen-kwh'] - \
                    hh_values['hist-export-gen-kwh'] - \
                    hh_values['hist-export-net-kwh']

                hh_values['msp-kwh'] = hh_values['used-gen-msp-kwh'] \
                    = hh_values['hist-used-gen-msp-kwh']
                for lec_cat in lec_cats:
                    hh_values[lec_cat + '-kwh'] = \
                        hh_values['hist-' + lec_cat + '-kwh']

                hh_values['hist-used-kwh'] = \
                    hh_values['hist-used-gen-msp-kwh'] + \
                    hh_values['hist-import-net-kwh'] + \
                    hh_values['hist-used-3rd-party-kwh']
                hh_values['hist-imp-msp-kvarh'] = 0
                hh_values['imp-msp-kvarh'] = 0
                hh_values['exp-msp-kvarh'] = 0

                hh_values['used-kwh'] = hh_values['hist-used-kwh']
                hh_values['import-net-kwh'] = hh_values['hist-import-net-kwh']
                hh_values['msp-kw'] = hh_values['used-gen-msp-kw'] \
                    = hh_values['used-gen-msp-kwh'] * 2
                hh_values['imp-msp-kvar'] = hh_values['imp-msp-kvarh'] * 2
                hh_values['exp-msp-kvar'] = hh_values['exp-msp-kvarh'] * 2

                self.hh_data.append(hh_values)
                hh_date += HH
                hist_date += HH

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
            pw, caches, bill=None):
        DataSource.__init__(
            self, sess, start_date, finish_date, forecast_date, pw, caches)

        self.is_displaced = False
        self.bill = bill
        if self.bill is not None:
            self.bill_start = bill.start_date
            self.bill_finish = bill.finish_date
            self.is_last_bill_gen = \
                not self.bill_finish < self.start_date and not \
                self.bill_finish > self.finish_date

        self.site = None
        self.era = era
        self.is_import = is_import
        if is_import:
            self.mpan_core = era.imp_mpan_core
            self.llfc = era.imp_llfc
            self.sc = era.imp_sc
            self.supplier_account = era.imp_supplier_account
            self.supplier_contract = era.imp_supplier_contract
        else:
            self.mpan_core = era.exp_mpan_core
            self.llfc = era.exp_llfc
            self.sc = era.exp_sc
            self.supplier_account = era.exp_supplier_account
            self.supplier_contract = era.exp_supplier_contract

        self.id = self.mpan_core
        self.llfc_code = self.llfc.code
        self.voltage_level = self.llfc.voltage_level
        self.voltage_level_code = self.voltage_level.code
        self.is_substation = self.llfc.is_substation
        self.supply = era.supply
        self.dno_contract = self.supply.dno_contract
        self.dno_code = self.dno_contract.name
        self.is_new = False
        self.mtc = self.era.mtc
        self.meter_type = self.mtc.meter_type
        self.meter_type_code = self.meter_type.code
        self.ssc = self.era.ssc
        self.cop_code = self.era.cop.code

        self.ssc_code = None if self.ssc is None else self.ssc.code

        self.pc_code = self.era.pc.code
        self.gsp_group_code = self.supply.gsp_group.code

        self.measurement_type = era.make_meter_category()

        self.consumption_info = ''

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
            hist_eras = hist_eras.all()
            if len(hist_eras) == 0:
                hist_eras = sess.query(Era).filter(
                    Era.supply == self.supply).order_by(Era.start_date)
                if self.is_import:
                    hist_eras = hist_eras.filter(Era.imp_mpan_core != null())
                else:
                    hist_eras = hist_eras.filter(Era.exp_mpan_core != null())
                hist_eras = hist_eras.limit(1).all()

        dte = start_date

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

            if hh_after(self.history_finish, hist_era.finish_date):
                chunk_finish = hist_era.finish_date
            else:
                chunk_finish = self.history_finish

            hist_measurement_type = hist_era.make_meter_category()
            if hist_measurement_type == 'unmetered':

                kwh = hist_era.imp_sc * 60 * 30 / (
                    Datetime(chunk_start.year + 1, 1, 1) -
                    Datetime(chunk_start.year, 1, 1)).total_seconds()

                orig_start = dte
                for tpr in sess.query(Tpr).join(MeasurementRequirement).filter(
                        MeasurementRequirement.ssc == hist_era.ssc):
                    datum_generator = _tpr_datum_generator(
                        sess, self.caches, tpr.code, self.years_back,
                        self.pw)
                    hist_date = chunk_start
                    dte = orig_start
                    while not hist_date > chunk_finish:
                        datum = datum_generator(sess, dte)
                        if datum is not None:
                            new_datum = datum.copy()
                            new_datum.update(
                                {
                                    'msp-kw': kwh * 2, 'msp-kwh': kwh,
                                    'hist-kwh': kwh, 'imp-msp-kvarh': 0,
                                    'imp-msp-kvar': 0, 'exp-msp-kvarh': 0,
                                    'exp-msp-kvar': 0})
                            self.hh_data.append(new_datum)
                        hist_date += HH
                        dte += HH
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

                            if aft_read['msn'] == fore_read['msn']:
                                num_hh = (
                                    fore_read['date'] - aft_read['date']
                                    ).total_seconds() / (30 * 60)

                                tprs = {}
                                for tpr_code, initial_val in \
                                        aft_read['reads'].items():
                                    if tpr_code in fore_read['reads']:
                                        end_val = fore_read['reads'][tpr_code]
                                    else:
                                        continue

                                    kwh = end_val - initial_val

                                    if kwh < 0:
                                        digits = int(
                                            math.log10(initial_val)) + 1
                                        kwh = 10 ** digits + kwh

                                    tprs[tpr_code] = float(kwh) / num_hh

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
                    orig_dte = dte
                    for tpr_code, pair_kwh in pair['tprs'].items():
                        hh_date = pair['start-date']
                        dte = orig_dte
                        datum_generator = _tpr_datum_generator(
                            sess, self.caches, tpr_code, self.years_back,
                            self.pw)
                        hh_part = []

                        while not hh_date > pair['finish-date']:
                            datum = datum_generator(sess, dte)
                            if datum is not None:
                                hh_part.append(datum.copy())
                            hh_date += HH
                            dte += HH

                        kwh = pair_kwh * pair_hhs / len(hh_part) \
                            if len(hh_part) > 0 else 0

                        for datum in hh_part:
                            datum.update(
                                {
                                    'msp-kw': kwh * 2, 'msp-kwh': kwh,
                                    'hist-kwh': kwh, 'imp-msp-kvar': 0,
                                    'imp-msp-kvarh': 0, 'exp-msp-kvar': 0,
                                    'exp-msp-kvarh': 0})
                        self.hh_data += hh_part
            elif self.bill is not None and hist_measurement_type in (
                    'nhh', 'amr'):
                datum_generator = _datum_generator(
                    sess, self.years_back, self.caches, self.pw)
                hhd = {}
                hh_date = chunk_start
                while hh_date <= chunk_finish:
                    datum = datum_generator(sess, hh_date).copy()
                    datum.update(
                        {
                            'status': 'X', 'imp-msp-kvarh': 0,
                            'imp-msp-kvar': 0, 'exp-msp-kvarh': 0,
                            'exp-msp-kvar': 0, 'msp-kw': 0,
                            'msp-kwh': 0, 'hist-kwh': 0})
                    hhd[hh_date] = datum
                    hh_date += HH

                tpr_codes = sess.query(Tpr.code). \
                    join(MeasurementRequirement).filter(
                        MeasurementRequirement.ssc == self.ssc).all()

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
                            self.problem += "The TPR " + str(tpr_code) + \
                                " from the register read does not match any " \
                                "of the TPRs associated with the MPAN."

                        if previous_date < bill.start_date:
                            self.problem += "There's a read before the " \
                                "start of the bill!"
                        if present_date > bill.finish_date:
                            self.problem += "There's a read after the end " \
                                "of the bill!"
                        advance = present_value - previous_value
                        if advance < 0:
                            self.problem += "Clocked? "
                            digits = int(math.log10(previous_value)) + 1
                            advance = 10 ** digits - previous_value + \
                                present_value

                        kwh = advance * coefficient
                        self.consumption_info += "dumb nhh kwh for " + \
                            tpr_code + " is " + str(kwh) + "\n"

                        kws[tpr_code] += kwh

                    for tpr_code, kwh in kws.items():
                        tpr_dict = _tpr_dict(
                            sess, self.caches, tpr_code, self.pw)
                        days_of_week = tpr_dict['days-of-week']

                        ct_tz = pytz.timezone('Europe/London')

                        tz = pytz.utc if tpr_dict['is-gmt'] else ct_tz

                        if present_type in ACTUAL_READ_TYPES \
                                and previous_type in ACTUAL_READ_TYPES:
                            status = 'A'
                        else:
                            status = 'E'

                        year_delta = relativedelta(years=self.years_back)
                        hh_part = {}
                        hh_date = chunk_start

                        while not hh_date > chunk_finish:
                            dt = tz.normalize(
                                hh_date.astimezone(tz)) + year_delta
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
                            hh_date += HH

                        num_hh = len(hh_part)
                        if num_hh > 0:
                            rate = kwh / num_hh
                            for d, h in hh_part.items():
                                hhd_datum = hhd[d]
                                hhd_datum['msp-kw'] += rate * 2
                                hhd_datum['msp-kwh'] += rate
                                hhd_datum['hist-kwh'] += rate
                                if hhd_datum['status'] in ('X', 'A'):
                                    hhd_datum['status'] = h['status']
                self.hh_data.extend(v for k, v in sorted(hhd.items()))
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
                    datum_generator = _datum_generator(
                        sess, self.years_back, self.caches, self.pw)
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
                    try:
                        msp_kwh, anti_msp_kwh, status, imp_kvarh, \
                            exp_kvarh, hist_start = next(data)
                    except StopIteration:
                        hist_start = None

                    hh_date = chunk_start
                    while hh_date <= chunk_finish:
                        datum = datum_generator(sess, dte).copy()

                        if hh_date == hist_start:
                            if not (msp_kwh > 0 and anti_msp_kwh == 0):
                                imp_kvarh = 0
                                exp_kvarh = 0

                            datum.update(
                                {
                                    'status': status,
                                    'imp-msp-kvarh': imp_kvarh,
                                    'imp-msp-kvar': imp_kvarh * 2,
                                    'exp-msp-kvarh': exp_kvarh,
                                    'exp-msp-kvar': exp_kvarh * 2,
                                    'msp-kw': msp_kwh * 2, 'msp-kwh': msp_kwh,
                                    'hist-kwh': msp_kwh})
                            try:
                                msp_kwh, anti_msp_kwh, status, imp_kvarh, \
                                    exp_kvarh, hist_start = next(data)
                            except StopIteration:
                                hist_date = None
                        else:
                            datum.update(
                                {
                                    'status': 'X', 'imp-msp-kvarh': 0,
                                    'imp-msp-kvar': 0, 'exp-msp-kvarh': 0,
                                    'exp-msp-kvar': 0, 'msp-kw': 0,
                                    'msp-kwh': 0, 'hist-kwh': 0})

                        self.hh_data.append(datum)
                        hh_date += HH
                        dte += HH
                else:
                    # new style
                    datum_generator = _datum_generator(
                        sess, self.years_back, self.caches, self.pw)
                    hh_date = chunk_start

                    data = iter(sess.execute(
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
                            "    order by 1,3"}))
                    try:
                        hist_start, status, msp_kwh, imp_kvarh, exp_kvarh = \
                            next(data)
                    except StopIteration:
                        hist_start = None
                        msp_kwh = None

                    while hh_date <= chunk_finish:
                        datum = datum_generator(sess, dte).copy()
                        if hh_date == hist_start:
                            if msp_kwh is None:
                                datum['status'] = 'X'
                                datum['hist-kwh'] = datum['msp-kwh'] = 0
                                datum['msp-kw'] = 0
                            else:
                                datum['status'] = status
                                datum['hist-kwh'] = msp_kwh
                                datum['msp-kwh'] = msp_kwh
                                datum['msp-kw'] = msp_kwh * 2
                            datum['imp-msp-kvarh'] = imp_kvarh
                            datum['imp-msp-kvar'] = imp_kvarh * 2
                            datum['exp-msp-kvarh'] = exp_kvarh
                            datum['exp-msp-kvar'] = exp_kvarh * 2

                            try:
                                hist_start, status, msp_kwh, imp_kvarh, \
                                    exp_kvarh = next(data)
                            except StopIteration:
                                hist_start = None
                        else:
                            datum['status'] = 'X'
                            datum['imp-msp-kvarh'] = datum['imp-msp-kvar'] = 0
                            datum['exp-msp-kvarh'] = datum['exp-msp-kvar'] = 0
                            datum['msp-kw'] = datum['msp-kwh'] = 0
                            datum['hist-kwh'] = 0

                        self.hh_data.append(datum)
                        hh_date += HH
                        dte += HH
            else:
                raise BadRequest("gen type not recognized")
