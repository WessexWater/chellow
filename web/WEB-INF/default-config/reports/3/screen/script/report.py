from net.sf.chellow.monad import Hiber, UserException, XmlTree
from net.sf.chellow.monad.types import MonadDate

supplyId = inv.getLong("supply-id")
if not inv.isValid():
    raise UserException()
supply = Hiber.session().createQuery("select supply from Supply supply join supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and supply.id = :supplyId").setEntity("organization", organization).setLong("supplyId", supplyId).uniqueResult() 
source.appendChild(supply.toXml(doc, XmlTree("source").put("generations", XmlTree("mpans", XmlTree("mpanCore").put("mpanTop", XmlTree("mtc").put("pc").put("llfc", XmlTree("voltageLevel"))).put("supplierAccount", XmlTree('contract')).put('hhdcAccount', XmlTree("contract", XmlTree("provider"))))).put("mpanCores")))
source.appendChild(MonadDate().toXml(doc))
source.appendChild(organization.toXml(doc))