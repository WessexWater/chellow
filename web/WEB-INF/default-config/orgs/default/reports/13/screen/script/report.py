from net.sf.chellow.monad import UserException
from net.sf.chellow.monad.types import MonadDate

siteId = inv.getLong("site-id")
if not inv.isValid():
  raise UserException.newInvalidParameter()
site = organization.getSite(siteId)
source.appendChild(site.toXML(doc))
source.appendChild(MonadDate.getMonthsXml(doc))
source.appendChild(MonadDate.getDaysXml(doc))
source.appendChild(MonadDate().toXML(doc))