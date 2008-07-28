from net.sf.chellow.monad import Hiber, XmlTree

pcs_element = doc.createElement('pcs')
source.appendChild(pcs_element)
for pc in Hiber.session().createQuery("from Pc pc order by pc.code").list():
    pcs_element.appendChild(pc.toXml(doc))
source.appendChild(organization.toXml(doc))

