from chellow.utils import get_file_rates


DAILY_THRESHOLD = 145


def vb(ds):
    for hh in ds.hh_data:
        rate = float(
            get_file_rates(
                ds.caches, 'g_ccl', hh['start_date'])['ccl_gbp_per_kwh'])

        hh['ccl'] = rate
