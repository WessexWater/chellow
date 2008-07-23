from net.sf.chellow.monad import Hiber
from net.sf.chellow.physical import Provider

provider_id = inv.getLong('provider-id')
provider = Provider.getProvider(provider_id)
source.appendChild(provider.toXml(doc, XmlTree('participant').put('marketRole')));
source.appendChild(organization.toXml(doc))

