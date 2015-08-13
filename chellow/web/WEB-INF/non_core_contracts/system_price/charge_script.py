from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from net.sf.chellow.monad import Monad
import db
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils')
UserException, hh_format = utils.UserException, utils.hh_format
Contract, RateScript = db.Contract, db.RateScript


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
            elexon_contract = Contract.get_non_core_by_name(
                supply_source.sess, 'system_price_elexon')

            h_start = hh['start-date']

            elexon_rs = supply_source.sess.query(RateScript).filter(
                RateScript.contract == elexon_contract,
                RateScript.start_date <= h_start, or_(
                    RateScript.finish_date == null(),
                    RateScript.finish_date >= h_start)).first()
            if elexon_rs is None:
                bmreports_contract = Contract.get_non_core_by_name(
                    supply_source.sess, 'system_price_bmreports')
                ssp = supply_source.hh_rate(
                    bmreports_contract.id, h_start, 'ssps')
                sbp = supply_source.hh_rate(
                    bmreports_contract.id, h_start, 'sbps')
            else:
                ssp = supply_source.hh_rate(
                    elexon_contract.id, h_start, 'ssps')
                sbp = supply_source.hh_rate(
                    elexon_contract.id, h_start, 'sbps')

            date_str = h_start.strftime("%d %H:%M Z")
            ssp_val = float(ssp[date_str]) / 1000
            sbp_val = float(sbp[date_str]) / 1000
            prices = {'ssp-gbp-per-kwh': ssp_val, 'sbp-gbp-per-kwh': sbp_val}
            cache[h_start] = prices

        hh.update(prices)
        hh['ssp-gbp'] = hh['nbp-kwh'] * hh['ssp-gbp-per-kwh']
        hh['sbp-gbp'] = hh['nbp-kwh'] * hh['sbp-gbp-per-kwh']
        rate_sets['ssp-rate'].add(hh['ssp-gbp-per-kwh'])
        rate_sets['sbp-rate'].add(hh['sbp-gbp-per-kwh'])
