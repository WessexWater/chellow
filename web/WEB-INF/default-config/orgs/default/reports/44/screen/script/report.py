from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import SupplierService

service_id = inv.getLong('supplier-service-id')
service = SupplierService.getSupplierService(service_id)
if not service.getProvider().getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such a supplier service doesn't exist in this organization")
batches_element = doc.createElement('batches')
source.appendChild(batches_element)
batches_element.appendChild(service.toXml(doc, XmlTree('provider', XmlTree('organization'))))
source.appendChild(batches_element)
for batch in Hiber.session().createQuery("from Batch batch where batch.service = :service order by batch.reference").setEntity("service", service).list():
    batches_element.appendChild(batch.toXml(doc))