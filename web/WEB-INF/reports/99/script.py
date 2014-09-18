from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Era', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()
    if inv.hasParameter('search_pattern'):
        pattern = inv.getString("search_pattern")
        pattern = pattern.strip()
        reduced_pattern = pattern.replace(" ", "")
        if inv.hasParameter("max_results"):
            max_results = inv.getInteger('max_results')
        else:
            max_results = 50
        eras = sess.query(Era).from_statement("select e1.* from era as e1 inner join (select e2.supply_id, max(e2.start_date) as max_start_date from era as e2 where replace(lower(e2.imp_mpan_core), ' ', '') like lower(:reducedPattern) or lower(e2.imp_supplier_account) like lower(:pattern) or replace(lower(e2.exp_mpan_core), ' ', '') like lower(:reducedPattern) or lower(e2.exp_supplier_account) like lower(:pattern) or lower(e2.hhdc_account) like lower(:pattern) or lower(e2.mop_account) like lower(:pattern) or lower(e2.msn) like lower(:pattern) group by e2.supply_id) as sq on e1.supply_id = sq.supply_id and e1.start_date = sq.max_start_date limit :max_results").params(pattern="%" + pattern + "%", reducedPattern="%" + reduced_pattern + "%", max_results=max_results).all()
        if len(eras) == 1:
            inv.sendTemporaryRedirect("/reports/7/output/?supply_id=" + str(eras[0].supply.id))
        else:
            render(inv, template, {'eras': eras, 'max_results': max_results})
    else:
        render(inv, template, {})
finally:
    if sess is not None:
        sess.close()