from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.monad.types import MonadDate
from java.util import Calendar

siteId = inv.getLong("site-id")
source.appendChild(organization.getSite(siteId).toXml(doc))
cal = MonadDate.getCalendar()
if inv.hasParameter("finish-date-year"):
    year = inv.getInteger("finish-date-year")
else:
    year = cal.get(Calendar.YEAR)
source.setAttribute("finish-date-year", str(year))
if inv.hasParameter("finish-date-month"):
    month = inv.getInteger("finish-date-month")
else:
    month = cal.get(Calendar.MONTH)
if inv.hasParameter("months"):
    months = inv.getInteger("months")
else:
    months = 1
for i in range(12):
    monthElement = doc.createElement("month")
    source.appendChild(monthElement)
    monthElement.setAttribute("value", str(i + 1))
source.setAttribute("finish-date-year", str(year))
source.setAttribute("finish-date-month", str(month))
source.setAttribute("months", str(months))
source.appendChild(inv.requestXml(doc))