from net.sf.chellow.monad import Hiber, UserException, XmlTree
from net.sf.chellow.monad.types import MonadDate

supply_generation_id = inv.getLong("supply-generation-id")
if not inv.isValid():
    raise UserException.newInvalidParameter()
supply_generation = Hiber.session().createQuery("select generation from SupplyGeneration generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and generation.id = :supplyGenerationId").setEntity("organization", organization).setLong("supplyGenerationId", supply_generation_id).uniqueResult()
source.appendChild(supply_generation.getXML(XmlTree("mpans", XmlTree("mpanCore").put('mpanTop', XmlTree("meterTimeswitch").put('llf', XmlTree('voltageLevel')).put('profileClass')).put('dceService', XmlTree("provider")).put('supplierService', XmlTree("provider")).put('supplierAccount')).put('supply', XmlTree('source').put('organization')).put('siteSupplyGenerations', XmlTree('site')), doc))
source.appendChild(MonadDate().toXML(doc))
source.appendChild(organization.toXML(doc))