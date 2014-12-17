from net.sf.chellow.monad import Monad
import datetime
from dateutil.relativedelta import relativedelta
import utils
import db
import templater
Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')
HH = utils.HH
RateScript = db.RateScript
inv, template = globals()['inv'], globals()['template']

sess = None
try:
    sess = db.session()

    contract_id = inv.getLong('supplier_contract_id')
    if contract_id is None:
        contract_id = inv.getLong('supplier-contract-id')
    contract = db.Contract.get_supplier_by_id(sess, contract_id)
    rate_scripts = sess.query(RateScript).filter(
        RateScript.contract_id == contract.id).order_by(
        RateScript.start_date).all()

    now = datetime.datetime.utcnow() - relativedelta(months=1)
    month_start = datetime.datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH

    templater.render(
        inv, template, {
            'contract': contract, 'month_start': month_start,
            'month_finish': month_finish, 'rate_scripts': rate_scripts})
finally:
    if sess is not None:
        sess.close()
