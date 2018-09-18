from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, cast, Float
from sqlalchemy.sql.expression import null
import math
from werkzeug.exceptions import BadRequest
from collections import defaultdict
from chellow.models import (
    GEra, GRegisterRead, GBill, BillType, GReadType, GBatch,
    get_non_core_contract_id, GRateScript)
from chellow.utils import (
    HH, hh_max, get_file_rates, hh_min, hh_range, to_ct, utc_datetime_now,
    utc_datetime, PropDict, hh_format)
from chellow.computer import hh_rate
from types import MappingProxyType
from datetime import timedelta
from zish import loads, dumps
import chellow.bank_holidays
from math import floor


def get_times(sess, caches, start_date, finish_date, forecast_date):
    times_cache = get_g_engine_cache(caches, 'times')
    try:
        s_cache = times_cache[start_date]
    except KeyError:
        s_cache = times_cache[start_date] = {}

    try:
        f_cache = s_cache[finish_date]
    except KeyError:
        f_cache = s_cache[finish_date] = {}

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


def get_g_engine_cache(caches, name):
    try:
        return caches['g_engine'][name]
    except KeyError:
        caches['g_engine'] = defaultdict(dict)
        return caches['g_engine'][name]


def g_contract_func(caches, contract, func_name):
    try:
        ns = caches['g_engine']['funcs'][contract.id]
    except KeyError:
        try:
            contr_func_cache = caches['g_engine']['funcs']
        except KeyError:
            contr_func_cache = get_g_engine_cache(caches, 'funcs')

        try:
            ns = contr_func_cache[contract.id]
        except KeyError:
            ns = {
                'db_id': contract.id, 'properties': contract.make_properties()}
            exec(contract.charge_script, ns)
            contr_func_cache[contract.id] = ns

    return ns.get(func_name, None)


def forecast_date():
    now = utc_datetime_now()
    return utc_datetime(now.year, now.month, 1)


def get_data_sources(ds, start_date, finish_date, forecast_date=None):

    if forecast_date is None:
        forecast_date = ds.forecast_date

    if ds.start_date == start_date and ds.finish_date == finish_date and \
            forecast_date == ds.forecast_date:
        yield ds
    else:
        for g_era in ds.sess.query(GEra).filter(
                GEra.g_supply == ds.g_supply,
                GEra.start_date <= finish_date, or_(
                    GEra.finish_date == null(),
                    GEra.finish_date >= start_date)):
            chunk_start = hh_max(g_era.start_date, start_date)
            chunk_finish = hh_min(g_era.finish_date, finish_date)

            ds = GDataSource(
                ds.sess, chunk_start, chunk_finish, forecast_date, g_era,
                ds.caches, ds.g_bill)
            yield ds


def datum_range(sess, caches, years_back, start_date, finish_date):
    try:
        return caches['g_engine']['datum'][years_back][start_date][finish_date]
    except KeyError:
        try:
            g_engine_cache = caches['g_engine']
        except KeyError:
            g_engine_cache = caches['g_engine'] = {}

        try:
            d_cache_datum = g_engine_cache['datum']
        except KeyError:
            d_cache_datum = g_engine_cache['datum'] = {}

        try:
            d_cache_years = d_cache_datum[years_back]
        except KeyError:
            d_cache_years = d_cache_datum[years_back] = {}

        try:
            d_cache = d_cache_years[start_date]
        except KeyError:
            d_cache = d_cache_years[start_date] = {}

        datum_list = []
        for dt in hh_range(caches, start_date, finish_date):
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

            datum_list.append(
                MappingProxyType(
                    {
                        'hist_start': hist_date, 'start_date': dt,
                        'ct_day': ct_dt.day, 'utc_month': dt.month,
                        'utc_day': dt.day,
                        'utc_decimal_hour': utc_decimal_hour,
                        'utc_year': dt.year, 'utc_hour': dt.hour,
                        'utc_minute': dt.minute, 'ct_year': ct_dt.year,
                        'ct_month': ct_dt.month,
                        'ct_decimal_hour': ct_decimal_hour,
                        'ct_day_of_week': ct_dt.weekday(),
                        'utc_day_of_week': dt.weekday(),
                        'utc_is_bank_holiday': utc_is_bank_holiday,
                        'ct_is_bank_holiday': ct_is_bank_holiday,
                        'utc_is_month_end': utc_is_month_end,
                        'ct_is_month_end': ct_is_month_end,
                        'status': 'X', 'kwh': 0, 'hist_kwh': 0,
                        'unit_code': 'M3', 'unit_factor': 1,
                        'units_consumed': 0,
                        'correction_factor': CORRECTION_FACTOR,
                        'calorific_value': 0,
                        'avg_cv': 0}))
        datum_tuple = tuple(datum_list)
        d_cache[finish_date] = datum_tuple
        return datum_tuple


ACTUAL_READ_TYPES = ['A', 'C', 'S']
CORRECTION_FACTOR = 1.02264


def g_rates(sess, caches, g_contract_id, date):
    try:
        return caches['g_engine']['rates'][g_contract_id][date]
    except KeyError:
        try:
            ccache = caches['g_engine']
        except KeyError:
            ccache = caches['g_engine'] = {}

        try:
            rss_cache = ccache['rates']
        except KeyError:
            rss_cache = ccache['rates'] = {}

        try:
            cont_cache = rss_cache[g_contract_id]
        except KeyError:
            cont_cache = rss_cache[g_contract_id] = {}

        try:
            return cont_cache[date]
        except KeyError:
            month_after = date + relativedelta(months=1) + relativedelta(
                days=1)
            month_before = date - relativedelta(months=1) - relativedelta(
                days=1)

            rs = sess.query(GRateScript).filter(
                GRateScript.g_contract_id == g_contract_id,
                GRateScript.start_date <= date, or_(
                    GRateScript.finish_date == null(),
                    GRateScript.finish_date >= date)).first()

            if rs is None:
                rs = sess.query(GRateScript).filter(
                    GRateScript.g_contract_id == g_contract_id).order_by(
                    GRateScript.start_date.desc()).first()
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
                "the local rate script for contract " + str(g_contract_id) +
                " at " + hh_format(cstart) + ".", loads(rs.script), [])
            for dt in hh_range(caches, cstart, cfinish):
                if dt not in cont_cache:
                    cont_cache[dt] = vals

            return vals


class GDataSource():
    def __init__(
            self, sess, start_date, finish_date, forecast_date, g_era,
            caches, g_bill):
        self.sess = sess
        self.caches = caches
        self.forecast_date = forecast_date
        self.start_date = start_date
        self.finish_date = finish_date
        times = get_times(sess, caches, start_date, finish_date, forecast_date)
        self.years_back = times['years-back']
        self.history_start = times['history-start']
        self.history_finish = times['history-finish']

        self.problem = ''
        self.bill = defaultdict(int, {'problem': ''})
        self.hh_data = []
        self.rate_sets = defaultdict(set)

        self.g_bill = g_bill
        if self.g_bill is not None:
            self.g_bill_start = g_bill.start_date
            self.g_bill_finish = g_bill.finish_date
            self.is_last_g_bill_gen = \
                not self.g_bill_finish < self.start_date and not \
                self.g_bill_finish > self.finish_date

        self.g_era = g_era
        self.g_supply = g_era.g_supply
        self.mprn = self.g_supply.mprn
        self.g_exit_zone_code = self.g_supply.g_exit_zone.code
        self.g_ldz_code = self.g_supply.g_exit_zone.g_ldz.code
        self.g_dn_code = self.g_supply.g_exit_zone.g_ldz.g_dn.code
        self.account = g_era.account
        self.g_contract = g_era.g_contract

        self.consumption_info = ''

        if self.years_back == 0:
            hist_g_eras = [self.g_era]
        else:
            hist_g_eras = sess.query(GEra).filter(
                GEra.g_supply == self.g_supply,
                GEra.start_date <= self.history_finish, or_(
                    GEra.finish_date == null(),
                    GEra.finish_date >= self.history_start)).order_by(
                GEra.start_date).all()
            if len(hist_g_eras) == 0:
                hist_g_eras = sess.query(GEra).filter(
                    GEra.g_supply == self.g_supply).order_by(
                    GEra.start_date).limit(1).all()

        g_cv_id = get_non_core_contract_id('g_cv')
        hist_map = {}

        for i, hist_g_era in enumerate(hist_g_eras):
            if self.history_start > hist_g_era.start_date:
                chunk_start = self.history_start
            else:
                if i == 0:
                    chunk_start = self.history_start
                else:
                    chunk_start = hist_g_era.start_date

            chunk_finish = hh_min(hist_g_era.finish_date, self.history_finish)
            if self.g_bill is None:
                read_list = []
                read_keys = set()
                pairs = []

                prior_pres_g_reads = iter(
                    sess.query(GRegisterRead).join(GBill).join(BillType)
                    .join(GRegisterRead.pres_type).filter(
                        GReadType.code.in_(ACTUAL_READ_TYPES),
                        GBill.g_supply == self.g_supply,
                        GRegisterRead.pres_date < chunk_start,
                        BillType.code != 'W').order_by(
                        GRegisterRead.pres_date.desc()))
                prior_prev_g_reads = iter(
                    sess.query(GRegisterRead).join(GBill).join(BillType)
                    .join(GRegisterRead.prev_type).filter(
                        GReadType.code.in_(ACTUAL_READ_TYPES),
                        GBill.g_supply == self.g_supply,
                        GRegisterRead.prev_date < chunk_start,
                        BillType.code != 'W').order_by(
                        GRegisterRead.prev_date.desc()))
                next_pres_g_reads = iter(
                    sess.query(GRegisterRead).join(GBill).join(BillType)
                    .join(GRegisterRead.pres_type).filter(
                        GReadType.code.in_(ACTUAL_READ_TYPES),
                        GBill.g_supply == self.g_supply,
                        GRegisterRead.pres_date >= chunk_start,
                        BillType.code != 'W').order_by(
                        GRegisterRead.pres_date))
                next_prev_g_reads = iter(
                    sess.query(GRegisterRead).join(GBill).join(BillType)
                    .join(GRegisterRead.prev_type).filter(
                        GReadType.code.in_(ACTUAL_READ_TYPES),
                        GBill.g_supply == self.g_supply,
                        GRegisterRead.prev_date >= chunk_start,
                        BillType.code != 'W').order_by(
                        GRegisterRead.prev_date))

                for is_forwards in (False, True):
                    if is_forwards:
                        pres_g_reads = next_pres_g_reads
                        prev_g_reads = next_prev_g_reads
                        read_list.reverse()
                    else:
                        pres_g_reads = prior_pres_g_reads
                        prev_g_reads = prior_prev_g_reads

                    prime_pres_g_read = None
                    prime_prev_g_read = None
                    while True:
                        while prime_pres_g_read is None:
                            try:
                                pres_g_read = next(pres_g_reads)
                            except StopIteration:
                                break

                            pres_date = pres_g_read.pres_date
                            pres_msn = pres_g_read.msn
                            read_key = '_'.join([str(pres_date), pres_msn])
                            if read_key in read_keys:
                                continue

                            pres_g_bill = sess.query(GBill).join(
                                BillType).filter(
                                GBill.g_supply == self.g_supply,
                                GBill.finish_date >=
                                pres_g_read.g_bill.start_date,
                                GBill.start_date <=
                                pres_g_read.g_bill.finish_date,
                                BillType.code != 'W').order_by(
                                GBill.issue_date.desc(),
                                BillType.code).first()

                            if pres_g_bill != pres_g_read.g_bill:
                                continue

                            value = sess.query(
                                cast(GRegisterRead.pres_value, Float)).filter(
                                GRegisterRead.g_bill == pres_g_bill,
                                GRegisterRead.pres_date == pres_date,
                                GRegisterRead.msn == pres_msn).scalar()

                            prime_pres_g_read = {
                                'date': pres_date, 'value': value,
                                'msn': pres_msn}
                            read_keys.add(read_key)

                        while prime_prev_g_read is None:

                            try:
                                prev_g_read = next(prev_g_reads)
                            except StopIteration:
                                break

                            prev_date = prev_g_read.prev_date
                            prev_msn = prev_g_read.msn
                            read_key = '_'.join([str(prev_date), prev_msn])
                            if read_key in read_keys:
                                continue

                            prev_g_bill = sess.query(GBill).join(
                                BillType).filter(
                                GBill.g_supply == self.g_supply,
                                GBill.finish_date >=
                                prev_g_read.g_bill.start_date,
                                GBill.start_date <=
                                prev_g_read.g_bill.finish_date,
                                BillType.code != 'W').order_by(
                                GBill.issue_date.desc(),
                                BillType.code).first()
                            if prev_g_bill != prev_g_read.g_bill:
                                continue

                            value = sess.query(
                                cast(GRegisterRead.prev_value, Float)).filter(
                                GRegisterRead.g_bill == prev_g_bill,
                                GRegisterRead.prev_date == prev_date,
                                GRegisterRead.msn == prev_msn).scalar()

                            prime_prev_g_read = {
                                'date': prev_date, 'value': value,
                                'msn': prev_msn}
                            read_keys.add(read_key)

                        if prime_pres_g_read is None and \
                                prime_prev_g_read is None:
                            break
                        elif prime_pres_g_read is None:
                            read_list.append(prime_prev_g_read)
                            prime_prev_g_read = None
                        elif prime_prev_g_read is None:
                            read_list.append(prime_pres_g_read)
                            prime_pres_g_read = None
                        else:
                            if is_forwards:
                                if prime_prev_g_read['date'] == \
                                        prime_pres_g_read['date'] or \
                                        prime_pres_g_read['date'] < \
                                        prime_prev_g_read['date']:
                                    read_list.append(prime_pres_g_read)
                                    prime_pres_g_read = None
                                else:
                                    read_list.append(prime_prev_g_read)
                                    prime_prev_g_read = None
                            else:
                                if prime_prev_g_read['date'] == \
                                        prime_pres_g_read['date'] or \
                                        prime_prev_g_read['date'] > \
                                        prime_pres_g_read['date']:
                                    read_list.append(prime_prev_g_read)
                                    prime_prev_g_read = None
                                else:
                                    read_list.append(prime_pres_g_read)
                                    prime_pres_g_read = None

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
                                    ).total_seconds() / (30 * 60) + 1

                                units = fore_read['value'] - aft_read['value']

                                if units < 0:
                                    digits = int(
                                        math.log10(aft_read['value'])) + 1
                                    units = 10 ** digits + units

                                pairs.append(
                                    {
                                        'start-date': aft_read['date'],
                                        'finish-date': fore_read['date'] + HH,
                                        'units': units / num_hh})

                                if len(pairs) > 0 and (
                                        not is_forwards or (
                                            is_forwards and
                                            read_list[-1]['date'] >
                                            chunk_finish)):
                                        break

                self.consumption_info += 'read list - \n' + dumps(read_list) \
                    + "\n"
                if len(pairs) == 0:
                    pairs.append(
                        {
                            'start-date': chunk_start,
                            'finish-date': chunk_finish, 'units': 0})

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

                self.consumption_info += 'pairs - \n' + dumps(pairs)

                cf = 1 if hist_g_era.is_corrected else CORRECTION_FACTOR
                g_unit = hist_g_era.g_unit
                unit_code, unit_factor = g_unit.code, float(g_unit.factor)
                for pair in pairs:
                    units = pair['units']
                    for hh_date in hh_range(
                            caches, pair['start-date'], pair['finish-date']):
                        cv, avg_cv = find_cv(
                            sess, caches, g_cv_id, hh_date, self.g_ldz_code)

                        hist_map[hh_date] = {
                            'unit_code': unit_code,
                            'unit_factor': unit_factor,
                            'units_consumed': units,
                            'correction_factor': cf,
                            'calorific_value': cv,
                            'avg_cv': avg_cv}

            else:
                g_bills = []
                for cand_bill in sess.query(GBill).join(GBatch) \
                        .join(BillType).filter(
                            GBill.g_supply == self.g_supply,
                            GBill.g_reads.any(),
                            GBatch.g_contract == self.g_contract,
                            GBill.start_date <= chunk_finish,
                            GBill.finish_date >= chunk_start,
                            BillType.code != 'W').order_by(
                            GBill.issue_date.desc(), GBill.start_date):
                    can_insert = True
                    for g_bill in g_bills:
                        if not cand_bill.start_date > g_bill.finish_date \
                                and not cand_bill.finish_date < \
                                g_bill.start_date:
                            can_insert = False
                            break
                    if can_insert:
                        g_bills.append(cand_bill)

                for g_bill in g_bills:
                    units_consumed = 0
                    for prev_value, pres_value in sess.query(
                            cast(GRegisterRead.prev_value, Float),
                            cast(GRegisterRead.pres_value, Float)).filter(
                            GRegisterRead.g_bill == g_bill):
                        units_diff = pres_value - prev_value
                        if units_diff < 0:
                            total_units = 10 ** len(str(int(prev_value)))
                            c_units = total_units - prev_value + pres_value
                            if c_units < abs(units_diff):
                                units_diff = c_units

                        units_consumed += units_diff

                    bill_s = (
                        g_bill.finish_date - g_bill.start_date +
                        timedelta(minutes=30)).total_seconds()
                    hh_units_consumed = units_consumed / (bill_s / (60 * 30))

                    cf = 1 if hist_g_era.is_corrected else CORRECTION_FACTOR
                    g_unit = hist_g_era.g_unit
                    unit_code, unit_factor = g_unit.code, float(g_unit.factor)
                    for hh_date in hh_range(
                            caches, g_bill.start_date, g_bill.finish_date):
                        cv, avg_cv = find_cv(
                            sess, caches, g_cv_id, hh_date, self.g_ldz_code)
                        hist_map[hh_date] = {
                            'unit_code': unit_code,
                            'unit_factor': unit_factor,
                            'units_consumed': hh_units_consumed,
                            'correction_factor': cf,
                            'calorific_value': cv,
                            'avg_cv': avg_cv}

        for d in datum_range(
                sess, self.caches, self.years_back, start_date, finish_date):
            h = d.copy()
            hist_start = h['hist_start']
            h.update(hist_map.get(hist_start, {}))
            h['kwh'] = h['units_consumed'] * h['unit_factor'] * \
                h['correction_factor'] * h['calorific_value'] / 3.6
            h['kwh_avg'] = h['units_consumed'] * h['unit_factor'] * \
                h['correction_factor'] * h['avg_cv'] / 3.6
            h['ug_rate'] = float(
                get_file_rates(
                    self.caches, 'g_ug',
                    h['start_date'])['ug_gbp_per_kwh'][self.g_exit_zone_code])
            self.hh_data.append(h)


def find_cv(sess, caches, g_cv_id, dt, g_ldz_code):
    cvs = chellow.computer.hh_rate(
        sess, caches, g_cv_id, dt)['cvs'][g_ldz_code]
    try:
        cv_props = cvs[dt.day]
    except KeyError:
        cv_props = sorted(cvs.items())[-1][1]

    cv = float(cv_props['cv'])

    try:
        avg_cv = caches['g_engine']['avg_cvs'][g_ldz_code][dt.year][dt.month]
    except KeyError:
        try:
            gec = caches['g_engine']
        except KeyError:
            gec = caches['g_engine'] = {}

        try:
            avg_cache = gec['avg_cvs']
        except KeyError:
            avg_cache = gec['avg_cvs'] = {}

        try:
            avg_cvs_cache = avg_cache[g_ldz_code]
        except KeyError:
            avg_cvs_cache = avg_cache[g_ldz_code] = {}

        try:
            year_cache = avg_cvs_cache[dt.year]
        except KeyError:
            year_cache = avg_cvs_cache[dt.year] = {}

        try:
            avg_cv = year_cache[dt.month]
        except KeyError:
            cv_list = [float(v['cv']) for v in cvs.values()]
            avg_cv = year_cache[dt.month] = floor(
                (sum(cv_list) / len(cv_list)) * 10) / 10
    return cv, avg_cv
