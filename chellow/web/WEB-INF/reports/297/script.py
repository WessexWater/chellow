from net.sf.chellow.monad import Monad
import templater
import utils
import db
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, message=None):
    messages = [] if message is None else [str(e)]
    return {'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        render(inv, template, make_fields(sess))
    else:
        db.set_read_write(sess)
        code = inv.getString("code")
        name = inv.getString("name")
        site = db.Site.insert(sess, code, name)
        sess.commit()
        inv.sendSeeOther("/reports/5/output/?site_id=" + str(site.id))
except UserException as e:
    render(inv, template, make_fields(sess, e))
finally:
    if sess is not None:
        sess.close()
