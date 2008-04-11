from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.physical import MpanTop

mpan_top_id = inv.getLong('mpan-top-id')
mpan_top = MpanTop.getMpanTop(mpan_top_id)
source.appendChild(mpan_top.getXML(XmlTree('profileClass').put('llf', XmlTree('dso')).put('meterTimeswitch'), doc))
source.appendChild(organization.toXML(doc))