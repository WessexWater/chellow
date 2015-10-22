from net.sf.chellow.monad import Monad
import utils
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, snag, message=None):
    messages = [] if message is None else [str(message)]
    return {'messages': messages, 'snag': snag}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        snag_id = utils.form_int(inv, 'site_snag_id')
        snag = db.Snag.get_by_id(sess, snag_id)
        templater.render(inv, template, make_fields(sess, snag))
except UserException as e:
    templater.render(inv, template, make_fields(sess, snag, e), 400)
finally:
    if sess is not None:
        sess.close()
