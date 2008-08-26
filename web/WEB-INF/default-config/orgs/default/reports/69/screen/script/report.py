from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import Dso

dso_id = inv.getLong('dso-id')
dso = Dso.getDso(dso_id)
dso_element = dso.toXml(doc, XmlTree('participant').put('role'))
source.appendChild(dso_element)
for service in Hiber.session().createQuery("from DsoService service where service.dso = :dso order by service.name").setEntity('dso', dso).list():
    dso_element.appendChild(service.toXml(doc, XmlTree('rateScripts')))
source.appendChild(organization.toXml(doc))

