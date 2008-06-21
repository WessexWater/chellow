from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import SupplierService

service_id = inv.getLong('service-id')
service = SupplierService.getSupplierService(service_id)
if not service.getProvider().getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such a supplier service doesn't exist in this organization")
bill_snags_element = doc.createElement('bill-snags')
source.appendChild(bill_snags_element)
bill_snags_element.appendChild(service.toXml(XmlTree('provider', XmlTree('organization')), doc))
source.appendChild(bill_snags_element)
for bill_snag in Hiber.session().createQuery("from BillSnag snag where snag.dateResolved is null and snag.service = :service order by snag.bill.id, snag.description").setEntity("service", service).list():
    bill_snags_element.appendChild(bill_snag.toXml(XmlTree('bill'), doc))