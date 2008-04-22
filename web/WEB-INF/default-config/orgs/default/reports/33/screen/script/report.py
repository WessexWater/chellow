from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import DsoService

service_id = inv.getLong('dso-service-id')
service = DsoService.getDsoService(service_id)
service_element = service.getXML(XmlTree('provider'), doc)
source.appendChild(service_element)
for rate_script in service.getRateScripts():
    service_element.appendChild(rate_script.toXML(doc))
source.appendChild(organization.toXML(doc))