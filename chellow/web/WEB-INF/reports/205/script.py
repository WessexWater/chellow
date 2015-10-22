from net.sf.chellow.monad import Monad
import utils
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
RateScript = db.RateScript

NotFoundException = utils.NotFoundException
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    rate_script_id = inv.getLong('mop_rate_script_id')
    rate_script = RateScript.get_mop_by_id(sess, rate_script_id)
    render(inv, template, {'rate_script': rate_script})
except NotFoundException as e:
    inv.sendNotFound(str(e))
finally:
    sess.close()
