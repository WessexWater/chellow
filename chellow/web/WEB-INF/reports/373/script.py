from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
UserException = utils.UserException
render = templater.render
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, snag, message=None):
    messages = [] if message is None else [str(message)]
    return {'snag': snag, 'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        snag_id = inv.getLong('site_snag_id')
        snag = db.Snag.get_by_id(sess, snag_id)
        templater.render(inv, template, make_fields(sess, snag))
    else:
        db.set_read_write(sess)
        snag_id = inv.getLong('site_snag_id')
        ignore = inv.getBoolean('ignore')

        snag = db.Snag.get_by_id(sess, snag_id)
        snag.is_ignored = ignore
        sess.commit()
        inv.sendSeeOther("/reports/119/output/?site_snag_id=" + str(snag.id))
except UserException as e:
    sess.rollback()
    templater.render(inv, template, make_fields(sess, snag, e), 400)
finally:
    sess.close()
