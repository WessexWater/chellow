from net.sf.chellow.monad import Hiber
from net.sf.chellow.billing import Dce

dce_id = inv.getLong('dce-id')
dce = organization.getDce(dce_id)
source.appendChild(dce.toXML(doc));
source.appendChild(organization.toXML(doc))