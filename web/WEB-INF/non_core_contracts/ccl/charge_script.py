from net.sf.chellow.monad import Monad
import datetime
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'computer')

HH = utils.HH
Contract = db.Contract

def ccl(data_source):
    bill = data_source.supplier_bill

    prefix = 'lec' if data_source.is_green else 'ccl'
    rate_set = data_source.supplier_rate_sets[prefix + '-rate']

    if data_source.supply.find_era_at(data_source.sess, data_source.finish_date + HH) == None:
        sup_end = data_source.finish_date
    else:
        sup_end = None

    try:
        cache = data_source.caches['ccl']
    except:
        data_source.caches['ccl'] = {}
        cache = data_source.caches['ccl']

    if data_source.bill is None:
        for hh_time in data_source.hh_times:
            if hh_time['utc-is-month-end'] or hh_time['start-date'] == sup_end:
                month_finish = hh_time['start-date']
                kwh = 0
                gbp = 0
                month_start = datetime.datetime(month_finish.year, month_finish.month, 1, tzinfo=pytz.utc)

                for ds in computer.get_data_sources(data_source, month_start, month_finish):
                    for hh in ds.hh_data:
                        try:
                            rate = cache[hh['start-date']]
                        except KeyError:
                            cache[hh['start-date']] = data_source.hh_rate(db_id, hh['start-date'], 'ccl_rate')
                            rate = cache[hh['start-date']]

                        rate_set.add(rate)
                        kwh += hh['msp-kwh']
                        gbp += hh['msp-kwh'] * rate

                if kwh > 999:
                    bill[prefix + '-kwh'] += kwh
                    bill[prefix + '-gbp'] += gbp
        if len(rate_set) == 1:
            bill[prefix + '-rate'] = rate_set.pop()

    elif data_source.is_last_bill_gen:
        if data_source.pc_code in ['03', '04']:
            threshold = 2999
        else:
            threshold = 999
        kwh = 0
        gbp = 0
        for ds in computer.get_data_sources(data_source, data_source.bill_start, data_source.bill_finish):
            for hh in ds.hh_data:
                try:
                    rate = cache[hh['start-date']]
                except KeyError:
                    cache[hh['start-date']] = data_source.hh_rate(db_id, hh['start-date'], 'ccl_rate')
                    rate = cache[hh['start-date']]

                rate_set.add(rate)
                kwh += hh['msp-kwh']
                gbp += hh['msp-kwh'] * rate

        if kwh > threshold:
            bill[prefix + '-kwh'] += kwh
            bill[prefix + '-gbp'] += gbp
