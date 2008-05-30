from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import SupplierService

service_id = inv.getLong('supplier-service-id')
service = SupplierService.getSupplierService(service_id)
if not service.getProvider().getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such a supplier service doesn't exist in this organization")
account_snags_element = doc.createElement('account-snags')
source.appendChild(account_snags_element)
account_snags_element.appendChild(service.getXML(XmlTree('provider', XmlTree('organization')), doc))
source.appendChild(account_snags_element)
for account_snag in Hiber.session().createQuery("from AccountSnag snag where snag.dateResolved is null and snag.service = :service order by snag.account.reference, snag.description, snag.startDate.date").setEntity("service", service).list():
    account_snags_element.appendChild(account_snag.getXML(XmlTree('account'), doc))