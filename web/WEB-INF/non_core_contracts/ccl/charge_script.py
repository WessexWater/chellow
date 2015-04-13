from net.sf.chellow.monad import Monad
import datetime
import pytz
import utils
import db
import computer
import scenario
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'computer', 'scenario')
HH = utils.HH
Contract = db.Contract
db_id = globals()['db_id']

create_future_func = scenario.make_create_future_func_simple(
    'ccl', ['ccl_rate'])


def ccl(data_source):
    rate_set = data_source.supplier_rate_sets['ccl-rate']

    if data_source.supply.find_era_at(
            data_source.sess, data_source.finish_date + HH) is None:
        sup_end = data_source.finish_date
    else:
        sup_end = None

    try:
        cache = data_source.caches['ccl']
    except:
        data_source.caches['ccl'] = {}
        cache = data_source.caches['ccl']

        try:
            future_funcs = data_source.caches['future_funcs']
        except KeyError:
            future_funcs = {}
            data_source.caches['future_funcs'] = future_funcs

        try:
            future_funcs[db_id]
        except KeyError:
            future_funcs[db_id] = {
                'start_date': None, 'func': create_future_func(1, 0)}

    if data_source.bill is None:
        for hh in data_source.hh_data:
            if hh['utc-is-month-end'] or hh['start-date'] == sup_end:
                month_finish = hh['start-date']
                kwh = 0
                gbp = 0
                month_start = datetime.datetime(
                    month_finish.year, month_finish.month, 1, tzinfo=pytz.utc)

                for ds in computer.get_data_sources(
                        data_source, month_start, month_finish):
                    for datum in ds.hh_data:
                        try:
                            rate = cache[datum['start-date']]
                        except KeyError:
                            cache[datum['start-date']] = data_source.hh_rate(
                                db_id, datum['start-date'], 'ccl_rate')
                            rate = cache[datum['start-date']]

                        rate_set.add(rate)
                        kwh += datum['msp-kwh']
                        gbp += datum['msp-kwh'] * rate

                if kwh > 999:
                    hh['ccl-kwh'] = kwh
                    hh['ccl-gbp'] = gbp

    elif data_source.is_last_bill_gen:
        if data_source.pc_code in ['03', '04']:
            threshold = 2999
        else:
            threshold = 999
        kwh = 0
        gbp = 0
        for ds in computer.get_data_sources(
                data_source, data_source.bill_start, data_source.bill_finish):
            for hh in ds.hh_data:
                try:
                    rate = cache[hh['start-date']]
                except KeyError:
                    cache[hh['start-date']] = data_source.hh_rate(
                        db_id, hh['start-date'], 'ccl_rate')
                    rate = cache[hh['start-date']]

                rate_set.add(rate)
                kwh += hh['msp-kwh']
                gbp += hh['msp-kwh'] * rate

        if kwh > threshold:
            data_source.hh_data[-1]['ccl-kwh'] = kwh
            data_source.hh_data[-1]['ccl-gbp'] = gbp
