def hh(supply_source):
    try:
        aahedc_cache = supply_source.caches["aahedc"]
    except KeyError:
        aahedc_cache = supply_source.caches["aahedc"] = {}

    for hh in supply_source.hh_data:
        hh["aahedc-kwh"] = hh["gsp-kwh"]
        try:
            rate = aahedc_cache[hh["start-date"]]
        except KeyError:
            hh_start = hh["start-date"]
            rates = supply_source.non_core_rate("aahedc", hh_start)
            rate = aahedc_cache[hh_start] = float(rates["aahedc_gbp_per_gsp_kwh"])

        hh["aahedc-rate"] = rate
        hh["aahedc-gbp"] = hh["gsp-kwh"] * rate
