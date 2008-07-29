from net.sf.chellow.monad import Hiber, XmlTree

sscs_element = doc.createElement('sscs')
source.appendChild(sscs_element)
for ssc in Hiber.session().createQuery("from Ssc ssc order by ssc.code").list():
    sscs_element.appendChild(ssc.toXml(doc, XmlTree("measurementRequirements", XmlTree("tpr"))))
source.appendChild(organization.toXml(doc))