from net.sf.chellow.monad import Monad
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'computer', 'duos', 'triad_rates')

HH, hh_after, hh_format = utils.HH, utils.hh_after, utils.hh_format
Contract, RateScript = db.Contract, db.RateScript

def triad_calc(bill, prefix, triad_data, financial_year_start, financial_year_finish, data_source, month_begin):
    gsp_kw = 0
    for i, triad_hh in enumerate(triad_data):
        triad_prefix = prefix + '-' + str(i + 1)
        bill[triad_prefix + '-date'] = hh_format(triad_hh['hist-start-date'])
        bill[triad_prefix + '-msp-kw'] = triad_hh['msp-kw']
        bill[triad_prefix + '-status'] = triad_hh['status']
        bill[triad_prefix + '-laf'] = triad_hh['laf']
        bill[triad_prefix + '-gsp-kw'] = triad_hh['gsp-kw']
        gsp_kw += triad_hh['gsp-kw']

    bill[prefix + '-gsp-kw'] = gsp_kw / 3

    if prefix == 'triad-actual':
        tot_rate = 0
        for rate_script in data_source.sess.query(RateScript).filter(RateScript.contract_id==triad_rates.db_id, RateScript.start_date<=financial_year_finish, or_(RateScript.finish_date==None, RateScript.finish_date>=financial_year_start)).order_by(RateScript.start_date):
            start_month = rate_script.start_date.month
            if start_month < 4:
                start_month += 12
            rate_finish_date = rate_script.finish_date
            if rate_finish_date is None:
                finish_month = financial_year_finish.month
            else:
                finish_month = rate_script.finish_date.month

            if finish_month < 4:
                finish_month += 12

            #data_source.pw .println("finish month " + str(finish_month) + " start month " + str(start_month) + " rate " + str(data_source.rate(rate_script, 'hh_demand_gbp_per_kw')[data_source.dno_code]))

            tot_rate += float(finish_month - start_month + 1) * data_source.hh_rate(triad_rates.db_id, rate_script.start_date, 'hh_demand_gbp_per_kw')[data_source.dno_code]
        rate = tot_rate / float(12)
    else:
        rate = data_source.hh_rate(triad_rates.db_id, month_begin, 'hh_demand_gbp_per_kw')[data_source.dno_code]
    #data_source.pw .println("triad rate " + str(rate))
    bill[prefix + '-rate'] = rate

def triad_bill(data_source, rate_period='monthly'):
    bill = data_source.supplier_bill
    for hh in (h for h in data_source.hh_times if h['utc-is-month-end']):
        month_finish = hh['start-date']
        month_start = month_finish + HH - relativedelta(months=1) 
        month_num = month_start.month

        # Get start of last financial year
        financial_year_start = month_start
        while financial_year_start.month != 4:
            financial_year_start -= relativedelta(months=1)
            
        last_financial_year_start = financial_year_start - relativedelta(years=1)
        financial_year_finish = financial_year_start + relativedelta(years=1) - HH

        triad_dates = []
        earliest_triad = None
        for dt in data_source.hh_rate(db_id, last_financial_year_start, 'triad_dates'):
            triad_dates.append(dt + relativedelta(years=1))
            if earliest_triad is None or dt < earliest_triad:
                earliest_triad = dt

        est_triad_kws = []
        for t_date in triad_dates:
            for ds in computer.get_data_sources(data_source, t_date, t_date, financial_year_start):
                duos.duos_vb(ds)
                est_triad_kws.append(ds.hh_data[0])

        if data_source.site is None:
            era = data_source.supply.find_era_at(data_source.sess, earliest_triad)
            if era is None or era.get_channel(data_source.sess, data_source.is_import, 'ACTIVE') is None:
                est_triad_kw = 0.85 * max(datum['msp-kwh'] for datum in data_source.hh_data) * 2
                for est_datum in est_triad_kws:
                    est_datum['msp-kw'] = est_triad_kw
                    est_datum['gsp-kw'] = est_datum['msp-kw'] * est_datum['laf']
        
        triad_calc(bill, 'triad-estimate', est_triad_kws, financial_year_start, financial_year_finish, data_source, month_start)

        est_triad_gbp = bill['triad-estimate-rate'] * bill['triad-estimate-gsp-kw']

        if rate_period == 'monthly':
            interval_type = 'month'
            total_intervals = 12

            est_intervals = 1
            bill['triad-estimate-months'] = est_intervals
        else:
            dt = financial_year_start
            total_intervals = 0
            while dt <= financial_year_finish:
                total_intervals += 1
                dt += relativedelta(days=1)

            interval_type = 'day'

            est_intervals = sum(ds.utc_days for ds in computer.get_data_sources(data_source, month_start, month_finish))
            bill['triad-estimate-days'] = est_intervals

        bill['triad-estimate-gbp'] = est_triad_gbp / total_intervals * est_intervals

        if month_num == 3:
            #T1 Date, T1 MSP kW, T1 Status, T1 LAF, T1 GSP kW, T2 Date, T2 MSP kW, T2 Status, T2 LAF, T2 GSP kW, T3 Date, T3 MSP kW, T3 Status, T3 LAF, T3 GSP kW, GSP kW, GBP
            triad_kws = []
            for t_date in data_source.hh_rate(db_id, month_start, 'triad_dates'):
                try:
                    ds = iter(computer.get_data_sources(data_source, t_date, t_date)).next()
                    if data_source.supplier_contract is None or ds.supplier_contract == data_source.supplier_contract:
                        duos.duos_vb(ds)
                        thh = ds.hh_data[0]
                    else:
                        thh = {'hist-start-date': t_date, 'msp-kw': 0, 'status': 'before contract', 'laf': 'before contract', 'gsp-kw': 0}
                except StopIteration:
                    thh = {'hist-start-date': t_date, 'msp-kw': 0, 'status': 'before start of supply', 'laf': 'before start of supply', 'gsp-kw': 0}
                triad_kws.append(thh)

            triad = triad_calc(bill, 'triad-actual', triad_kws, financial_year_start, financial_year_finish, data_source, month_start)
            bill['triad-actual-gbp'] = bill['triad-actual-rate'] * bill['triad-actual-gsp-kw']

            era = data_source.supply.find_era_at(data_source.sess, month_finish)
            est_intervals = 0
            march_intervals = 0
            
            interval = relativedelta(months=1) if rate_period == 'monthly' else relativedelta(days=1)
            
            dt = month_finish
            while era is not None and dt > financial_year_start:
                est_intervals += 1                
                dt -= interval
                if hh_after(dt, era.finish_date):
                    era = sup.find_era_at(data_source.sess, dt)
                    
            if rate_period == 'monthly':
                bill['triad-all-estimates-months'] = est_intervals
            else:
                bill['triad-all-estimates-days'] = est_intervals
            bill['triad-all-estimates-gbp'] = est_triad_gbp / total_intervals * est_intervals * -1