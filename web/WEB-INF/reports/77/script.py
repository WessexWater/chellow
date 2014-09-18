from net.sf.chellow.monad import Monad
import datetime
from dateutil.relativedelta import relativedelta

Monad.getUtils()['imprt'](globals(), {
        'db': ['Contract', 'Party', 'RateScript', 'set_read_write', 'session'], 
        'utils': ['UserException'],
        'templater': ['render']})

sess = None
try:
    sess = session()

    contract_id = inv.getLong('supplier_contract_id')
    if contract_id is None:
        contract_id = inv.getLong('supplier-contract-id')
    contract = Contract.get_supplier_by_id(sess, contract_id)
    rate_scripts = sess.query(RateScript).filter(RateScript.contract_id==contract.id).order_by(RateScript.start_date).all()

    now = datetime.datetime.utcnow() - relativedelta(months=1)
    month_start = datetime.datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - relativedelta(minutes=30)

    render(inv, template, {'contract': contract, 'month_start': month_start, 'month_finish': month_finish, 'rate_scripts': rate_scripts})

finally:
    sess.close()