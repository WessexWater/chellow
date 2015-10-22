from net.sf.chellow.monad import Monad
import utils
import templater
import db

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
RateScript = db.RateScript
NotFoundException = utils.NotFoundException
render = templater.render
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    rate_script_id = inv.getLong('rate_script_id')
    rate_script = RateScript.get_non_core_by_id(sess, rate_script_id)
    render(inv, template, {'rate_script': rate_script})
except NotFoundException as e:
    inv.sendNotFound(str(e))
finally:
    if sess is not None:
        sess.close()
