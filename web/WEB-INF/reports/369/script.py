from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from sqlalchemy.sql.expression import text
from datetime import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Supply', 'Batch', 'Participant', 'set_read_write', 'session'], 
        'utils': ['UserException', 'form_date'],
        'templater': ['render']})


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
    sess = session()
    supply_id = inv.getLong('supply_id')
    supply = Supply.get_by_id(sess, supply_id)
    render(inv, template, make_fields(sess, supply))
except UserException, e:
    render(inv, template, make_fields(sess, supply, e))
finally:
    sess.close()