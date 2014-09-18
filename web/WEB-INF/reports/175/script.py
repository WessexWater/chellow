from java.util import GregorianCalendar, TimeZone, Locale, Calendar
from net.sf.chellow.monad.types import MonadDate

cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
if cal.get(Calendar.MONTH) < Calendar.MARCH:
    cal.add(Calendar.YEAR, -1)
source.setAttribute('year', str(cal.get(Calendar.YEAR)))