from net.sf.chellow.monad import Monad
from datetime import datetime
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

def make_fields():
    initial_date = datetime.utcnow().replace(tzinfo=pytz.utc)
    initial_date = datetime(initial_date.year, initial_date.month, 1)
    return {'initial_date': initial_date}

sess = None
try:
    sess = db.session()
    if inv.getRequest().getMethod() == 'GET':
        templater.render(inv, template, make_fields())
    else:
        db.set_read_write(sess)
        name = inv.getString('name')
        is_core = inv.getBoolean('is_core')
        start_date = utils.form_date(inv, 'start')
        contract = db.Contract.insert_non_core(
            sess, is_core, name, '{}', '{}', start_date, None, '{}')
        sess.commit()
        inv.sendSeeOther(
            '/reports/267/output/?non_core_contract_id=' + str(contract.id))
finally:
    if sess is not None:
        sess.close()
