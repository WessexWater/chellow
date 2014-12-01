from net.sf.chellow.monad import Monad
from datetime import datetime
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
form_int, form_date = utils.form_int, utils.form_date
UserException = utils.UserException
render = templater.render
Contract = db.Contract

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
        contract_id = form_int(inv, 'supplier_contract_id')
        contract = Contract.get_supplier_by_id(sess, contract_id)
        render(inv, template, page_fields(contract))
    else:
        db.set_read_write(sess)
        contract_id = form_int(inv, 'supplier_contract_id')
        contract = Contract.get_supplier_by_id(sess, contract_id)
        start_date = form_date(inv, 'start')
        rate_script = contract.insert_rate_script(sess, start_date, '')
        sess.commit()
        inv.sendSeeOther('/reports/79/output/?supplier_rate_script_id='
                + str(rate_script.id))
except UserException, e:
        render(inv, template, page_fields(contract, str(e)), 400)
finally:
    if sess is not None:
        sess.close()

