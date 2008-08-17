from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import SupplierContract

contract_id = inv.getLong('contract-id')
contract = SupplierContract.getSupplierContract(contract_id)
if not contract.getOrganization().equals(organization):
    raise UserException("Such a supplier contract doesn't exist in this organization")
contract_element = contract.toXml(doc, XmlTree('provider').put('organization'))
source.appendChild(contract_element)
for rate_script in contract.getRateScripts():
    contract_element.appendChild(rate_script.toXml(doc))