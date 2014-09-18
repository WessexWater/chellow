from java.util import GregorianCalendar, TimeZone, Locale, Calendar, Date
from net.sf.chellow.monad.types import MonadDate
from net.sf.chellow.monad import Hiber, UserException
from net.sf.chellow.physical import HhStartDate


source.appendChild(MonadDate.getMonthsXml(doc))
source.appendChild(MonadDate.getDaysXml(doc))
source.appendChild(MonadDate.getHoursXml(doc))
source.appendChild(HhStartDate.getHhMinutesXml(doc))

supplier_contracts_elem = doc.createElement('supplier-contracts')
source.appendChild(supplier_contracts_elem)
for contract in Hiber.session().createQuery("from Contract contract order by contract.name").list():
    supplier_contracts_elem.appendChild(contract.toXml(doc))

cal = MonadDate.getCalendar()
cal.setTime(Date())
cal.set(Calendar.DAY_OF_MONTH, 1)
cal.set(Calendar.HOUR_OF_DAY, 0)
cal.set(Calendar.MINUTE, 0)
cal.set(Calendar.SECOND, 0)
cal.set(Calendar.MILLISECOND, 0)
cal.add(Calendar.MINUTE, -30)
to_date = HhStartDate(cal.getTime())
to_date.setLabel('to')
source.appendChild(to_date.toXml(doc))

cal.add(Calendar.MINUTE, 30)
cal.add(Calendar.MONTH, -1)
from_date = HhStartDate(cal.getTime())
from_date.setLabel('from')
source.appendChild(from_date.toXml(doc))