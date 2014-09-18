from java.text import DecimalFormat
from java.lang import Runtime, System, Thread
from java.io import StringWriter, InputStreamReader
from net.sf.chellow.monad import Hiber, Monad, MonadMessage
from java.lang.management import OperatingSystemMXBean, ManagementFactory
from com.jezhumble.javasysmon import JavaSysMon
from net.sf.chellow.ui import ContextListener
from net.sf.chellow.billing import Contract


con = Hiber.session().connection()
stmt = con.createStatement()

con.setAutoCommit(False)

stmt.executeUpdate("begin isolation level serializable read write")
stmt.executeUpdate("alter table channel drop constraint channel_era_id_is_import_is_kwh_key")
stmt.executeUpdate("alter table channel drop column is_kwh")
stmt.executeUpdate("alter table channel drop column is_import")

con.commit()