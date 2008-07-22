from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import HhdcContract

contract_id = inv.getLong('contract-id')
contract = HhdcContract.getHhdcContract(contract_id)
if not contract.getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such an HHDC contract doesn't exist in this organization")
source.appendChild(contract.toXml(doc, XmlTree('provider', XmlTree('participant')).put('rateScripts').put('organization')))
source.appendChild(contract.getProvider().toXml(doc))
