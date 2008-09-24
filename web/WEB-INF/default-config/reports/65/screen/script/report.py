from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import MeterType

type_id = inv.getLong('type-id')
type = MeterType.getMeterType(type_id)
source.appendChild(type.toXml(doc))
source.appendChild(organization.toXml(doc))