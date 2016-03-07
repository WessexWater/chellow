import chellow.scenario
from chellow.models import Session, Contract

sess = None
try:
    sess = Session()
    db_id = Contract.get_non_core_by_name(sess, 'aahedc').id
finally:
    if sess is not None:
        sess.close()

create_future_func = chellow.scenario.make_create_future_func_simple(
    'aahedc', ['aahedc_gbp_per_gsp_kwh'])


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
            future_funcs = {}
            supply_source.caches['future_funcs'] = future_funcs

        try:
            future_funcs[db_id]
        except KeyError:
            future_funcs[db_id] = {
                'start_date': None, 'func': create_future_func(1, 0)}

    for hh in supply_source.hh_data:
        bill['aahedc-msp-kwh'] += hh['msp-kwh']
        bill['aahedc-gsp-kwh'] += hh['gsp-kwh']
        rate = supply_source.hh_rate(
            db_id, hh['start-date'], 'aahedc_gbp_per_gsp_kwh')
        rate_set.add(rate)
        bill['aahedc-gbp'] += hh['gsp-kwh'] * rate
