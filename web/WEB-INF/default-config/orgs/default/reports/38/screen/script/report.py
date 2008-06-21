from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import SupplierService

service_id = inv.getLong('supplier-service-id')
service = SupplierService.getSupplierService(service_id)
if not service.getProvider().getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such a supplier service doesn't exist in this organization")
service_element = service.toXml(XmlTree('provider'), doc)
source.appendChild(service_element)
for rate_script in service.getRateScripts():
    service_element.appendChild(rate_script.toXml(doc))
source.appendChild(organization.toXml(doc))