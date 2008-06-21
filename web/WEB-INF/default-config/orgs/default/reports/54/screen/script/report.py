from net.sf.chellow.monad import Hiber, XmlTree

dces_element = doc.createElement('dces')
source.appendChild(dces_element)
for dce in Hiber.session().createQuery("from Dce dce where dce.organization = :organization order by dce.name").setEntity('organization', organization).list():
    dces_element.appendChild(dce.toXml(doc))
source.appendChild(organization.toXml(doc))