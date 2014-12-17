from net.sf.chellow.monad import Monad
import utils
import templater
import db
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
form_str, form_int = utils.form_str, utils.form_int
render = templater.render
Era = db.Era
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    if inv.hasParameter('search_pattern'):
        pattern = form_str(inv, "search_pattern")
        pattern = pattern.strip()
        reduced_pattern = pattern.replace(" ", "")
        if inv.hasParameter("max_results"):
            max_results = form_int(inv, 'max_results')
        else:
            max_results = 50
        eras = sess.query(Era).from_statement(
            "select e1.* from era as e1 "
            "inner join (select e2.supply_id, max(e2.start_date) "
            "as max_start_date from era as e2 "
            "where replace(lower(e2.imp_mpan_core), ' ', '') "
            "like lower(:reducedPattern) "
            "or lower(e2.imp_supplier_account) like lower(:pattern) "
            "or replace(lower(e2.exp_mpan_core), ' ', '') "
            "like lower(:reducedPattern) "
            "or lower(e2.exp_supplier_account) like lower(:pattern) "
            "or lower(e2.hhdc_account) like lower(:pattern) "
            "or lower(e2.mop_account) like lower(:pattern) "
            "or lower(e2.msn) like lower(:pattern) "
            "group by e2.supply_id) as sq "
            "on e1.supply_id = sq.supply_id "
            "and e1.start_date = sq.max_start_date limit :max_results").params(
            pattern="%" + pattern + "%",
            reducedPattern="%" + reduced_pattern + "%",
            max_results=max_results).all()
        if len(eras) == 1:
            inv.sendTemporaryRedirect(
                "/reports/7/output/?supply_id=" + str(eras[0].supply.id))
        else:
            render(inv, template, {'eras': eras, 'max_results': max_results})
    else:
        render(inv, template, {})
finally:
    if sess is not None:
        sess.close()
