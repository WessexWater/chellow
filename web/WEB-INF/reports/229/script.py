from java.util import GregorianCalendar, TimeZone, Locale, Calendar
from net.sf.chellow.monad.types import MonadDate
from net.sf.chellow.monad import Hiber, UserException
from net.sf.chellow.billing import Contract

contract_id = inv.getLong('mop_contract_id')
if not inv.isValid():
    raise UserException()

contract = Contract.getMopContract(contract_id)


cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
cal.add(Calendar.MONTH, -1)
source.appendChild(MonadDate(cal.getTime()).toXml(doc))
source.appendChild(MonadDate.getMonthsXml(doc))
source.appendChild(contract.toXml(doc))