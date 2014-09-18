from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
from datetime import datetime
import pytz

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException', 'form_date'],
        'templater': ['render']})

def page_fields(contract, message=None):
    now = datetime.now(pytz.utc)
    initial_date = datetime(now.year, now.month, 1, tzinfo=pytz.utc)
    messages = None if message is None else [message]
    return {'contract': contract, 'initial_date': initial_date,
        'messages': messages}

sess = None
try:
    sess = session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('non_core_contract_id')
        contract = Contract.get_non_core_by_id(sess, contract_id)
        render(inv, template, page_fields(contract))
    else:
        set_read_write(sess)
        contract_id = inv.getLong('non_core_contract_id')
        contract = Contract.get_non_core_by_id(sess, contract_id)
        start_date = form_date(inv, 'start')
        rate_script = contract.insert_rate_script(sess, start_date, '')
        sess.commit()
        inv.sendSeeOther('/reports/271/output/?rate_script_id='
                + str(rate_script.id))
except UserException, e:
        render(inv, template, page_fields(contract, str(e)))
finally:
    sess.close()