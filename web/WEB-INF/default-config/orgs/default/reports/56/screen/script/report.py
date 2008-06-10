from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import Dce

dce_id = inv.getLong('dce-id')
dce = organization.getDce(dce_id)
services_element = doc.createElement('services')
source.appendChild(services_element)
for service in Hiber.session().createQuery("from DceService service where service.provider.id = :dceId order by service.startRateScript.startDate.date").setLong("dceId", dce.getId()).list():
    service_element = service.toXML(doc)
    services_element.appendChild(service_element)
    start_rate_script = service.getStartRateScript()
    start_rate_script.setLabel('start')
    service_element.appendChild(start_rate_script.toXML(doc))
    finish_rate_script = service.getFinishRateScript()
    finish_rate_script.setLabel('finish')
    service_element.appendChild(finish_rate_script.toXML(doc))
services_element.appendChild(dce.toXML(doc));
source.appendChild(organization.toXML(doc))