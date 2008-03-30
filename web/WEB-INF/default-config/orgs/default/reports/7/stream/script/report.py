import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import calendar
import java.util
import net.sf.chellow.data08

supplyId = inv.getMonadLong("supply-id")
supply = net.sf.chellow.persistant08.Hiber.session().load(java.lang.Class.forName("net.sf.chellow.persistant08.Supply"), java.lang.Long(supplyId.getLong()))
isImport = inv.getMonadBoolean("is-import");
isImport = isImport.getBoolean()
if not supply.getOrganization().equals(organization):
    raise net.sf.chellow.monad.ui.ProgrammerException("Supply does not belong to this organization.")
kwhChannel = supply.getChannel(net.sf.chellow.persistant08.IsImport(isImport),net.sf.chellow.persistant08.IsKwh("true")) 
kvarhChannel = supply.getChannel(net.sf.chellow.persistant08.IsImport(isImport),net.sf.chellow.persistant08.IsKwh("false"))
inv.getResponse().setContentType("text/csv")
pw = inv.getResponse().getWriter()
pw.println("Month Starting, MPAN Core,MD / kW,Power Factor,MD / kVA,Agreed Supply Capacity (kVA),kWh")
cal = java.util.GregorianCalendar(java.util.TimeZone.getTimeZone("GMT"), java.util.Locale.UK)
cal.set(java.util.Calendar.DAY_OF_MONTH, 1)
cal.set(java.util.Calendar.HOUR_OF_DAY, 0)
cal.set(java.util.Calendar.MINUTE, 0)
cal.set(java.util.Calendar.SECOND, 0)
cal.set(java.util.Calendar.MILLISECOND, 0)
monthFinish = net.sf.chellow.persistant08.HhEndDate(cal.getTime())
nextMonthFinish = None
for i in range(60):
    cal.add(java.util.Calendar.MONTH, -1)
    nextMonthFinish = net.sf.chellow.persistant08.HhEndDate(cal.getTime())
    monthStart = nextMonthFinish.getNext()
    
    generation = supply.getGeneration(monthFinish)
    if generation == None:
        mpanCoreStr = ""
    else:
        mpan = generation.getMpan(net.sf.chellow.persistant08.IsImport(isImport))
        if mpan == None:
            mpanCoreStr = "NA"
            agreedSupplyCapacityStr = "NA"
        else:
            mpanCoreStr = mpan.getMpanCore().toString()
            agreedSupplyCapacityStr = str(mpan.getAgreedSupplyCapacity())
    kwhDatumAtMd = net.sf.chellow.persistant08.Hiber.session().createQuery("from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate and datum.value.float = (select max(datum.value.float) from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate) order by datum.endDate.date").setEntity("channel", kwhChannel).setTimestamp("startDate", monthStart.getDate()).setTimestamp("finishDate", monthFinish.getDate()).uniqueResult()
    if kwhDatumAtMd == None:
        mdKwStr = "NA"
        pfStr = "NA"
        kvaAtMdStr = "NA"
    else:
        mdKwh = kwhDatumAtMd.getValue().getFloat()
        mdKwStr = str(round(mdKwh * 2))
        kvarhDatumAtMd = net.sf.chellow.persistant08.Hiber.session().createQuery("from HhDatum datum where datum.channel = :channel and datum.endDate.date = :mdDate").setEntity("channel", kvarhChannel).setTimestamp("mdDate", kwhDatumAtMd.getEndDate().getDate()).uniqueResult()
        if kvarhDatumAtMd == None:
            pfStr = "NA"
            kvaAtMdStr = "NA"
        else:
            kvarhAtMd = kvarhDatumAtMd.getValue().getFloat()
            kvahAtMd = (mdKwh ** 2 + kvarhAtMd ** 2) ** 0.5
            pf = mdKwh / kvahAtMd
            pfStr = str(round(pf, 4))
            kvaAtMdStr = str(round(kvahAtMd * 2))
    totalKwh = net.sf.chellow.persistant08.Hiber.session().createQuery("select sum(datum.value.float) from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate").setEntity("channel", kwhChannel).setTimestamp("startDate", monthStart.getDate()).setTimestamp("finishDate", monthFinish.getDate()).uniqueResult()
    if totalKwh == None:
        totalKwhStr = "NA"
    else:
        totalKwhStr = str(round(totalKwh))
    pw.println(monthStart.getYear() + "-" + monthStart.getMonth() + "-" + monthStart.getDay() + "," + mpanCoreStr + "," + mdKwStr + "," + pfStr + "," + kvaAtMdStr + "," + agreedSupplyCapacityStr + "," + totalKwhStr)
    pw.flush()
    monthFinish = nextMonthFinish
pw.close()