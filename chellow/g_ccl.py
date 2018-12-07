import chellow.scenario
from chellow.utils import HH, utc_datetime, get_file_rates
import chellow.g_engine


THRESHOLD = 4397


def vb(ds, kwh_key='kwh'):
    rate_set = ds.rate_sets['ccl_rate']

    if ds.g_supply.find_g_era_at(ds.sess, ds.finish_date + HH) is None:
        sup_end = ds.finish_date
    else:
        sup_end = None

    if ds.g_bill is None:
        for hh in ds.hh_data:
            if hh['utc_is_month_end'] or hh['start_date'] == sup_end:
                month_finish = hh['start_date']
                kwh = gbp = 0
                month_start = utc_datetime(
                    month_finish.year, month_finish.month, 1)

                for dsr in chellow.g_engine.get_data_sources(
                        ds, month_start, month_finish):
                    for datum in dsr.hh_data:
                        rate = float(
                            get_file_rates(
                                ds.caches, 'g_ccl',
                                datum['start_date'])['ccl_gbp_per_kwh'])

                        rate_set.add(rate)
                        hh_kwh = datum[kwh_key]
                        kwh += hh_kwh
                        gbp += hh_kwh * rate

                if abs(kwh) > THRESHOLD:
                    hh['ccl_kwh'] = kwh
                    hh['ccl_gbp'] = gbp

    elif ds.is_last_g_bill_gen:
        kwh = gbp = 0
        for ds in chellow.g_engine.get_data_sources(
                ds, ds.g_bill_start, ds.g_bill_finish):
            for hh in ds.hh_data:
                rate = float(
                    get_file_rates(
                        ds.caches, 'g_ccl',
                        hh['start_date'])['ccl_gbp_per_kwh'])
                rate_set.add(rate)
                hh_kwh = hh[kwh_key]
                kwh += hh_kwh
                gbp += hh_kwh * rate

        if abs(kwh) > THRESHOLD:
            ds.hh_data[-1]['ccl_kwh'] = kwh
            ds.hh_data[-1]['ccl_gbp'] = gbp
