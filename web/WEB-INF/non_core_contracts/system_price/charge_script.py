from net.sf.chellow.monad import Monad
import types
from dateutil.relativedelta import relativedelta
import db
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils')
UserException, hh_format = utils.UserException, utils.hh_format
Contract = db.Contract


def identity_func(x):
    return x


def hh(supply_source):
    rate_sets = supply_source.supplier_rate_sets

    try:
        cache = supply_source.caches['system_price']
    except KeyError:
        cache = {}
        supply_source.caches['system_price'] = cache

    for hh in supply_source.hh_data:
        try:
            prices = cache[hh['start-date']]
        except KeyError:
            bmreports_contract = Contract.get_non_core_by_name(
                supply_source.sess, 'system_price_bmreports')
            elexon_contract = Contract.get_non_core_by_name(
                supply_source.sess, 'system_price_elexon')
            prices = {}
            date_str = hh['start-date'].strftime("%d %H:%M Z")
            for pref in ['ssp', 'sbp']:
                transform_func = identity_func
                rate = supply_source.hh_rate(
                    elexon_contract.id, hh['start-date'], pref + 's')
                if isinstance(rate, dict):
                    rate = transform_func(rate)
                    prices[pref + '-gbp-per-kwh'] = float(rate[date_str]) / \
                        1000
                else:
                    rate = supply_source.hh_rate(
                        bmreports_contract.id, hh['start-date'], pref + 's')
                    dt = hh['start-date']
                    while isinstance(rate, types.FunctionType):
                        transform_func = rate
                        dt += relativedelta(years=1)
                        rate = supply_source.hh_rate(
                            bmreports_contract.id, dt, pref + 's')

                    if isinstance(rate, dict):
                        rate = transform_func(rate)
                        prices[pref + '-gbp-per-kwh'] = \
                            float(rate[date_str]) / 1000
                    else:
                        raise UserException(
                            "Type returned by " + pref + "s at " +
                            hh_format(dt) + " must be function or dictionary.")
            cache[hh['start-date']] = prices

        hh.update(prices)
        hh['ssp-gbp'] = hh['nbp-kwh'] * hh['ssp-gbp-per-kwh']
        hh['sbp-gbp'] = hh['nbp-kwh'] * hh['sbp-gbp-per-kwh']
        rate_sets['ssp-rate'].add(hh['ssp-gbp-per-kwh'])
        rate_sets['sbp-rate'].add(hh['sbp-gbp-per-kwh'])
