from net.sf.chellow.monad import Monad
import datetime
import pytz
import utils
import computer
import scenario
Monad.getUtils()['impt'](globals(), 'utils', 'computer', 'scenario')
HH = utils.HH
db_id = globals()['db_id']

create_future_func = scenario.make_create_future_func_simple(
    'ccl', ['ccl_rate'])

THRESHOLD = 4397


def vb(data_source):
    rate_set = data_source.rate_sets['ccl_rate']

    if data_source.g_supply.find_g_era_at(
            data_source.sess, data_source.finish_date + HH) is None:
        sup_end = data_source.finish_date
    else:
        sup_end = None

    try:
        cache = data_source.caches['g_ccl']
    except:
        data_source.caches['g_ccl'] = {}
        cache = data_source.caches['g_ccl']

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

    if data_source.g_bill is None:
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
                            rate = cache[datum['start_date']]
                        except KeyError:
                            cache[datum['start_date']] = data_source.rate(
                                db_id, datum['start_date'], 'ccl_gbp_per_kwh')
                            rate = cache[datum['start_date']]

                        rate_set.add(rate)
                        kwh += datum['kwh']
                        gbp += datum['kwh'] * rate

                if kwh > THRESHOLD:
                    hh['ccl_kwh'] = kwh
                    hh['ccl_gbp'] = gbp

    elif data_source.is_last_g_bill_gen:
        kwh = 0
        gbp = 0
        for ds in computer.get_data_sources(
                data_source, data_source.g_bill_start,
                data_source.g_bill_finish):
            for hh in ds.hh_data:
                try:
                    rate = cache[hh['start_date']]
                except KeyError:
                    cache[hh['start_date']] = data_source.rate(
                        db_id, hh['start_date'], 'ccl_rate')
                    rate = cache[hh['start_date']]

                rate_set.add(rate)
                kwh += hh['kwh']
                gbp += hh['kwh'] * rate

        if kwh > THRESHOLD:
            data_source.hh_data[-1]['ccl_kwh'] = kwh
            data_source.hh_data[-1]['ccl_gbp'] = gbp
