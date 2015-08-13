from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Supply = db.Supply
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, supply, message=None):
    messages = [] if message is None else [str(message)]

    if len(supply.note.strip()) > 0:
        note_str = supply.note
    else:
        note_str = "{'notes': []}"
    supply_note = eval(note_str)

    return {'supply': supply, 'messages': messages, 'supply_note': supply_note}

sess = None
try:
    sess = db.session()
    supply_id = inv.getLong('supply_id')
    supply = Supply.get_by_id(sess, supply_id)
    render(inv, template, make_fields(sess, supply))
except UserException, e:
    render(inv, template, make_fields(sess, supply, e))
finally:
    sess.close()
