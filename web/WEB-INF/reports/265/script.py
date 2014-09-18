from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from datetime import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'Participant', 'set_read_write', 'session'], 
        'utils': ['UserException', 'form_date'],
        'templater': ['render']})

def make_fields():
    initial_date = datetime.utcnow().replace(tzinfo=pytz.utc)
    initial_date = datetime(initial_date.year, initial_date.month, 1)
    return {'initial_date': initial_date}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        render(inv, template, make_fields())
    else:
        set_read_write(sess)
        name = inv.getString('name')
        is_core = inv.getBoolean('is_core')
        start_date = form_date(inv, 'start')
        contract = Contract.insert_non_core(sess, is_core, name, '{}', '{}',
                start_date, None, '{}')
        sess.commit()
        inv.sendSeeOther('/reports/267/output/?non_core_contract_id=' +
            str(contract.id))
finally:
    sess.close()