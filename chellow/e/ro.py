from chellow.models import get_non_core_contract_id


def hh(supply_source):
    try:
        ro_cache = supply_source.caches["ro"]
    except KeyError:
        ro_cache = supply_source.caches["ro"] = {}

    for hh in supply_source.hh_data:
        try:
            hh["ro-rate"] = ro_rate = ro_cache[hh["start-date"]]
        except KeyError:
            db_id = get_non_core_contract_id("ro")
            h_start = hh["start-date"]
            hh["ro-rate"] = ro_rate = ro_cache[h_start] = float(
                supply_source.hh_rate(db_id, h_start)["ro_gbp_per_msp_kwh"]
            )

        ro_kwh = hh["msp-kwh"]
        hh["ro-msp-kwh"] = ro_kwh
        hh["ro-gbp"] = ro_kwh * ro_rate
