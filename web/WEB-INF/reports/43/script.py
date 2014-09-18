from net.sf.chellow.monad import Hiber, XmlTree

groups_element = doc.createElement('gsp-groups')
source.appendChild(groups_element)
for group in Hiber.session().createQuery("from GspGroup group order by group.code").list():
    groups_element.appendChild(group.toXml(doc))