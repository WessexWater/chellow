from chellow.utils import get_file_rates


THRESHOLD = 145


def vb(ds, kwh_key='kwh'):
    rate_set = ds.rate_sets['ccl_rate']
    kwh = gbp = 0
    for hh in ds.hh_data:
        if hh['utc_decimal_hour'] == 0:
            if abs(kwh) > THRESHOLD:
                hh['ccl_kwh'] = kwh
                hh['ccl_gbp'] = gbp
            kwh = gbp = 0

        rate = float(
            get_file_rates(
                ds.caches, 'g_ccl', hh['start_date'])['ccl_gbp_per_kwh'])

        rate_set.add(rate)
        hh_kwh = hh[kwh_key]
        kwh += hh_kwh
        gbp += hh_kwh * rate
