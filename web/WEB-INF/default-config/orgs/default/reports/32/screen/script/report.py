from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Dso

dso_id = inv.getLong('dso-id')
dso = Dso.getDso(dso_id)
services_element = doc.createElement('services')
source.appendChild(services_element)
for service in Hiber.session().createQuery("from DsoService service where service.provider.id = :dsoId order by service.startRateScript.startDate.date").setLong("dsoId", dso.getId()).list():
    services_element.appendChild(service.toXML(doc))
services_element.appendChild(dso.toXML(doc));
source.appendChild(organization.toXML(doc))