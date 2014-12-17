from net.sf.chellow.monad import Monad
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Supply = db.Supply
render = templater.render
UserException = utils.UserException
inv, template = globals()['inv'], globals()['template']


def make_fields(sess, supply, index, message=None):
    messages = [] if message is None else [str(message)]
    supply_note = eval(supply.note)
    note = supply_note['notes'][index]
    note['index'] = index
    return {'supply': supply, 'messages': messages, 'note': note}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        supply_id = inv.getLong('supply_id')
        supply = Supply.get_by_id(sess, supply_id)
        index = inv.getLong('note_index')
        render(inv, template, make_fields(sess, supply, index))
    else:
        if inv.hasParameter('update'):
            db.set_read_write(sess)
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
            inv.sendSeeOther(
                "/reports/369/output/?supply_id=" + str(supply_id))
        elif inv.hasParameter('delete'):
            db.set_read_write(sess)
            supply_id = inv.getLong('supply_id')
            supply = Supply.get_by_id(sess, supply_id)
            index = inv.getLong('note_index')
            supply_note = eval(supply.note)
            del supply_note['notes'][index]
            supply.note = str(supply_note)
            sess.commit()
            inv.sendSeeOther(
                "/reports/369/output/?supply_id=" + str(supply_id))

except UserException, e:
    render(inv, template, make_fields(sess, supply, index, e))
finally:
    sess.close()
