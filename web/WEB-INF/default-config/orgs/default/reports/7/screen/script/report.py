from net.sf.chellow.monad import Hiber, XmlTree
from java.util import Calendar
import java.util
from net.sf.chellow.physical import HhEndDate, IsImport

supplyId = inv.getLong("supply-id")
supply = Hiber.session().createQuery("select supply from Supply supply join supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and supply.id = :supplyId").setEntity("organization", organization).setLong("supplyId", supplyId).uniqueResult()
source.appendChild(supply.toXML(doc))
isImport = inv.getBoolean("is-import");
kwhChannel = supply.getChannel(isImport, True) 
kvarhChannel = supply.getChannel(isImport, False)
cal = java.util.GregorianCalendar(java.util.TimeZone.getTimeZone("GMT"), java.util.Locale.UK)
cal.set(Calendar.DAY_OF_MONTH, 1)
cal.set(Calendar.HOUR_OF_DAY, 0)
cal.set(Calendar.MINUTE, 0)
cal.set(Calendar.SECOND, 0)
cal.set(Calendar.MILLISECOND, 0)
monthFinish = HhEndDate(cal.getTime())
nextMonthFinish = None
for i in range(60):
    cal.add(Calendar.MONTH, -1)
    nextMonthFinish = HhEndDate(cal.getTime())
    monthStart = nextMonthFinish.getNext()
    
    monthElement = doc.createElement("month")
    source.appendChild(monthElement)
    generation = supply.getGeneration(monthFinish)
    if generation != None:
        mpan = generation.getMpan(IsImport(isImport))
        if mpan != None:
            monthElement.setAttribute("mpan-core", mpan.getMpanCore().toString())
            monthElement.setAttribute("agreed-supply-capacity", str(mpan.getAgreedSupplyCapacity()))
    kwhDatumAtMd = Hiber.session().createQuery("from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate and datum.value = (select max(datum.value) from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate) order by datum.endDate.date").setEntity("channel", kwhChannel).setTimestamp("startDate", monthStart.getDate()).setTimestamp("finishDate", monthFinish.getDate()).setMaxResults(1).uniqueResult()
    if kwhDatumAtMd != None:
        mdKwh = kwhDatumAtMd.getValue()
        monthElement.setAttribute("md-kw", str(round(mdKwh * 2)))
        kvarhDatumAtMd = Hiber.session().createQuery("from HhDatum datum where datum.channel = :channel and datum.endDate.date = :mdDate").setEntity("channel", kvarhChannel).setTimestamp("mdDate", kwhDatumAtMd.getEndDate().getDate()).uniqueResult()
        if kvarhDatumAtMd != None:
            kvarhAtMd = kvarhDatumAtMd.getValue()
            kvahAtMd = (mdKwh ** 2 + kvarhAtMd ** 2) ** 0.5
            if kvahAtMd > 0:
                pf = mdKwh / kvahAtMd
                monthElement.setAttribute("pf", str(round(pf, 4)))
            monthElement.setAttribute("kva-at-md", str(round(kvahAtMd * 2)))
    totalKwh = Hiber.session().createQuery("select sum(datum.value) from HhDatum datum where datum.channel = :channel and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate").setEntity("channel", kwhChannel).setTimestamp("startDate", monthStart.getDate()).setTimestamp("finishDate", monthFinish.getDate()).uniqueResult()
    if totalKwh != None:
        monthElement.setAttribute("total-kwh", str(round(totalKwh)))
    monthElement.setAttribute("date", monthStart.toString())
    monthFinish = nextMonthFinish