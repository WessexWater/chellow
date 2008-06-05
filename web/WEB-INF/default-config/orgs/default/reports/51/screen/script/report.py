from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import AccountSnag

snag_id = inv.getLong('snag-id')
snag = AccountSnag.getAccountSnag(snag_id)
if not snag.getService().getProvider().getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such a snag doesn't exist in this organization")
source.appendChild(snag.getXML(XmlTree('service', XmlTree('provider', XmlTree('organization'))).put('account'), doc))