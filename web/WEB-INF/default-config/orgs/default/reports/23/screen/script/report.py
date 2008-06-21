from net.sf.chellow.monad import Hiber
from net.sf.chellow.physical import Dso

dso_id = inv.getLong('dso-id')
dso = Dso.getDso(dso_id)
source.appendChild(dso.toXml(doc));
source.appendChild(organization.toXml(doc))

