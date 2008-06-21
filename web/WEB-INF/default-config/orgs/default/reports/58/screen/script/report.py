from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.physical import ChannelSnag

snag_id = inv.getLong('snag-id')
snag = ChannelSnag.getChannelSnag(snag_id)
if not snag.getService().getProvider().getOrganization().equals(organization):
    raise UserException("Such a DCE service doesn't exist in this organization")
source.appendChild(snag.toXml(doc, XmlTree("service", XmlTree(
                        "provider", XmlTree("organization"))).put("channel",
                        XmlTree("supply"))))