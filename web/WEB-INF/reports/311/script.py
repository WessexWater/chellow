from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
import datetime
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Source, GeneratorType, GspGroup = db.Source, db.GeneratorType, db.GspGroup
SiteEra, Contract, Pc, Cop = db.SiteEra, db.Contract, db.Pc, db.Cop
Site, MarketRole, Era = db.Site, db.MarketRole, db.Era
UserException = utils.UserException
render = templater.render

def make_fields(sess, site, message=None):
    messages = [] if message is None else [str(message)]
    sources = sess.query(Source).order_by(Source.code)
    generator_types = sess.query(GeneratorType).order_by(GeneratorType.code)
    gsp_groups = sess.query(GspGroup).order_by(GspGroup.code)
    eras = sess.query(Era).join(SiteEra).filter(
        SiteEra.site == site).order_by(Era.start_date.desc())
    mop_contracts = sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'M').order_by(Contract.name)
    hhdc_contracts = sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'C').order_by(Contract.name)
    supplier_contracts = sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'X').order_by(Contract.name)
    pcs = sess.query(Pc).order_by(Pc.code)
    cops = sess.query(Cop).order_by(Cop.code)
    return {
        'site': site, 'messages': messages, 'sources': sources,
        'generator_types': generator_types, 'gsp_groups': gsp_groups,
        'eras': eras, 'mop_contracts': mop_contracts,
        'hhdc_contracts': hhdc_contracts,
        'supplier_contracts': supplier_contracts, 'pcs': pcs, 'cops': cops}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        site_id = inv.getLong('site_id')
        site = Site.get_by_id(sess, site_id)
        render(inv, template, make_fields(sess, site))
    else:
        db.set_read_write(sess)
        site_id = inv.getLong('site_id')
        site = Site.get_by_id(sess, site_id)

        if inv.hasParameter("delete"):
            site.delete(sess)
            sess.commit()
            inv.sendSeeOther("/reports/3/output/")
        elif inv.hasParameter("update"):
            code = inv.getString("code")
            name = inv.getString("name")
            site.update(code, name)
            sess.commit()
            inv.sendSeeOther("/reports/5/output/?site_id=" + str(site.id))
        elif inv.hasParameter("insert"):
            name = inv.getString("name")
            source_id = inv.getLong("source_id")
            source = Source.get_by_id(sess, source_id)
            gsp_group_id = inv.getLong("gsp_group_id")
            gsp_group = GspGroup.get_by_id(sess, gsp_group_id)
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
            cop_id = inv.getLong("cop_id")
            cop = Cop.get_by_id(sess, cop_id)
            ssc_code = inv.getString("ssc_code")
            ssc_code = ssc_code.strip()
            if len(ssc_code) > 0:
                ssc = Ssc.get_by_code(sess, ssc_code)
            else:
                ssc = None
            start_date = form_date(inv, "start")
            if inv.hasParameter('generator_type_id'):
                generator_type_id = inv.getLong("generator_type_id")
                generator_type = GeneratorType.get_by_id(
                    sess, generator_type_id)
            else:
                generator_type = None

            if inv.hasParameter('imp_mpan_core'):
                imp_mpan_core_raw = inv.getString('imp_mpan_core')
                if len(imp_mpan_core_raw) == 0:
                    imp_mpan_core = None
                else:
                    imp_mpan_core = parse_mpan_core(imp_mpan_core_raw)
            else:
                imp_mpan_core = None

            if imp_mpan_core is None:
                imp_supplier_contract = None
                imp_supplier_account = None
                imp_sc = None
                imp_llfc_code = None
            else:
                imp_supplier_contract_id = inv.getLong(
                    "imp_supplier_contract_id")
                imp_supplier_contract = Contract.get_supplier_by_id(
                    sess, imp_supplier_contract_id)
                imp_supplier_account = inv.getString("imp_supplier_account")
                imp_sc= inv.getInteger('imp_sc')
                imp_llfc_code = inv.getString("imp_llfc_code")

            if inv.hasParameter('exp_mpan_core'):
                exp_mpan_core_raw = inv.getString('exp_mpan_core')
                if len(exp_mpan_core_raw) == 0:
                    exp_mpan_core = None
                else:
                    exp_mpan_core = parse_mpan_core(exp_mpan_core_raw)
            else:
                exp_mpan_core = None

            if exp_mpan_core is None:
                exp_supplier_contract = None
                exp_supplier_account = None
                exp_sc = None
                exp_llfc_code = None
            else:
                exp_supplier_contract_id = inv.getLong(
                    "exp_supplier_contract_id")
                exp_supplier_contract = Contract.get_supplier_by_id(
                    sess, exp_supplier_contract_id)
                exp_supplier_account = inv.getString("exp_supplier_account")
                exp_sc= inv.getInteger('exp_sc')
                exp_llfc_code = inv.getString("exp_llfc_code")

            supply = site.insert_supply(
                sess, source, generator_type, name, start_date, None,
                gsp_group, mop_contract, mop_account, hhdc_contract,
                hhdc_account, msn, pc, mtc_code, cop, ssc, imp_mpan_core,
                imp_llfc_code, imp_supplier_contract, imp_supplier_account,
                imp_sc, exp_mpan_core, exp_llfc_code, exp_supplier_contract,
                exp_supplier_account, exp_sc)
            sess.commit()
            inv.sendSeeOther("/reports/7/output/?supply_id=" + str(supply.id))
except UserException, e:
    sess.rollback()
    render(inv, template, make_fields(sess, site, e), 400)
finally:
    if sess is not None:
        sess.close()
