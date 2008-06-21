from net.sf.chellow.monad import Hiber, XmlTree

tprs_element = doc.createElement('tprs')
source.appendChild(tprs_element)
for tpr in Hiber.session().createQuery("from Tpr tpr order by tpr.code").list():
    tprs_element.appendChild(tpr.toXml(doc))
source.appendChild(organization.toXml(doc))