from net.sf.chellow.monad import Monad
from java.lang import System

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

Snag, Site = db.Snag, db.Site

sess = None

try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        snags = sess.query(Snag).filter(Snag.is_ignored==False, Snag.site_id!=None).order_by(Snag.start_date.desc(), Snag.id).all()
        site_count = sess.query(Snag).join(Site).filter(Snag.is_ignored==False).distinct(Site.id).count()
        templater.render(inv, template, {'snags': snags, 'site_count': site_count})
except utils.UserException, e:
        render(inv, template, {'messages': [str(e)]}, 400)
finally:
    if sess is not None:
        sess.close()