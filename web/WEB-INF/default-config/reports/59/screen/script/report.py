from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.physical import SiteSnag

snag_id = inv.getLong('snag-id')
snag = SiteSnag.getSiteSnag(snag_id)
if not snag.getContract().getOrganization().equals(organization):
    raise UserException("Such an HHDC contract doesn't exist in this organization")
source.appendChild(snag.toXml(doc, XmlTree("contract", XmlTree(
                        "provider").put("organization")).put("site")))