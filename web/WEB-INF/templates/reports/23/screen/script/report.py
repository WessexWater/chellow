from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import Provider
from net.sf.chellow.physical import MarketRole

provider_id = inv.getLong('provider-id')
provider = Provider.getProvider(provider_id)
provider_element = provider.toXml(doc, XmlTree('participant').put('role'))
source.appendChild(provider_element)
if provider.getRole().getCode() == MarketRole.DISTRIBUTOR:
    services = Hiber.session().createQuery("from DsoService service where service.provider = :provider order by service.name").setEntity('provider', provider).list()
else:
    services = Hiber.session().createQuery("from Contract contract where contract.organization = :organization and contract.provider = :provider order by contract.name").setEntity('organization', organization).setEntity('provider', provider).list()
for service in services:
    provider_element.appendChild(service.toXml(doc))
source.appendChild(organization.toXml(doc))

