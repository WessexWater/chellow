from net.sf.chellow.monad import Monad
import collections
import datetime
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_, cast, Float
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import aliased
import math
import utils
import db
import simplejson as json
import bank_holidays
import computer

Monad.getUtils()['impt'](
    globals(), 'db', 'utils', 'templater', 'bank_holidays', 'computer')

HH, hh_after, totalseconds = utils.HH, utils.hh_after, utils.totalseconds
hh_before, hh_format = utils.hh_before, utils.hh_format

Contract, GEra, GRateScript = db.Contract, db.GEra, db.GRateScript
GRegisterRead = db.GRegisterRead
BillType, GBill, GReadType = db.BillType, db.GBill, db.GReadType
GBatch, GUnits = db.GBatch, db.GUnits

UserException = utils.UserException


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


def get_times(sess, caches, start_date, finish_date, forecast_date, pw):
    times_cache = get_g_engine_cache(caches, 'times')
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
            raise UserException('The start date is after the finish date.')
        times_dict = collections.defaultdict(int)
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
        caches['g_engine'] = collections.defaultdict(dict)
        return caches['g_engine'][name]


def g_contract_func(caches, contract, func_name, pw):
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


def identity_func(x):
    return x


def g_rate(sess, caches, g_contract_id, date, name, pw):
    try:
        rate_cache = caches['g_engine']['rates']
    except KeyError:
        rate_cache = get_g_engine_cache(caches, 'rates')

    try:
        cont_cache = rate_cache[g_contract_id]
    except KeyError:
        cont_cache = {}
        rate_cache[g_contract_id] = cont_cache

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
            future_func = future_funcs[g_contract_id]
        except KeyError:
            future_func = {'start_date': None, 'func': identity_func}
            future_funcs[g_contract_id] = future_func

        start_date = future_func['start_date']
        ffunc = future_func['func']

        if start_date is None:
            rs = sess.query(GRateScript).filter(
                GRateScript.g_contract_id == g_contract_id,
                GRateScript.start_date <= date,
                or_(
                    GRateScript.finish_date == null(),
                    GRateScript.finish_date >= date)).first()

            if rs is None:
                rs = sess.query(GRateScript).filter(
                    GRateScript.g_contract_id == g_contract_id). \
                    order_by(GRateScript.start_date.desc()).first()
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
                rs = sess.query(GRateScript).filter(
                    GRateScript.g_contract_id == g_contract_id,
                    GRateScript.start_date <= date,
                    or_(
                        GRateScript.finish_date == null(),
                        GRateScript.finish_date >= date)).first()

                if rs is None:
                    rs = sess.query(GRateScript).filter(
                        GRateScript.g_contract_id == g_contract_id). \
                        order_by(GRateScript.start_date.desc()).first()
                func = identity_func
                cstart = max(rs.start_date, month_before)
                cfinish = min(month_after, start_date - HH)
            else:
                rs = sess.query(GRateScript).filter(
                    GRateScript.g_contract_id == g_contract_id,
                    GRateScript.start_date <= start_date,
                    or_(
                        GRateScript.finish_date == null(),
                        GRateScript.finish_date >= start_date)).first()
                if rs is None:
                    rs = sess.query(GRateScript).filter(
                        GRateScript.g_contract_id == g_contract_id). \
                        order_by(GRateScript.start_date.desc()).first()
                func = ffunc
                cstart = max(start_date, month_before)
                cfinish = month_after

        ns = json.loads(rs.script)

        script_dict = {'ns': func(ns), 'rates': {}}
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
            raise UserException(
                "Can't find the rate " + name + " in the rate script at " +
                hh_format(date) + " of the contract " +
                str(g_contract_id) + ".")
        script_dict['rates'][name] = val
        return val


def forecast_date():
    now = datetime.datetime.now(pytz.utc)
    return datetime.datetime(now.year, now.month, 1, tzinfo=pytz.utc)


def get_data_sources(data_source, start_date, finish_date, forecast_date=None):

    if forecast_date is None:
        forecast_date = data_source.forecast_date

    if data_source.start_date == start_date and \
            data_source.finish_date == finish_date \
            and forecast_date == data_source.forecast_date:
        yield data_source
    else:
        for g_era in data_source.sess.query(GEra).filter(
                GEra.g_supply == data_source.g_supply,
                GEra.start_date <= finish_date,
                or_(
                    GEra.finish_date == null(),
                    GEra.finish_date >= start_date)):
            g_era_start = g_era.start_date

            if start_date < g_era_start:
                chunk_start = g_era_start
            else:
                chunk_start = start_date

            g_era_finish = g_era.finish_date

            chunk_finish = g_era_finish if \
                hh_after(finish_date, g_era_finish) else finish_date

            ds = DataSource(
                data_source.sess, chunk_start, chunk_finish, forecast_date,
                g_era, data_source.pw, data_source.caches, data_source.bill)
            yield ds


def _datum_generator(sess, years_back, caches, pw):
    try:
        datum_cache = caches['g_engine']['datum'][years_back]
    except KeyError:
        try:
            g_engine_cache = caches['g_engine']
        except KeyError:
            caches['g_engine'] = {}
            g_engine_cache = caches['g_engine']

        try:
            d_cache = g_engine_cache['datum']
        except KeyError:
            g_engine_cache['datum'] = {}
            d_cache = g_engine_cache['datum']

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

            utc_bank_holidays = computer.hh_rate(
                sess2, caches, bank_holidays.db_id, hh_date, 'bank_holidays',
                pw)
            if utc_bank_holidays is None:
                msg = "\nCan't find bank holidays for " + str(hh_date)
                pw.println(msg)
                raise UserException(msg)
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


ACTUAL_READ_TYPES = ['N', 'N3', 'C', 'X', 'CP']


class DataSource():
    def __init__(
            self, sess, start_date, finish_date, forecast_date, g_era, pw,
            caches, g_bill):
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
        self.bill = collections.defaultdict(int, {'problem': ''})
        self.hh_data = []
        self.rate_sets = collections.defaultdict(set)

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
        self.account = g_era.account
        self.g_contract = g_era.g_contract

        self.consumption_info = ''

        if self.years_back == 0:
            hist_g_eras = [self.g_era]
        else:
            hist_g_eras = sess.query(GEra).filter(
                GEra.g_supply == self.g_supply,
                GEra.start_date <= self.history_finish,
                or_(
                    GEra.finish_date == null(),
                    GEra.finish_date >= self.history_start)).order_by(
                GEra.start_date).all()
            if len(hist_g_eras) == 0:
                hist_g_eras = sess.query(GEra).filter(
                    GEra.g_supply == self.g_supply).order_by(
                    GEra.start_date).limit(1).all()

        dte = start_date

        for i, hist_g_era in enumerate(hist_g_eras):
            if self.history_start > hist_g_era.start_date:
                chunk_start = self.history_start
            else:
                if i == 0:
                    chunk_start = self.history_start
                else:
                    chunk_start = hist_g_era.start_date

            if hh_after(self.history_finish, hist_g_era.finish_date):
                chunk_finish = hist_g_era.finish_date
            else:
                chunk_finish = self.history_finish
            if self.g_bill is None:
                read_list = []
                read_keys = {}
                pairs = []

                prior_pres_g_reads = iter(
                    sess.query(GRegisterRead).join(GBill).join(BillType)
                    .join(GRegisterRead.pres_type).filter(
                        GReadType.code.in_(ACTUAL_READ_TYPES),
                        GBill.g_supply == self.g_supply,
                        GRegisterRead.present_date < chunk_start,
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

                for is_forwards in [False, True]:
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
                                pres_g_read = pres_g_reads.next()
                            except StopIteration:
                                break

                            pres_date = pres_g_read.present_date
                            pres_msn = pres_g_read.msn
                            read_key = '_'.join([str(pres_date), pres_msn])
                            if read_key in read_keys:
                                continue

                            pres_g_bill = sess.query(GBill) \
                                .join(GRegisterRead) \
                                .join(BillType).filter(
                                    GBill.g_supply == self.g_supply,
                                    GBill.finish_date >= pres_g_read.pres_date,
                                    GBill.start_date <= pres_g_read.pres_date,
                                    BillType.code != 'W').order_by(
                                    GBill.issue_date.desc(),
                                    BillType.code).first()

                            if pres_g_bill != pres_g_read.g_bill:
                                continue

                            reads = sess.query(GRegisterRead.pres_value). \
                                filter(
                                    GRegisterRead.g_bill == pres_g_bill,
                                    GRegisterRead.pres_date == pres_date,
                                    GRegisterRead.msn == pres_msn).all()

                            prime_pres_g_read = {
                                'date': pres_date, 'reads': reads,
                                'msn': pres_msn}
                            read_keys[read_key] = None

                        while prime_prev_g_read is None:

                            try:
                                prev_g_read = prev_g_reads.next()
                            except StopIteration:
                                break

                            prev_date = prev_g_read.prev_date
                            prev_msn = prev_g_read.msn
                            read_key = '_'.join([str(prev_date), prev_msn])
                            if read_key in read_keys:
                                continue

                            prev_g_bill = sess.query(GBill).join(BillType). \
                                filter(
                                GBill.g_supply == self.g_supply,
                                GBill.finish_date >=
                                prev_g_read.g_bill.start_date,
                                GBill.start_date <=
                                prev_g_read.g_bill.start_date,
                                BillType.code != 'W').order_by(
                                GBill.issue_date.desc(),
                                BillType.code).first()
                            if prev_g_bill != prev_g_read.g_bill:
                                continue

                            reads = sess.query(GRegisterRead.prev_val).filter(
                                GRegisterRead.g_bill == prev_g_bill,
                                GRegisterRead.prev_date == prev_date,
                                GRegisterRead.msn == prev_msn).all()

                            prime_prev_read = {
                                'date': prev_date, 'reads': reads,
                                'msn': prev_msn}
                            read_keys[read_key] = None

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
                                    read_list.append(prime_prev_read)
                                    prime_prev_read = None
                            else:
                                if prime_prev_read['date'] == \
                                        prime_pres_g_read['date'] or \
                                        prime_prev_g_read['date'] > \
                                        prime_pres_g_read['date']:
                                    read_list.append(prime_prev_read)
                                    prime_prev_read = None
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
                                num_hh = float(
                                    totalseconds(
                                        fore_read['date'] -
                                        aft_read['date'])) / (30 * 60)

                                tprs = {}
                                for tpr_code, initial_val in \
                                        aft_read['reads'].iteritems():
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

                self.consumption_info += 'read list - \n' + str(read_list) \
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

                self.consumption_info += 'pairs - \n' + str(pairs)

                for pair in pairs:
                    pair_hhs = totalseconds(
                        pair['finish-date'] + HH - pair['start-date']) / \
                        (60 * 30)
                    orig_dte = dte
                    for tpr_code, pair_kwh in pair['tprs'].iteritems():
                        hh_date = pair['start-date']
                        dte = orig_dte
                        datum_generator = _datum_generator(
                            sess, self.caches, self.years_back, self.pw)
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

                prev_type_alias = aliased(GReadType)
                pres_type_alias = aliased(GReadType)
                for g_bill in g_bills:
                    for prev_date, prev_value, prev_type, pres_date, \
                            pres_value, pres_type, correction_factor, \
                            g_units_code, g_units_factor, calorific_value \
                            in sess.query(
                            GRegisterRead.prev_date,
                            cast(GRegisterRead.prev_value, Float),
                            prev_type_alias.code,
                            GRegisterRead.pres_date,
                            cast(GRegisterRead.pres_value, Float),
                            pres_type_alias.code,
                            cast(GRegisterRead.correction_factor, Float),
                            GUnits.code,
                            cast(GUnits.factor, Float),
                            cast(GRegisterRead.calorific_value, Float)) \
                            .join(GUnits) \
                            .join(
                                prev_type_alias,
                                GRegisterRead.prev_type_id ==
                                prev_type_alias.id).join(
                            pres_type_alias,
                            GRegisterRead.pres_type_id ==
                            pres_type_alias.id).filter(
                            GRegisterRead.g_bill == g_bill,
                            GRegisterRead.prev_date <= chunk_finish,
                            GRegisterRead.pres_date >= chunk_start) \
                            .order_by(GRegisterRead.pres_date):

                        if prev_date < g_bill.start_date:
                            self.problem += "There's a read before the " \
                                "start of the bill!"
                        if pres_date > g_bill.finish_date:
                            self.problem += "There's a read after the end " \
                                "of the bill!"
                        units_consumed = pres_value - prev_value
                        if units_consumed < 0:
                            self.problem += "Clocked? "
                            digits = int(math.log10(prev_value)) + 1
                            units_consumed = 10 ** digits - prev_value + \
                                pres_value

                        hh_units_consumed = float(units_consumed) / \
                            float(
                                totalseconds(pres_date - prev_date) /
                                (60 * 30))
                        hh_kwh = hh_units_consumed * g_units_factor * \
                            correction_factor * calorific_value

                        ct_tz = pytz.timezone('Europe/London')

                        if pres_type in ACTUAL_READ_TYPES \
                                and prev_type in ACTUAL_READ_TYPES:
                            status = 'A'
                        else:
                            status = 'E'
                        if prev_date < chunk_start:
                            hh_date = chunk_start
                        else:
                            hh_date = prev_date

                        if pres_date > chunk_finish:
                            pass_finish = chunk_finish
                        else:
                            pass_finish = pres_date

                        year_delta = relativedelta(year=self.years_back)
                        while not hh_date > pass_finish:
                            dt_utc = hh_date + year_delta
                            next_dt_utc = dt_utc + HH
                            utc_is_month_end = all((
                                next_dt_utc.day == 1, next_dt_utc.hour == 0,
                                next_dt_utc.minute == 0))
                            dt_ct = ct_tz.normalize(dt_utc.astimezone(ct_tz))
                            next_dt_ct = dt_ct + HH
                            ct_is_month_end = all((
                                next_dt_ct.day == 1, next_dt_ct.hour == 0,
                                next_dt_ct.minute == 0))
                            self.hh_data.append(
                                {
                                    'hist_start_date': chunk_start,
                                    'start_date': dt_utc,
                                    'ct_day': dt_ct.day,
                                    'utc_month': dt_utc.month,
                                    'utc_day': dt_utc.day,
                                    'utc_decimal_hour': dt_utc.hour +
                                    float(dt_utc.minute) / 60,
                                    'utc_year': dt_utc.year,
                                    'utc_hour': dt_utc.hour,
                                    'utc_minute': dt_utc.minute,
                                    'ct_year': dt_ct.year,
                                    'ct_month': dt_ct.month,
                                    'ct_decimal-hour': dt_ct.hour +
                                    float(dt_ct.minute) / 60,
                                    'ct_day_of_week': dt_ct.weekday(),
                                    'utc_day_of_week':
                                    dt_utc.weekday(),
                                    'utc_is_month_end':
                                    utc_is_month_end,
                                    'ct_is_month_end':
                                    ct_is_month_end,
                                    'status': status,
                                    'units_code': g_units_code,
                                    'units_factor': g_units_factor,
                                    'calorific_value': calorific_value,
                                    'correction_factor': correction_factor,
                                    'units_consumed': hh_units_consumed,
                                    'kwh': hh_kwh})
                            hh_date += HH

    def g_contract_func(self, g_contract, func_name):
        return g_contract_func(self.caches, g_contract, func_name, self.pw)

    def g_rate(self, g_contract_id, date, name):
        try:
            return self.rate_cache[g_contract_id][date][name]
        except KeyError:
            return g_rate(
                self.sess, self.caches, g_contract_id, date, name, self.pw)
        except AttributeError:
            val = g_rate(
                self.sess, self.caches, g_contract_id, date, name, self.pw)
            self.rate_cache = self.caches['g_engine']['rates']
            return val

    def rate(self, contract_id, date, name):
        return computer.hh_rate(
            self.sess, self.caches, contract_id, date, name, self.pw)
