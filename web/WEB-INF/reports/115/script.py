from net.sf.chellow.monad import Monad
from sqlalchemy.orm import joinedload_all
import datetime
import pytz
from dateutil.relativedelta import relativedelta

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater')

RateScript = db.RateScript

sess = None
rate_scripts = None
try:
    sess = db.session()
    contract_id = inv.getLong('hhdc_contract_id')
    contract = db.Contract.get_hhdc_by_id(sess, contract_id)
    rate_scripts = sess.query(RateScript).filter(RateScript.contract_id == contract.id).order_by(RateScript.start_date.desc()).all()
    now = datetime.datetime.now(pytz.utc)
    last_month_finish = datetime.datetime(now.year, now.month, 1) - relativedelta(minutes=30)
    templater.render(inv, template, {'contract': contract, 'rate_scripts': rate_scripts, 'last_month_finish': last_month_finish})
except utils.UserException, e:
    if str(e).startswith("There isn't a contract"):
        inv.sendNotFound(str(e))
    else:
        templater.render(inv, template, {'messages': [str(e)], 'contract': contract, 'rate_scripts': rate_scripts})
finally:
    if sess is not None:
        sess.close()