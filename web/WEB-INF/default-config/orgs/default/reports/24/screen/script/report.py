from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import Dso

dso_id = inv.getLong('dso-id')
dso = Dso.getDso(dso_id)
llfcs_element = doc.createElement('llfcs')
source.appendChild(llfcs_element)
for llfc in Hiber.session().createQuery("from Llfc llfc where llfc.dso = :dso order by llfc.code").setEntity("dso", dso).list():
    llfcs_element.appendChild(llfc.toXml(doc, XmlTree("voltageLevel")))
llfcs_element.appendChild(dso.toXml(doc));
source.appendChild(organization.toXml(doc))