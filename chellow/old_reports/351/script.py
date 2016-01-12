from net.sf.chellow.monad import Monad
from datetime import datetime
import pytz
import db
import templater
import utils
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
Contract = db.Contract
render = templater.render
form_date, UserException = utils.form_date, utils.UserException
inv, template = globals()['inv'], globals()['template']


def page_fields(contract, message=None):
    now = datetime.now(pytz.utc)
    initial_date = datetime(now.year, now.month, 1, tzinfo=pytz.utc)
    messages = None if message is None else [message]
    return {
        'contract': contract, 'initial_date': initial_date,
        'messages': messages}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        contract_id = inv.getLong('mop_contract_id')
        contract = Contract.get_mop_by_id(sess, contract_id)
        render(inv, template, page_fields(contract))
    else:
        db.set_read_write(sess)
        contract_id = inv.getLong('mop_contract_id')
        contract = Contract.get_mop_by_id(sess, contract_id)
        start_date = form_date(inv, 'start')
        rate_script = contract.insert_rate_script(sess, start_date, '')
        sess.commit()
        inv.sendSeeOther(
            '/reports/205/output/?mop_rate_script_id=' + str(rate_script.id))
except UserException as e:
        render(inv, template, page_fields(contract, str(e)))
finally:
    sess.close()
