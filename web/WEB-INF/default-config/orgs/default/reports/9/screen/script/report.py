import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import calendar
import java.util
import net.sf.chellow.data08

supplyId = inv.getMonadLong("supply-id")
supply = net.sf.chellow.persistant08.Hiber.session().load(java.lang.Class.forName("net.sf.chellow.persistant08.Supply"), java.lang.Long(supplyId.getLong()))
source.appendChild(supply.toXml(net.sf.chellow.monad.vf.bo.XMLTree("siteSupplies",
                net.sf.chellow.monad.vf.bo.XMLTree("site")),doc))
isImport = inv.getMonadBoolean("is-import");
isImport = isImport.getBoolean()
if not supply.getOrganization().equals(organization):
    raise net.sf.chellow.monad.ui.ProgrammerException("Supply does not belong to this organization.")
kwhChannel = supply.getChannel(net.sf.chellow.persistant08.IsImport(isImport),net.sf.chellow.persistant08.IsKwh("true")) 
kvarhChannel = supply.getChannel(net.sf.chellow.persistant08.IsImport(isImport),net.sf.chellow.persistant08.IsKwh("false"))
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
    
    monthElement = doc.createElement("month")
    source.appendChild(monthElement)
    generation = supply.getGeneration(monthFinish)
    if generation != None:
        mpan = generation.getMpan(net.sf.chellow.persistant08.IsImport(isImport))
        if mpan != None:
            monthElement.setAttribute("mpan-core", mpan.getMpanCore().toString())
            monthElement.setAttribute("agreed-supply-capacity", str(mpan.getAgreedSupplyCapacity()))
    kwhDatumAtMd = net.sf.chellow.persistant08.Hiber.session().createQuery("from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate and datum.value.float = (select max(datum.value.float) from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate) order by datum.endDate.date").setEntity("channel", kwhChannel).setTimestamp("startDate", monthStart.getDate()).setTimestamp("finishDate", monthFinish.getDate()).uniqueResult()
    if kwhDatumAtMd != None:
        mdKwh = kwhDatumAtMd.getValue().getFloat()
        monthElement.setAttribute("md-kw", str(round(mdKwh * 2)))
        kvarhDatumAtMd = net.sf.chellow.persistant08.Hiber.session().createQuery("from HhDatum datum where datum.channel = :channel and datum.endDate.date = :mdDate").setEntity("channel", kvarhChannel).setTimestamp("mdDate", kwhDatumAtMd.getEndDate().getDate()).uniqueResult()
        if kvarhDatumAtMd != None:
            kvarhAtMd = kvarhDatumAtMd.getValue().getFloat()
            kvahAtMd = (mdKwh ** 2 + kvarhAtMd ** 2) ** 0.5
            pf = mdKwh / kvahAtMd
            monthElement.setAttribute("pf", str(round(pf, 4)))
            monthElement.setAttribute("kva-at-md", str(round(kvahAtMd * 2)))
    totalKwh = net.sf.chellow.persistant08.Hiber.session().createQuery("select sum(datum.value.float) from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate").setEntity("channel", kwhChannel).setTimestamp("startDate", monthStart.getDate()).setTimestamp("finishDate", monthFinish.getDate()).uniqueResult()
    if totalKwh != None:
        monthElement.setAttribute("total-kwh", str(round(totalKwh)))
    monthElement.setAttribute("date", monthStart.getYear() + "-" + monthStart.getMonth() + "-" + monthStart.getDay())
    monthFinish = nextMonthFinish