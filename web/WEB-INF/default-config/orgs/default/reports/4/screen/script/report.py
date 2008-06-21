from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.monad.types import MonadDate
from java.util import Calendar

siteId = inv.getLong("site-id")
source.appendChild(organization.getSite(siteId).toXml(XmlTree('organization'), doc))
cal = MonadDate.getCalendar()
if inv.hasParameter("finish-date-year") and inv.hasParameter("finish-date-month"):
    year = inv.getInteger("finish-date-year")
    month = inv.getInteger("finish-date-month")
else:
    year = cal.get(Calendar.YEAR)
    month = cal.get(Calendar.MONTH) + 1
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