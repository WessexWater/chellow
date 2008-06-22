from net.sf.chellow.monad import Hiber, XmlTree, UserException
from net.sf.chellow.billing import Invoice

invoice_id = inv.getLong('invoice-id')
invoice = Invoice.getInvoice(invoice_id)
if not invoice.getBatch().getService().getProvider().getOrganization().equals(organization):
    raise UserException.newInvalidParameter("Such an invoice doesn't exist in this organization")
invoice_element = invoice.toXml(doc, XmlTree('batch', XmlTree('service', XmlTree('provider', XmlTree('organization')))).put('bill', XmlTree('account', XmlTree('provider', XmlTree('organization')))))
source.appendChild(invoice_element)
for register_read in Hiber.session().createQuery("from RegisterRead read where read.invoice = :invoice order by read.units.int, read.tpr.code").setEntity('invoice', invoice).list():
    invoice_element.appendChild(register_read.toXml(doc, XmlTree('mpan', XmlTree('supplyGeneration').put('mpanCore')).put('tpr')));