from chellow.utils import get_file_rates


def hh(supply_source):
    try:
        supply_source.caches["ro"]
    except KeyError:
        supply_source.caches["ro"] = {}

    for hh in supply_source.hh_data:
        rate = float(
            get_file_rates(supply_source.caches, "ro", hh["start-date"])[
                "ro_gbp_per_msp_kwh"
            ]
        )
        hh["ro-rate"] = rate
        hh["ro-msp-kwh"] = hh["msp-kwh"]
        hh["ro-gbp"] = hh["msp-kwh"] * rate
