from net.sf.chellow.monad import Hiber, XmlTree

types_element = doc.createElement('read-types')
source.appendChild(types_element)
for type in Hiber.session().createQuery("from ReadType type order by type.code").list():
    types_element.appendChild(type.toXml(doc))