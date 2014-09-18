from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from sqlalchemy.sql.expression import text
from datetime import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Supply', 'Batch', 'Participant', 'set_read_write', 'session'], 
        'utils': ['UserException', 'form_date'],
        'templater': ['render']})


def make_fields(sess, supply, index, message=None):
    messages = [] if message is None else [str(message)]
    supply_note = eval(supply.note)
    note = supply_note['notes'][index]
    note['index'] = index
    return {'supply': supply, 'messages': messages, 'note': note}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        supply_id = inv.getLong('supply_id')
        supply = Supply.get_by_id(sess, supply_id)
        index = inv.getLong('note_index')
        render(inv, template, make_fields(sess, supply, index))
    else:
        if inv.hasParameter('update'):
            set_read_write(sess)
            supply_id = inv.getLong('supply_id')
            supply = Supply.get_by_id(sess, supply_id)
            index = inv.getLong('note_index')
            category = inv.getString('category')
            is_important = inv.getBoolean('is_important')
            body = inv.getString('body')
            supply_note = eval(supply.note)
            note = supply_note['notes'][index]
            note['category'] = category
            note['is_important'] = is_important
            note['body'] = body
            supply.note = str(supply_note)
            sess.commit()
            inv.sendSeeOther("/reports/369/output/?supply_id=" + str(supply_id))
        elif inv.hasParameter('delete'):
            set_read_write(sess)
            supply_id = inv.getLong('supply_id')
            supply = Supply.get_by_id(sess, supply_id)
            index = inv.getLong('note_index')
            supply_note = eval(supply.note)
            del supply_note['notes'][index]
            supply.note = str(supply_note)
            sess.commit()
            inv.sendSeeOther("/reports/369/output/?supply_id=" + str(supply_id))

except UserException, e:
    render(inv, template, make_fields(sess, supply, index, e))
finally:
    sess.close()