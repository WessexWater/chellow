from net.sf.chellow.monad.data import Hiber
from net.sf.chellow.monad.ui import UserException
from net.sf.chellow.monad.vf.bo import XMLTree, MonadDate
from java.util import GregorianCalendar, Calendar, TimeZone, Locale, Date

dceServiceId = inv.getLong("dce-service-id")
if not inv.isValid():
    raise UserException.newInvalidParameter()
dceService = Hiber.session().createQuery("from DceService service where service.provider.organization = :organization and service.id = :serviceId").setEntity('organization', organization).setLong('serviceId', dceServiceId).uniqueResult()
source.appendChild(dceService.getXML(XMLTree('provider', XMLTree('organization')), doc))