from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from sqlalchemy.sql.expression import text
from datetime import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Supply', 'Batch', 'Participant', 'set_read_write', 'session'], 
        'utils': ['UserException', 'form_date', 'form_str', 'form_int'],
        'templater': ['render']})


def make_fields(sess, supply, message=None):
    messages = [] if message is None else [str(message)]
    return {'supply': supply, 'messages': messages}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        supply_id = inv.getLong('supply_id')
        supply = Supply.get_by_id(sess, supply_id)
        render(inv, template, make_fields(sess, supply))
    else:
        set_read_write(sess)
        supply_id = form_int(inv, 'supply_id')
        supply = Supply.get_by_id(sess, supply_id)
        body = form_str(inv, 'body')
        category = form_str(inv, 'category')
        is_important = inv.getBoolean('is_important')
        if len(supply.note.strip()) == 0:
            supply.note = "{'notes': []}"
        note_dict = eval(supply.note)
        note_dict['notes'].append({'category': category, 'is_important': is_important, 'body': body})
        supply.note = str(note_dict)
        sess.commit()
        inv.sendSeeOther("/reports/369/output/?supply_id=" + str(supply_id))
except UserException, e:
    render(inv, template, make_fields(sess, supply, e))
finally:
    sess.close()