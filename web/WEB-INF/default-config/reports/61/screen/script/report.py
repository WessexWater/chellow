from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import MarketRole

role_id = inv.getLong('role-id')
role = MarketRole.getMarketRole(role_id)
role_element = role.toXml(doc)
source.appendChild(role_element)
for party in Hiber.session().createQuery("from Party party where party.role = :role order by party.participant.code").setEntity("role", role).list():
    role_element.appendChild(party.toXml(doc, XmlTree('participant')))
source.appendChild(organization.toXml(doc))