from net.sf.chellow.monad import Hiber, XmlTree

mtcs_element = doc.createElement('mtcs')
source.appendChild(mtcs_element)
for mt in Hiber.session().createQuery("select mtc from Mtc mtc left outer join mtc.dso dso order by mtc.code, dso.dsoCode").list():
    mtcs_element.appendChild(mt.toXml(doc, XmlTree('dso')))
source.appendChild(organization.toXml(doc))

