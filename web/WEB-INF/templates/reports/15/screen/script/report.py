from net.sf.chellow.monad import Hiber, UserException, XmlTree
from net.sf.chellow.monad.types import MonadDate

supply_generation_id = inv.getLong("supply-generation-id")
if not inv.isValid():
    raise UserException()
supply_generation = Hiber.session().createQuery("select generation from SupplyGeneration generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and generation.id = :supplyGenerationId").setEntity("organization", organization).setLong("supplyGenerationId", supply_generation_id).uniqueResult()
source.appendChild(supply_generation.toXml(doc, XmlTree("mpans", XmlTree("mpanCore").put('mpanTop', XmlTree("mtc").put('llfc', XmlTree('voltageLevel')).put('pc')).put('hhdcAccount', XmlTree('contract', XmlTree("provider"))).put('supplierAccount', XmlTree('contract', XmlTree("provider")))).put('supply', XmlTree('source').put('organization')).put('siteSupplyGenerations', XmlTree('site'))))
source.appendChild(MonadDate().toXml(doc))
source.appendChild(organization.toXml(doc))