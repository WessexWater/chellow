from net.sf.chellow.monad import Hiber
from net.sf.chellow.billing import Supplier

supplier_id = inv.getLong('supplier-id')
supplier = organization.getSupplier(supplier_id)
source.appendChild(supplier.toXML(doc));
source.appendChild(organization.toXML(doc))

