from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import Supplier

supplier_id = inv.getLong('supplier-id')
supplier = organization.getSupplier(supplier_id)
services_element = doc.createElement('services')
source.appendChild(services_element)
for service in Hiber.session().createQuery("from SupplierService service where service.provider.id = :supplierId order by service.startRateScript.startDate.date").setLong("supplierId", supplier.getId()).list():
    service_element = service.toXml(doc)
    services_element.appendChild(service_element)
    start_rate_script = service.getStartRateScript()
    start_rate_script.setLabel('start')
    service_element.appendChild(start_rate_script.toXml(doc))
    finish_rate_script = service.getFinishRateScript()
    finish_rate_script.setLabel('finish')
    service_element.appendChild(finish_rate_script.toXml(doc))
services_element.appendChild(supplier.toXml(doc));
source.appendChild(organization.toXml(doc))