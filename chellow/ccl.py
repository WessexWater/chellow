from chellow.utils import get_file_rates


def ccl(data_source):
    cache = data_source.caches

    for hh in data_source.hh_data:
        rates = get_file_rates(cache, 'ccl', hh['start-date'])
        rate = float(rates['ccl_gbp_per_msp_kwh'])
        hh['ccl-kwh'] = hh['msp-kwh']
        hh['ccl-rate'] = rate
        hh['ccl-gbp'] = hh['msp-kwh'] * rate
