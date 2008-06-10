from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import DceService

service_id = inv.getLong('service-id')
service = DceService.getDceService(service_id)
if not service.getProvider().getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such a DCE service doesn't exist in this organization")
service_element = service.getXML(XmlTree('provider'), doc)
source.appendChild(service_element)
for rate_script in service.getRateScripts():
    service_element.appendChild(rate_script.toXML(doc))
source.appendChild(organization.toXML(doc))