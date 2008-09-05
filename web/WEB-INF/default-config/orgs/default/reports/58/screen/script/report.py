from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.physical import ChannelSnag

snag_id = inv.getLong('snag-id')
snag = ChannelSnag.getChannelSnag(snag_id)
if not snag.getContract().getOrganization().equals(organization):
    raise UserException("Such a HHDC contract doesn't exist in this organization")
source.appendChild(snag.toXml(doc, XmlTree("contract", XmlTree("organization")).put("channel",
                        XmlTree("supplyGeneration", XmlTree('supply')))))