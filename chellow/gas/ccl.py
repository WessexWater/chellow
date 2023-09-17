from chellow.gas.engine import g_rates


DAILY_THRESHOLD = 145


def vb(ds):
    for hh in ds.hh_data:
        rate = float(
            g_rates(ds.sess, ds.caches, "ccl", hh["start_date"], True)[
                "ccl_gbp_per_kwh"
            ]
        )

        hh["ccl"] = rate
