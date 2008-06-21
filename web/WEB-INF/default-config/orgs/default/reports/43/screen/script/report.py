from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import Bill

bill_id = inv.getLong('bill-id')
bill = Bill.getBill(bill_id)
if not bill.getAccount().getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such an account doesn't exist in this organization")
bill_element = bill.toXml(XmlTree('account', XmlTree('provider', XmlTree('organization'))), doc)
source.appendChild(bill_element)
for invoice in Hiber.session().createQuery("from Invoice invoice where invoice.bill = :bill order by invoice.startDate.date").setEntity('bill', bill).list():
    bill_element.appendChild(invoice.toXml(XmlTree('batch', XmlTree('service')), doc))