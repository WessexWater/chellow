from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import SupplierContract

contract_id = inv.getLong('contract-id')
contract = SupplierContract.getSupplierContract(contract_id)
if not contract.getOrganization().equals(organization):
    raise UserException("Such a supplier contract doesn't exist in this organization")
bill_snags_element = doc.createElement('bill-snags')
source.appendChild(bill_snags_element)
bill_snags_element.appendChild(contract.toXml(doc, XmlTree('provider').put('organization')))
source.appendChild(bill_snags_element)
for bill_snag in Hiber.session().createQuery("from BillSnag snag where snag.dateResolved is null and snag.contract = :contract order by snag.bill.id, snag.description").setEntity('contract', contract).list():
    bill_snags_element.appendChild(bill_snag.toXml(doc, XmlTree('bill')))