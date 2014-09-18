from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
import datetime
from dateutil.relativedelta import relativedelta
import pytz

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

HH = utils.HH
Contract, RateScript = db.Contract, db.RateScript

sess = None
try:
    sess = db.session()
    contract_id = inv.getLong('mop_contract_id')
    contract = Contract.get_mop_by_id(sess, contract_id)
    rate_scripts = sess.query(RateScript).filter(RateScript.contract_id==contract.id).order_by(RateScript.start_date.desc()).all()
    now = datetime.datetime.utcnow().replace(tzinfo=pytz.utc)
    last_month_start = datetime.datetime(now.year, now.month, 1, tzinfo=pytz.utc) - relativedelta(months=1)
    last_month_finish = last_month_start + relativedelta(months=1) - HH
    templater.render(inv, template, {'contract': contract, 'rate_scripts': rate_scripts, 'last_month_start': last_month_start, 'last_month_finish': last_month_finish})
finally:
    if sess is not None:
        sess.close()