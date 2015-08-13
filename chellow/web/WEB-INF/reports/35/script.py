from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'templater', 'db', 'utils')
GspGroup = db.GspGroup
form_int = utils.form_int
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()
    group_id = form_int(inv, 'gsp_group_id')
    group = GspGroup.get_by_id(sess, group_id)
    templater.render(inv, template, {'group': group})
finally:
    if sess is not None:
        sess.close()
