from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Dso

dso_id = inv.getLong('dso-id')
dso = Dso.getDso(dso_id)
llfs_element = doc.createElement('llfs')
source.appendChild(llfs_element)
for llf in Hiber.session().createQuery("from Llf llf where llf.dso = :dso order by llf.code").setEntity("dso", dso).list():
    llfs_element.appendChild(llf.toXml(XmlTree("voltageLevel"), doc))
llfs_element.appendChild(dso.toXml(doc));
source.appendChild(organization.toXml(doc))

