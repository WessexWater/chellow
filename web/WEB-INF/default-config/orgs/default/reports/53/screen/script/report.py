from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import BillSnag

snag_id = inv.getLong('snag-id')
snag = BillSnag.getBillSnag(snag_id)
if not snag.getContract().getOrganization().equals(organization):
    raise UserException("Such a snag doesn't exist in this organization")
source.appendChild(snag.toXml(doc, XmlTree('contract', XmlTree('provider').put('organization')).put('bill', XmlTree('account'))))