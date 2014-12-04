from net.sf.chellow.monad import Monad
import db
import templater

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Site = db.Site
render = templater.render
inv, template = globals()['inv'], globals()['template']

LIMIT = 50
sess = None
try:
    sess = db.session()
    if inv.hasParameter('pattern'):
        pattern = inv.getString("pattern")
        sites = sess.query(Site).from_statement(
            "select * from site "
            "where lower(code || ' ' || name) like '%' || lower(:pattern) "
            "|| '%' order by code limit :lim").params(
            pattern=pattern, lim=LIMIT).all()

        if len(sites) == 1:
            inv.sendTemporaryRedirect(
                "/reports/5/output/?site_id=" + str(sites[0].id))
        else:
            render(inv, template, {'sites': sites, 'limit': LIMIT})
    else:
        render(inv, template, {})
finally:
    if sess is not None:
        sess.close()
