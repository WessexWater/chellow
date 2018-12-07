from chellow.utils import get_file_rates


def ccl(data_source):
    rate_set = data_source.supplier_rate_sets['ccl-rate']
    cache = data_source.caches

    for hh in data_source.hh_data:
        rates = get_file_rates(cache, 'ccl', hh['start-date'])
        rate = float(rates['ccl_gbp_per_msp_kwh'])
        rate_set.add(rate)
        hh['ccl-kwh'] = hh['msp-kwh']
        hh['ccl-rate'] = rate
        hh['ccl-gbp'] = hh['msp-kwh'] * rate
