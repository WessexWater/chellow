from chellow.utils import get_file_rates


def vb(ds):
    to_exit_commodity_rate_set = ds.rate_sets['to_exit_commodity_rate']
    so_exit_commodity_rate_set = ds.rate_sets['so_exit_commodity_rate']
    dn_system_commodity_rate_set = ds.rate_sets['dn_system_commodity_rate']
    dn_system_capacity_rate_set = ds.rate_sets['dn_system_capacity_rate']
    dn_system_capacity_fixed_rate_set = ds.rate_sets[
        'dn_system_capacity_fixed_rate']
    dn_customer_capacity_rate_set = ds.rate_sets['dn_customer_capacity_rate']
    dn_customer_capacity_fixed_rate_set = ds.rate_sets[
        'dn_customer_capacity_fixed_rate']
    dn_customer_fixed_rate_set = ds.rate_sets['dn_customer_fixed_rate']
    dn_ecn_rate_set = ds.rate_sets['dn_ecn_rate']
    dn_ecn_fixed_rate_set = ds.rate_sets['dn_ecn_fixed_rate']

    for hh in ds.hh_data:
        soq = hh['soq']
        aq = hh['aq']
        nts_rates = get_file_rates(
            ds.caches, 'g_nts_commodity', hh['start_date'])

        to_exit_commodity_rate = float(nts_rates['to_exit_gbp_per_kwh'])
        to_exit_commodity_rate_set.add(to_exit_commodity_rate)
        hh['to_exit_commodity_rate'] = to_exit_commodity_rate

        so_exit_commodity_rate = float(nts_rates['so_exit_gbp_per_kwh'])
        so_exit_commodity_rate_set.add(so_exit_commodity_rate)
        hh['so_exit_commodity_rate'] = so_exit_commodity_rate

        rates = get_file_rates(ds.caches, 'g_dn', hh['start_date'])
        dn_rates = rates['gdn'][ds.g_dn_code]
        system_commodity_rates = dn_rates['system_commodity']
        system_capacity_rates = dn_rates['system_capacity']
        customer_capacity_rates = dn_rates['customer_capacity']
        customer_fixed_rates = dn_rates['customer_fixed']

        if aq <= 73200:
            pref = 'to_73200_'
            dn_system_commodity_rate = float(
                system_commodity_rates[pref + 'gbp_per_kwh'])
            dn_system_capacity_rate = float(
                system_capacity_rates[pref + 'gbp_per_kwh_per_day'])
            dn_customer_capacity_rate = float(
                customer_capacity_rates[pref + 'gbp_per_kwh_per_day'])
            dn_customer_fixed_rate = 0
        elif 73200 < aq < 732000:
            pref = '73200_to_732000_'
            dn_system_commodity_rate = float(
                system_commodity_rates[pref + 'gbp_per_kwh'])
            dn_system_capacity_rate = float(
                system_capacity_rates[pref + 'gbp_per_kwh_per_day'])
            dn_customer_capacity_rate = float(
                customer_capacity_rates[pref + 'gbp_per_kwh_per_day'])
            if aq < 293000:
                dn_customer_fixed_rate = float(
                    customer_fixed_rates[pref + "biannual_gbp_per_day"])
            else:
                dn_customer_fixed_rate = float(
                    customer_fixed_rates[pref + "monthly_gbp_per_day"])

        else:
            key = '732000_and_over'

            system_commodity_rts = system_commodity_rates[key]
            dn_system_commodity_rate = max(
                float(system_commodity_rts['minimum_gbp_per_kwh']),
                float(system_commodity_rts['gbp_per_kwh']) * soq **
                float(system_commodity_rts['exponent'])
            )

            system_capacity_rts = system_capacity_rates[key]
            dn_system_capacity_rate = max(
                float(system_capacity_rts['minimum_gbp_per_kwh_per_day']),
                float(system_capacity_rts['gbp_per_kwh_per_day']) * soq **
                float(system_capacity_rts['exponent']))

            customer_capacity_rts = customer_capacity_rates[key]
            dn_customer_capacity_rate = float(
                customer_capacity_rts['gbp_per_kwh_per_day']) * soq ** float(
                customer_capacity_rts['exponent'])

            dn_customer_fixed_rate = 0

        dn_system_commodity_rate_set.add(dn_system_commodity_rate)
        hh['dn_system_commodity_rate'] = dn_system_commodity_rate

        dn_system_capacity_rate_set.add(dn_system_capacity_rate)
        hh['dn_system_capacity_rate'] = dn_system_capacity_rate

        dn_system_capacity_fixed_rate = soq * dn_system_capacity_rate
        dn_system_capacity_fixed_rate_set.add(dn_system_capacity_fixed_rate)
        hh['dn_system_capacity_fixed_rate'] = dn_system_capacity_fixed_rate

        dn_customer_capacity_rate_set.add(dn_customer_capacity_rate)
        hh['dn_customer_capacity_rate'] = dn_customer_capacity_rate

        dn_customer_capacity_fixed_rate = soq * dn_customer_capacity_rate
        dn_customer_capacity_fixed_rate_set.add(
            dn_customer_capacity_fixed_rate)
        hh['dn_customer_capacity_fixed_rate'] = dn_customer_capacity_fixed_rate

        dn_customer_fixed_rate_set.add(dn_customer_fixed_rate)
        hh['dn_customer_fixed_rate'] = dn_customer_fixed_rate

        dn_ecn_rate = float(rates['exit_zones'][ds.g_exit_zone_code][
            'exit_capacity_gbp_per_kwh_per_day'])
        dn_ecn_rate_set.add(dn_ecn_rate)
        hh['dn_ecn_rate'] = dn_ecn_rate

        dn_ecn_fixed_rate = dn_ecn_rate * soq
        dn_ecn_fixed_rate_set.add(dn_ecn_fixed_rate)
        hh['dn_ecn_fixed_rate'] = dn_ecn_fixed_rate
