from chellow.utils import get_file_rates


def hh(supply_source):
    bill = supply_source.supplier_bill
    rate_set = supply_source.supplier_rate_sets['aahedc-rate']

    for hh in supply_source.hh_data:
        bill['aahedc-gsp-kwh'] += hh['gsp-kwh']
        rate = float(
            get_file_rates(
                supply_source.caches, 'aahedc',
                hh['start-date'])['aahedc_gbp_per_gsp_kwh'])
        rate_set.add(rate)
        bill['aahedc-gbp'] += hh['gsp-kwh'] * rate
