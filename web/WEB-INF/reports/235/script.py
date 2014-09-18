from java.util import GregorianCalendar, TimeZone, Locale, Calendar
from net.sf.chellow.monad.types import MonadDate

cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
cal.add(Calendar.MONTH, -1)
source.appendChild(MonadDate(cal.getTime()).toXml(doc))
source.appendChild(MonadDate.getMonthsXml(doc))
source.appendChild(MonadDate.getDaysXml(doc))