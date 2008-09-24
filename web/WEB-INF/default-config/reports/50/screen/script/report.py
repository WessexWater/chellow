from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import SupplierContract

contract_id = inv.getLong('contract-id')
contract = SupplierContract.getSupplierContract(contract_id)
if not contract.getOrganization().equals(organization):
    raise UserException("Such a supplier contract doesn't exist in this organization")
account_snags_element = doc.createElement('account-snags')
source.appendChild(account_snags_element)
account_snags_element.appendChild(contract.toXml(doc, XmlTree('provider').put('organization')))
source.appendChild(account_snags_element)
for account_snag in Hiber.session().createQuery("from AccountSnag snag where snag.dateResolved is null and snag.contract = :contract order by snag.account.reference, snag.description, snag.startDate.date").setEntity('contract', contract).list():
    account_snags_element.appendChild(account_snag.toXml(doc, XmlTree('account')))