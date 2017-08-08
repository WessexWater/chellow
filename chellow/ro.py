import chellow.scenario
from chellow.utils import get_file_rates


create_future_func = chellow.scenario.make_create_future_func_simple(
    'ro', ['gbp_per_msp_kwh'])


def hh(supply_source):
    bill = supply_source.supplier_bill
    rate_set = supply_source.supplier_rate_sets['ro-rate']

    try:
        supply_source.caches['ro']
    except KeyError:
        supply_source.caches['ro'] = {}

        try:
            future_funcs = supply_source.caches['future_funcs']
        except KeyError:
            future_funcs = {}
            supply_source.caches['future_funcs'] = future_funcs

        try:
            future_funcs['ro']
        except KeyError:
            future_funcs['ro'] = {
                'start_date': None, 'func': create_future_func(1, 0)}

    for hh in supply_source.hh_data:
        rate = float(
            get_file_rates(
                supply_source.caches, 'ro', hh['start-date'])
            ['ro_gbp_per_msp_kwh'])
        rate_set.add(rate)
        bill['ro-msp-kwh'] += hh['msp-kwh']
        bill['ro-gbp'] += hh['msp-kwh'] * rate
