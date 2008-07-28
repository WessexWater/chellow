from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Pc

pc_id = inv.getLong('pc-id')
pc = Pc.getPc(pc_id)
source.appendChild(pc.toXml(doc))
source.appendChild(organization.toXml(doc))