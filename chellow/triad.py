from dateutil.relativedelta import relativedelta
from chellow.utils import (
    HH, hh_after, utc_datetime, get_file_scripts, hh_before, get_file_rates)
import chellow.computer
import chellow.duos


def triad_calc(
        hh, prefix, triad_data, financial_year_start, financial_year_finish,
        data_source, month_begin):
    gsp_kw = 0
    for i, triad_hh in enumerate(triad_data):
        triad_prefix = prefix + '-' + str(i + 1)
        hh[triad_prefix + '-date'] = triad_hh['hist-start']
        hh[triad_prefix + '-msp-kw'] = triad_hh['msp-kw']
        hh[triad_prefix + '-status'] = triad_hh['status']
        hh[triad_prefix + '-laf'] = triad_hh['laf']
        hh[triad_prefix + '-gsp-kw'] = triad_hh['gsp-kw']
        gsp_kw += triad_hh['gsp-kw']

    hh[prefix + '-gsp-kw'] = gsp_kw / 3

    if prefix == 'triad-actual':
        tot_rate = 0
        for start_date, finish_date, script in get_file_scripts('triad_rates'):
            if start_date <= financial_year_finish and not hh_before(
                    finish_date, financial_year_start):
                start_month = start_date.month
                if start_month < 4:
                    start_month += 12

                if finish_date is None:
                    finish_month = financial_year_finish.month
                else:
                    finish_month = finish_date.month

                if finish_month < 4:
                    finish_month += 12

                rt = get_file_rates(
                    data_source.caches, 'triad_rates',
                    start_date)['triad_gbp_per_gsp_kw'][data_source.dno_code]
                tot_rate += (finish_month - start_month + 1) * float(rt)

        rate = tot_rate / 12
    else:
        rate = float(
            get_file_rates(
                data_source.caches, 'triad_rates',
                month_begin)['triad_gbp_per_gsp_kw'][data_source.dno_code])

    hh[prefix + '-rate'] = rate


def hh(data_source, rate_period='monthly'):
    for hh in (h for h in data_source.hh_data if h['ct-is-month-end']):
        hh_start = hh['start-date']
        month_start = utc_datetime(hh_start.year, hh_start.month)
        month_finish = month_start + relativedelta(months=1) - HH
        month_num = month_start.month

        # Get start of last financial year
        financial_year_start = month_start
        while financial_year_start.month != 4:
            financial_year_start -= relativedelta(months=1)

        last_financial_year_start = financial_year_start - \
            relativedelta(years=1)
        financial_year_finish = financial_year_start + \
            relativedelta(years=1) - HH

        triad_dates = []
        earliest_triad = None
        for dt in get_file_rates(
                data_source.caches, 'triad_dates',
                last_financial_year_start)['triad_dates']:
            triad_dates.append(dt + relativedelta(years=1))
            if earliest_triad is None or dt < earliest_triad:
                earliest_triad = dt

        est_triad_kws = []
        for t_date in triad_dates:
            for ds in chellow.computer.get_data_sources(
                    data_source, t_date, t_date, financial_year_start):
                chellow.duos.duos_vb(ds)
                est_triad_kws.append(ds.hh_data[0])
        if data_source.site is None:
            era = data_source.supply.find_era_at(
                data_source.sess, earliest_triad)
            if era is None or era.get_channel(
                    data_source.sess, data_source.is_import, 'ACTIVE') is None:
                est_triad_kw = 0.85 * max(
                    datum['msp-kwh'] for datum in data_source.hh_data) * 2
                for est_datum in est_triad_kws:
                    est_datum['msp-kw'] = est_triad_kw
                    est_datum['gsp-kw'] = est_datum['msp-kw'] * \
                        est_datum['laf']

        triad_calc(
            hh, 'triad-estimate', est_triad_kws, financial_year_start,
            financial_year_finish, data_source, month_start)

        est_triad_gbp = hh['triad-estimate-rate'] * hh['triad-estimate-gsp-kw']

        if rate_period == 'monthly':
            total_intervals = 12

            est_intervals = 1
            hh['triad-estimate-months'] = est_intervals
        else:
            dt = financial_year_start
            total_intervals = 0
            while dt <= financial_year_finish:
                total_intervals += 1
                dt += relativedelta(days=1)

            est_intervals = 0
            for ds in chellow.computer.get_data_sources(
                    data_source, month_start, month_finish):
                for h in ds.hh_data:
                    if h['utc-decimal-hour'] == 0:
                        est_intervals += 1

            hh['triad-estimate-days'] = est_intervals

        hh['triad-estimate-gbp'] = est_triad_gbp / total_intervals * \
            est_intervals

        if month_num == 3:
            triad_kws = []
            for t_date in get_file_rates(
                    data_source.caches, 'triad_dates',
                    month_start)['triad_dates']:
                try:
                    ds = next(
                        iter(
                            chellow.computer.get_data_sources(
                                data_source, t_date, t_date)))
                    if data_source.supplier_contract is None or \
                            ds.supplier_contract == \
                            data_source.supplier_contract:
                        chellow.duos.duos_vb(ds)
                        thh = ds.hh_data[0]
                    else:
                        thh = {
                            'hist-start': t_date, 'msp-kw': 0,
                            'status': 'before contract',
                            'laf': 'before contract', 'gsp-kw': 0}
                except StopIteration:
                    thh = {
                        'hist-start': t_date, 'msp-kw': 0,
                        'status': 'before start of supply',
                        'laf': 'before start of supply', 'gsp-kw': 0}
                triad_kws.append(thh)

            triad_calc(
                hh, 'triad-actual', triad_kws, financial_year_start,
                financial_year_finish, data_source, month_start)
            hh['triad-actual-gbp'] = hh['triad-actual-rate'] * \
                hh['triad-actual-gsp-kw']

            era = data_source.supply.find_era_at(
                data_source.sess, month_finish)
            est_intervals = 0

            interval = relativedelta(months=1) if \
                rate_period == 'monthly' else relativedelta(days=1)

            dt = month_finish
            while era is not None and dt > financial_year_start:
                est_intervals += 1
                dt -= interval
                if hh_after(dt, era.finish_date):
                    era = data_source.supply.find_era_at(data_source.sess, dt)

            if rate_period == 'monthly':
                hh['triad-all-estimates-months'] = est_intervals
            else:
                hh['triad-all-estimates-days'] = est_intervals
            hh['triad-all-estimates-gbp'] = est_triad_gbp / \
                total_intervals * est_intervals * -1


RATE_TITLES = {
    'triad-estimate-months', 'triad-all-estimates-months',
    'triad-estimate-days', 'triad-all-estimates-days'}
SCALAR_TITLES = {'triad-all-estimates-gbp'}


for eora in ('actual', 'estimate'):
    for i in range(1, 4):
        for suffix, titles in (
                ('date', RATE_TITLES), ('msp-kw', SCALAR_TITLES),
                ('status', RATE_TITLES), ('laf', RATE_TITLES),
                ('gsp-kw', SCALAR_TITLES)):
            titles.add('-'.join(('triad', eora, str(i), suffix)))
    for suf, titles in (
            ('rate', RATE_TITLES), ('gbp', SCALAR_TITLES),
            ('gsp-kw', SCALAR_TITLES)):
        titles.add('-'.join(('triad', eora, suf)))


def bill(ds):
    bill = ds.supplier_bill
    rate_sets = ds.supplier_rate_sets
    for hh in ds.hh_data:
        for title in RATE_TITLES & hh.keys():
            rate_sets[title].add(hh[title])

        for title in SCALAR_TITLES & hh.keys():
            bill[title] += hh[title]
