from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import MeterTimeswitch

mt_id = inv.getLong('mt-id')
mt = MeterTimeswitch.getMeterTimeswitch(mt_id)
source.appendChild(mt.toXml(doc))
source.appendChild(organization.toXml(doc))