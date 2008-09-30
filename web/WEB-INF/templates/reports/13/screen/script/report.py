from net.sf.chellow.monad import UserException, XmlTree
from net.sf.chellow.monad.types import MonadDate

siteId = inv.getLong("site-id")
if not inv.isValid():
  raise UserException()
site = organization.getSite(siteId)
source.appendChild(site.toXml(doc, XmlTree('organization')))
source.appendChild(MonadDate.getMonthsXml(doc))
source.appendChild(MonadDate.getDaysXml(doc))
source.appendChild(MonadDate().toXml(doc))