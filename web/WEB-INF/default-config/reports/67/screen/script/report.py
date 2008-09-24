from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import MeterPaymentType

type_id = inv.getLong('type-id')
type = MeterPaymentType.getMeterPaymentType(type_id)
source.appendChild(type.toXml(doc))
source.appendChild(organization.toXml(doc))