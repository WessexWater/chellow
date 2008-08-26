from net.sf.chellow.monad import Hiber, XmlTree
from net.sf.chellow.billing import SupplierContract

id = inv.getLong('supplier-contract-id')
contract = organization.getSupplierContract(id)
accounts_element = doc.createElement('accounts')
source.appendChild(accounts_element)
accounts_element.appendChild(contract.toXml(doc, XmlTree('organization')))
for account in Hiber.session().createQuery("from Account account where account.contract = :contract order by account.reference").setEntity('contract', contract).list():
    account_element = account.toXml(doc)
    accounts_element.appendChild(account_element)