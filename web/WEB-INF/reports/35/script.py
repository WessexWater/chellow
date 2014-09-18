from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import GspGroup

group_id = inv.getLong('gsp-group-id')
group = GspGroup.getGspGroup(group_id)
source.appendChild(group.toXml(doc))