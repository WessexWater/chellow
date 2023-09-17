def ccl(data_source):
    try:
        ccl_cache = data_source.caches["ccl"]
    except KeyError:
        ccl_cache = data_source.caches["ccl"] = {}

    for hh in data_source.hh_data:
        try:
            rate = ccl_cache[hh["start-date"]]
        except KeyError:
            hh_start = hh["start-date"]
            rates = data_source.non_core_rate("ccl", hh_start)
            rate = ccl_cache[hh_start] = float(rates["ccl_gbp_per_msp_kwh"])

        hh["ccl-kwh"] = hh["msp-kwh"]
        hh["ccl-rate"] = rate
        hh["ccl-gbp"] = hh["msp-kwh"] * rate
