from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Dso

pcs_element = doc.createElement('pcs')
source.appendChild(pcs_element)
for pc in Hiber.session().createQuery("from ProfileClass pc order by pc.code").list():
    pcs_element.appendChild(pc.toXML(doc))
source.appendChild(organization.toXML(doc))

