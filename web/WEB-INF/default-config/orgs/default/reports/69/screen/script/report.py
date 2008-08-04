from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import Dso

dso_id = inv.getLong('dso-id')
dso = Dso.getDso(dso_id)
dso_element = dso.toXml(doc, XmlTree('participant').put('role'))
source.appendChild(dso_element)
for service in Hiber.session().createQuery("from DsoService service where service.provider = :provider order by service.name").setEntity('provider', provider).list():
    dso_element.appendChild(service.toXml(doc))
source.appendChild(organization.toXml(doc))

