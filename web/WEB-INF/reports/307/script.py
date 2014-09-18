from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Channel', 'Era', 'Supply', 'Source', 'GeneratorType', 'GspGroup', 'Pc', 'Cop', 'Contract', 'MarketRole', 'SiteEra', 'Site', 'Mtc', 'Ssc', 'set_read_write', 'session'], 
        'utils': ['UserException', 'form_date', 'form_decimal', 'hh_after', 'hh_before', 'validate_hh_start', 'parse_mpan_core'],
        'templater': ['render']})

def make_fields(sess, era, message=None):
    messages = [] if message is None else [str(message)]
    pcs = sess.query(Pc).order_by(Pc.code)
    cops = sess.query(Cop).order_by(Cop.code)
    gsp_groups = sess.query(GspGroup).order_by(GspGroup.code)
    mop_contracts = sess.query(Contract).join(MarketRole).filter(MarketRole.code == 'M').order_by(Contract.name)
    hhdc_contracts = sess.query(Contract).join(MarketRole).filter(MarketRole.code == 'C').order_by(Contract.name)
    supplier_contracts = sess.query(Contract).join(MarketRole).filter(MarketRole.code == 'X').order_by(Contract.name)
    site_eras = sess.query(SiteEra).join(Site).filter(SiteEra.era == era).order_by(Site.code).all()
    return {'era': era, 'messages': messages, 'pcs': pcs, 'cops': cops, 'gsp_groups': gsp_groups, 'mop_contracts': mop_contracts, 'hhdc_contracts': hhdc_contracts, 'supplier_contracts': supplier_contracts, 'site_eras': site_eras}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        era_id = inv.getLong('era_id')
        era = Era.get_by_id(sess, era_id)
        render(inv, template, make_fields(sess, era))
    else:
        set_read_write(sess)
        era_id = inv.getLong('era_id')
        era = Era.get_by_id(sess, era_id)

        if inv.hasParameter("delete"):
            supply = era.supply
            supply.delete_era(sess, era)
            sess.commit()
            inv.sendSeeOther("/reports/7/output/?supply_id=" + str(supply.id))
        elif inv.hasParameter("attach"):
            site_code = inv.getString("site_code")
            site = Site.get_by_code(sess, site_code)
            era.attach_site(sess, site)
            sess.commit()
            inv.sendSeeOther("/reports/7/output/?supply_id=" + str(era.supply.id))
        elif inv.hasParameter("detach"):
            site_id = inv.getLong("site_id")
            site = Site.get_by_id(sess, site_id)
            era.detach_site(sess, site)
            sess.commit()
            inv.sendSeeOther("/reports/7/output/?supply_id=" + str(era.supply.id))
        elif inv.hasParameter("locate"):
            site_id = inv.getLong("site_id")
            site = Site.get_by_id(sess, site_id)
            era.set_physical_location(sess, site)
            sess.commit()
            inv.sendSeeOther("/reports/7/output/?supply_id=" + str(era.supply.id))
        else:
            start_date = form_date(inv, 'start')
            is_ended = inv.getBoolean("is_ended")
            if is_ended:
                finish_date = form_date(inv, "finish")
                validate_hh_start(finish_date)
            else:
                finish_date = None
            mop_contract_id = inv.getLong("mop_contract_id")
            mop_contract = Contract.get_mop_by_id(sess, mop_contract_id)
            mop_account = inv.getString("mop_account")
            hhdc_contract_id = inv.getLong("hhdc_contract_id")
            hhdc_contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)
            hhdc_account = inv.getString("hhdc_account")
            msn = inv.getString("msn")
            pc_id = inv.getLong("pc_id")
            pc = Pc.get_by_id(sess, pc_id)
            mtc_code = inv.getString("mtc_code")
            mtc = Mtc.get_by_code(sess, era.supply.dno_contract.party, mtc_code)
            cop_id = inv.getLong("cop_id")
            cop = Cop.get_by_id(sess, cop_id)
            ssc_code = inv.getString("ssc_code")
            ssc_code = ssc_code.strip()
            ssc = None if len(ssc_code) == 0 else Ssc.get_by_code(sess, ssc_code)

            if inv.hasParameter('imp_mpan_core'):
                imp_mpan_core_raw = inv.getString('imp_mpan_core')
            else:
                imp_mpan_core_raw = None

            if imp_mpan_core_raw is None or len(imp_mpan_core_raw.strip()) == 0:
                imp_mpan_core = None
                imp_sc = None
                imp_supplier_contract = None
                imp_supplier_account = None
                imp_llfc_code = None
            else:
                imp_mpan_core = parse_mpan_core(imp_mpan_core_raw)
                imp_llfc_code = inv.getString('imp_llfc_code')
                imp_supplier_contract_id = inv.getLong("imp_supplier_contract_id")
                imp_supplier_contract = Contract.get_supplier_by_id(sess, imp_supplier_contract_id)
                imp_supplier_account = inv.getString("imp_supplier_account")
                imp_sc = inv.getInteger("imp_sc")

            if inv.hasParameter('exp_mpan_core'):
                exp_mpan_core_raw = inv.getString('exp_mpan_core')
            else:
                exp_mpan_core_raw = None

            if exp_mpan_core_raw is None or len(exp_mpan_core_raw.strip()) == 0:
                exp_mpan_core = None
                exp_llfc_code = None
                exp_sc = None
                exp_supplier_contract = None
                exp_supplier_account = None
            else:
                exp_mpan_core = parse_mpan_core(exp_mpan_core_raw)
                exp_llfc_code = inv.getString("exp_llfc_code")
                exp_sc = inv.getInteger("exp_sc")
                exp_supplier_contract_id = inv.getLong('exp_supplier_contract_id')
                exp_supplier_contract = Contract.get_supplier_by_id(sess, exp_supplier_contract_id)
                exp_supplier_account = inv.getString('exp_supplier_account')

            era.supply.update_era(sess, era, start_date, finish_date, mop_contract, mop_account, hhdc_contract, hhdc_account, msn, pc, mtc, cop, ssc, imp_mpan_core, imp_llfc_code, imp_supplier_contract, imp_supplier_account, imp_sc, exp_mpan_core, exp_llfc_code, exp_supplier_contract, exp_supplier_account, exp_sc)
            sess.commit()
            inv.sendSeeOther("/reports/7/output/?supply_id=" + str(era.supply.id))
except UserException, e:
    render(inv, template, make_fields(sess, era, e), 400)
finally:
    sess.close()