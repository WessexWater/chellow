from net.sf.chellow.monad import Hiber, XmlTree

roles_element = doc.createElement('roles')
source.appendChild(roles_element)
for role in Hiber.session().createQuery("from MarketRole role order by role.code").list():
    roles_element.appendChild(role.toXml(doc))
roles_element.appendChild(organization.toXml(doc))