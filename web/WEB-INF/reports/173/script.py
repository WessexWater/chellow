from net.sf.chellow.monad import Monad

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

sess = None
try:
    sess = db.session()
    rate_script_id = inv.getLong('hhdc_rate_script_id')
    rate_script = db.RateScript.get_hhdc_by_id(sess, rate_script_id)
    templater.render(inv, template, {'rate_script': rate_script})
finally:
    if sess is not None:
        sess.close()
