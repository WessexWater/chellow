from net.sf.chellow.monad import Monad
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
RateScript = db.RateScript
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    rate_script_id = inv.getLong('dno_rate_script_id')
    rate_script = RateScript.get_dno_by_id(sess, rate_script_id)
    render(inv, template, {'rate_script': rate_script})
finally:
    if sess is not None:
        sess.close()
