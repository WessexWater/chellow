from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Snag, Site = db.Snag, db.Site
render = templater.render

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        render(inv, template, {})
    else:
        db.set_read_write(sess)
        finish_date = utils.form_date(inv, 'ignore')
        sess.execute(
            "update snag set is_ignored = true "
            "where snag.site_id is not null and "
            "snag.finish_date < :finish_date", {'finish_date': finish_date})
        sess.commit()
        inv.sendSeeOther('/reports/39/output/')
except utils.UserException, e:
        render(inv, template, {'messages': [str(e)]}, 400)
finally:
    if sess is not None:
        sess.close()
