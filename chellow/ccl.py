import chellow.computer
import chellow.scenario
from chellow.utils import get_file_rates


create_future_func = chellow.scenario.make_create_future_func_simple(
    'ccl', ['ccl_rate'])


def ccl(data_source):
    rate_set = data_source.supplier_rate_sets['ccl-rate']
    cache = data_source.caches

    try:
        future_funcs = data_source.caches['future_funcs']
    except KeyError:
        future_funcs = {}
        data_source.caches['future_funcs'] = future_funcs

    try:
        future_funcs['ccl']
    except KeyError:
        future_funcs['ccl'] = {
            'start_date': None, 'func': create_future_func(1, 0)}

    for hh in data_source.hh_data:
        rates = get_file_rates(cache, 'ccl', hh['start-date'])
        rate = float(rates['ccl_gbp_per_msp_kwh'])
        rate_set.add(rate)
        hh['ccl-kwh'] = hh['msp-kwh']
        hh['ccl-rate'] = rate
        hh['ccl-gbp'] = hh['msp-kwh'] * rate
