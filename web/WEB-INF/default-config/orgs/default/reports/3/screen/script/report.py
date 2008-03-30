from net.sf.chellow.monad import Hiber, UserException, XmlTree
from net.sf.chellow.monad.types import MonadDate

supplyId = inv.getLong("supply-id")
if not inv.isValid():
    raise UserException.newInvalidParameter()
supply = Hiber.session().createQuery("select supply from Supply supply join supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and supply.id = :supplyId").setEntity("organization", organization).setLong("supplyId", supplyId).uniqueResult() 
source.appendChild(supply.getXML(XmlTree("source").put("generations", XmlTree("mpans", XmlTree("mpanCore").put("mpanTop", XmlTree("meterTimeswitch").put("profileClass").put("lineLossFactor", XmlTree("voltageLevel"))).put("supplierAccount").put("dceService", XmlTree("provider")))).put("mpanCores"), doc))
source.appendChild(MonadDate().toXML(doc))