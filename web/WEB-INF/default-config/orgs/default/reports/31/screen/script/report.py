from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import Mtc

mtc_id = inv.getLong('mtc-id')
mtc = Mtc.getMtc(mtc_id)
source.appendChild(mtc.toXml(doc, XmlTree('meterType').put('paymentType')))
source.appendChild(organization.toXml(doc))