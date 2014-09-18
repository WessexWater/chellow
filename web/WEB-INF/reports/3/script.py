from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all

Monad.getUtils()['imprt'](globals(), {
        'db': ['Site', 'Party', 'Era', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

LIMIT = 50
sess = None
try:
    sess = session()
    if inv.hasParameter('pattern'):
        pattern = inv.getString("pattern")
        #pattern = pattern.strip()
        sites = sess.query(Site).from_statement("select * from site where lower(code || ' ' || name) like '%' || lower(:pattern) || '%' order by code limit :lim").params(pattern=pattern, lim=LIMIT).all()

        if len(sites) == 1:
            inv.sendTemporaryRedirect("/reports/5/output/?site_id=" + str(sites[0].id))
        else:
            render(inv, template, {'sites': sites, 'limit': LIMIT})
    else:
        render(inv, template, {})
finally:
    if sess is not None:
        sess.close()