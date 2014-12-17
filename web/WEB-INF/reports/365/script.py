from net.sf.chellow.monad import Monad
import templater
import utils
import db
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
inv, template = globals()['inv'], globals()['templater']


def make_fields(sess, snag, message=None):
    messages = [] if message is None else [str(message)]
    return {'snag': snag, 'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        snag_id = inv.getLong('snag_id')
        snag = db.Snag.get_by_id(sess, snag_id)
        templater.render(inv, template, make_fields(sess, snag))
    else:
        db.set_read_write(sess)
        snag_id = inv.getLong('snag_id')
        ignore = inv.getBoolean('ignore')

        snag = db.Snag.get_by_id(sess, snag_id)
        snag.is_ignored = ignore
        sess.commit()
        inv.sendSeeOther("/reports/117/output/?snag_id=" + str(snag.id))
except utils.UserException, e:
    sess.rollback()
    templater.render(inv, template, make_fields(sess, snag, e), 400)
finally:
    sess.close()
