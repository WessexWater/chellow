import chellow.scenario
from chellow.utils import get_file_rates


create_future_func = chellow.scenario.make_create_future_func_simple('aahedc')


def hh(supply_source):
    bill = supply_source.supplier_bill
    rate_set = supply_source.supplier_rate_sets['aahedc-rate']

    try:
        supply_source.caches['aahedc']
    except KeyError:
        supply_source.caches['aahedc'] = {}

        try:
            future_funcs = supply_source.caches['future_funcs']
        except KeyError:
            future_funcs = supply_source.caches['future_funcs'] = {}

        try:
            future_funcs['aahedc']
        except KeyError:
            future_funcs['aahedc'] = {
                'start_date': None, 'func': create_future_func(1, 0)}

    for hh in supply_source.hh_data:
        bill['aahedc-gsp-kwh'] += hh['gsp-kwh']
        rate = float(
            get_file_rates(
                supply_source.caches, 'aahedc',
                hh['start-date'])['aahedc_gbp_per_gsp_kwh'])
        rate_set.add(rate)
        bill['aahedc-gbp'] += hh['gsp-kwh'] * rate
