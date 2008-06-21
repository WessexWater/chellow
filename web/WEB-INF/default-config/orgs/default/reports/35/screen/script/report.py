from net.sf.chellow.monad import Hiber, XmlTree

suppliers_element = doc.createElement('suppliers')
source.appendChild(suppliers_element)
for supplier in Hiber.session().createQuery("from Supplier supplier where supplier.organization = :organization order by supplier.name").setEntity('organization', organization).list():
    suppliers_element.appendChild(supplier.toXml(doc))
source.appendChild(organization.toXml(doc))