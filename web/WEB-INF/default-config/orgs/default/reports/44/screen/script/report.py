from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import SupplierContract

contract_id = inv.getLong('contract-id')
contract = SupplierContract.getSupplierContract(contract_id)
if not contract.getOrganization().equals(organization):
    raise UserException("Such a supplier contract doesn't exist in this organization")
batches_element = doc.createElement('batches')
source.appendChild(batches_element)
batches_element.appendChild(contract.toXml(doc, XmlTree('provider').put('organization')))
source.appendChild(batches_element)
for batch in Hiber.session().createQuery("from Batch batch where batch.contract = :contract order by batch.reference").setEntity("contract", contract).list():
    batches_element.appendChild(batch.toXml(doc))