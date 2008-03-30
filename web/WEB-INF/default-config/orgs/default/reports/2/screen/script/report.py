from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.monad.types import MonadDate
from java.util import GregorianCalendar, Calendar, TimeZone, Locale, Date

siteId = inv.getLong("site-id")
if not inv.isValid():
    raise UserException.newInvalidParameter()
site = organization.getSite(siteId)
site_element = site.getXML(XmlTree('organization'), doc)
source.appendChild(site_element)
last_supply = None
last_supply_generation = None
supply_element = None
for supply_generation in Hiber.session().createQuery("select siteSupplyGeneration.supplyGeneration from SiteSupplyGeneration siteSupplyGeneration where siteSupplyGeneration.site = :site order by siteSupplyGeneration.supplyGeneration.supply.id, siteSupplyGeneration.supplyGeneration.finishDate.date desc").setEntity('site', site).list():
    supply = supply_generation.getSupply()
    if not supply.equals(last_supply) or not supply_generation.getFinishDate().getNext().equals(last_supply_generation.getStartDate()):
        supply_element = supply.getXML(XmlTree('source'), doc)
        site_element.appendChild(supply_element)
    supply_element.appendChild(supply_generation.getXML(XmlTree("mpans", XmlTree("mpanCore")), doc))
    last_supply = supply
    last_supply_generation = supply_generation
cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
cal.add(Calendar.DAY_OF_MONTH, -1)
yesterday = MonadDate(cal.getTime())
yesterday.setLabel('yesterday')
source.appendChild(yesterday.toXML(doc))