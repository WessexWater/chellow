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
stmt.executeUpdate("create type channel_type as enum ('ACTIVE', 'REACTIVE_IMP', 'REACTIVE_EXP')")
stmt.executeUpdate("alter table channel add column channel_type channel_type")
stmt.executeUpdate("ALTER TABLE channel ADD COLUMN imp_related boolean")
stmt.executeUpdate("alter table channel add constraint channel_era_id_imp_related_channel_type_key unique (era_id, imp_related, channel_type)")

con.commit()

stmt.executeUpdate("begin isolation level serializable read write")
pstmt = con.prepareStatement("select * from channel")
rs = pstmt.executeQuery()
while rs.next():
    channel_id = rs.getLong('id')
    is_import = rs.getBoolean('is_import')
    is_kwh = rs.getBoolean('is_kwh')
    if is_kwh:
        channel_type = 'ACTIVE'
        imp_related = is_import
    else:
        imp_related = True
        channel_type = 'REACTIVE_IMP' if is_import else 'REACTIVE_EXP'    

    pstmt = con.prepareStatement("update channel set imp_related = ?, channel_type = cast(? as channel_type) where id = ?")
    pstmt.setBoolean(1, imp_related)
    pstmt.setString(2, channel_type)
    pstmt.setLong(3, channel_id)
    pstmt.execute()
rs.close()
con.commit()

stmt.executeUpdate("begin isolation level serializable read write")
stmt.executeUpdate("alter table channel alter column imp_related set not null")
stmt.executeUpdate("alter table channel alter column channel_type set not null")

con.commit()