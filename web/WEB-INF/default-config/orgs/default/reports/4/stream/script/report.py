import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import net.sf.chellow.monad.vf.bo

if inv.hasParameter("site-id"):
    siteId = inv.getMonadLong("site-id")
    source.appendChild(organization.getSite(siteId).getXML(net.sf.chellow.monad.vf.bo.XMLTree("suppliesByStartDate",
                net.sf.chellow.monad.vf.bo.XMLTree("generationLast", net.sf.chellow.monad.vf.bo.XMLTree("mpans", net.sf.chellow.monad.vf.bo.XMLTree(
                        "mpanCore"))).put("source")).put("organization"), doc))
    currentDate = net.sf.chellow.monad.vf.bo.MonadDate()
    if inv.hasParameter("finish-date-year"):
        yearMonad = inv.getMonadInteger("finish-date-year")
        year = yearMonad.getInteger()
    else:
        year = currentDate.getYear()
    source.setAttribute("finish-date-year", str(year))
    if inv.hasParameter("finish-date-month"):
        monthMonad = inv.getMonadInteger("finish-date-month")
        month = monthMonad.getInteger()
    else:
        month = currentDate.getMonth()
    if inv.hasParameter("months"):
        months = inv.getMonadInteger("months")
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
else:
    raise UserException.newInvalidParameter()