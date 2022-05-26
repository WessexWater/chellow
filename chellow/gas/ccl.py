from chellow.gas.engine import g_rates
from chellow.models import get_g_industry_contract_id


DAILY_THRESHOLD = 145


def vb(ds):
    ccl_id = get_g_industry_contract_id("ccl")
    for hh in ds.hh_data:
        rate = float(
            g_rates(ds.sess, ds.caches, ccl_id, hh["start_date"])["ccl_gbp_per_kwh"]
        )

        hh["ccl"] = rate
