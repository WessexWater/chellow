from datetime import datetime as Datetime
import pytz
from chellow.models import Session, Contract
import chellow.computer
import chellow.scenario
from chellow.utils import HH

sess = None
try:
    sess = Session()
    ccl_contract_id = Contract.get_non_core_by_name(sess, 'ccl').id
finally:
    if sess is not None:
        sess.close()


create_future_func = chellow.scenario.make_create_future_func_simple(
    'ccl', ['ccl_rate'])


def ccl(data_source, ct_month=False):
    rate_set = data_source.supplier_rate_sets['ccl-rate']
    end_key = 'ct-is-month-end' if ct_month else 'utc-is-month-end'

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
            future_funcs[ccl_contract_id]
        except KeyError:
            future_funcs[ccl_contract_id] = {
                'start_date': None, 'func': create_future_func(1, 0)}

    if data_source.bill is None:
        for hh in data_source.hh_data:
            if hh[end_key] or hh['start-date'] == sup_end:
                month_finish = hh['start-date']
                kwh = 0
                gbp = 0
                month_start = Datetime(
                    month_finish.year, month_finish.month, 1, tzinfo=pytz.utc)

                for ds in chellow.computer.get_data_sources(
                        data_source, month_start, month_finish):
                    for datum in ds.hh_data:
                        try:
                            rate = cache[datum['start-date']]
                        except KeyError:
                            cache[datum['start-date']] = data_source.hh_rate(
                                ccl_contract_id, datum['start-date'],
                                'ccl_rate')
                            rate = cache[datum['start-date']]

                        rate_set.add(rate)
                        kwh += datum['msp-kwh']
                        gbp += datum['msp-kwh'] * rate

                if kwh > 999:
                    hh['ccl-kwh'] = kwh
                    hh['ccl-gbp'] = gbp

    elif data_source.is_last_bill_gen:
        kwh = 0
        gbp = 0
        for ds in chellow.computer.get_data_sources(
                data_source, data_source.bill_start, data_source.bill_finish):
            for hh in ds.hh_data:
                try:
                    rate = cache[hh['start-date']]
                except KeyError:
                    cache[hh['start-date']] = data_source.hh_rate(
                        ccl_contract_id, hh['start-date'], 'ccl_rate')
                    rate = cache[hh['start-date']]

                rate_set.add(rate)
                kwh += hh['msp-kwh']
                gbp += hh['msp-kwh'] * rate

        hhs = (
            data_source.bill_finish - data_source.bill_start).total_seconds()
        if (kwh / hhs) > ((1000 * 12) / (365 * 24 * 60 * 60)):
            data_source.hh_data[-1]['ccl-kwh'] = kwh
            data_source.hh_data[-1]['ccl-gbp'] = gbp
