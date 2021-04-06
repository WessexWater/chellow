from chellow.utils import get_file_rates


def hh(supply_source):
    for hh in supply_source.hh_data:
        hh["aahedc-kwh"] = hh["gsp-kwh"]
        rate = float(
            get_file_rates(supply_source.caches, "aahedc", hh["start-date"])[
                "aahedc_gbp_per_gsp_kwh"
            ]
        )
        hh["aahedc-rate"] = rate
        hh["aahedc-gbp"] = hh["gsp-kwh"] * rate
