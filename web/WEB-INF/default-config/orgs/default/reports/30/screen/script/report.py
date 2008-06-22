from net.sf.chellow.monad import Hiber, XmlTree

mtcs_element = doc.createElement('mtcs')
source.appendChild(mtcs_element)
for mt in Hiber.session().createQuery("select mt from MeterTimeswitch mt left outer join mt.dso dso order by mt.code, dso.code").list():
    mtcs_element.appendChild(mt.toXml(doc, XmlTree('dso')))
source.appendChild(organization.toXml(doc))

