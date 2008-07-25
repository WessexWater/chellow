from net.sf.chellow.monad import Hiber
from net.sf.chellow.billing import Provider

provider_id = inv.getLong('provider-id')
provider = Provider.getProvider(provider_id)
provider_element = provider.toXml(doc, XmlTree('participant').put('marketRole'))
source.appendChild(provider_element)
for service in Hiber.session("from Service service where service.provider = :provider and service. order by service.)
source.appendChild(organization.toXml(doc))

