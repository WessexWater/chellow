from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import HhdcContract

contract_id = inv.getLong('hhdc-contract-id')
contract = organization.getHhdcContract(contract_id)
source.appendChild(contract.toXml(doc, XmlTree('provider', XmlTree('participant')).put('rateScripts').put('organization')))