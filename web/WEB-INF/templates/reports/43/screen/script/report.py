from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import Bill

bill_id = inv.getLong('bill-id')
bill = Bill.getBill(bill_id)
if not bill.getAccount().getContract().getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such an account doesn't exist in this organization")
bill_element = bill.toXml(doc, XmlTree('account', XmlTree('contract', XmlTree('provider').put('organization'))))
source.appendChild(bill_element)
for invoice in Hiber.session().createQuery("from Invoice invoice where invoice.bill = :bill order by invoice.startDate.date").setEntity('bill', bill).list():
    bill_element.appendChild(invoice.toXml(doc, XmlTree('batch', XmlTree('contract'))))