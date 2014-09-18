from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.monad.types import MonadDate
from net.sf.chellow.physical import Site
from java.util import Calendar
from java.lang import System

site_id = inv.getLong("site_id")
if not inv.isValid():
    raise UserException()

if inv.hasParameter('finish_year'):
    year = inv.getInteger("finish_year")
    month = inv.getInteger("finish_month")
    months = inv.getInteger("months")
    if not inv.isValid():
        raise UserException()

    site = Site.getSite(site_id)
    source.appendChild(site.toXml(doc))

    source.appendChild(MonadDate.getMonthsXml(doc))
else:
    cal = MonadDate.getCalendar()
    cal.setTimeInMillis(System.currentTimeMillis())
    inv.sendTemporaryRedirect('/reports/11/output/?site_id=' + str(site_id) + '&months=1&finish_month=' + str(cal.get(Calendar.MONTH) + 1) + '&finish_year=' + str(cal.get(Calendar.YEAR)))