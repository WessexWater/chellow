def hh(supply_source):
    try:
        ro_cache = supply_source.caches["ro"]
    except KeyError:
        ro_cache = supply_source.caches["ro"] = {}

    for hh in supply_source.hh_data:
        try:
            hh["ro-rate"] = ro_rate = ro_cache[hh["start-date"]]
        except KeyError:
            h_start = hh["start-date"]
            hh["ro-rate"] = ro_rate = ro_cache[h_start] = float(
                supply_source.non_core_rate("ro", h_start)["ro_gbp_per_msp_kwh"]
            )

        ro_kwh = hh["msp-kwh"]
        hh["ro-msp-kwh"] = ro_kwh
        hh["ro-gbp"] = ro_kwh * ro_rate
