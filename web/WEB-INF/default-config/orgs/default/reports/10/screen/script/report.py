import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import net.sf.chellow.monad.vf.bo
import org.w3c.dom
import java.util
import java.text
import calendar
import math

inv.getResponse().setContentType("image/svg+xml")

siteId = inv.getMonadLong("site-id")
finishDateYear = inv.getMonadInteger("finish-date-year")
finishDateMonth = inv.getMonadInteger("finish-date-month")
months = inv.getMonadInteger("months")
if not inv.isValid():
    raise net.sf.chellow.monad.ui.UserException.newInvalidParameter()
cal = java.util.GregorianCalendar(java.util.TimeZone.getTimeZone("GMT"), java.util.Locale.UK)
cal.clear()
cal.set(java.util.Calendar.YEAR, finishDateYear.getInteger())
cal.set(java.util.Calendar.MONTH, finishDateMonth.getInteger())
cal.set(java.util.Calendar.DAY_OF_MONTH, 1)
finishDate = cal.getTime()
cal.add(java.util.Calendar.MONTH, -1 * months.getInteger())
startDate = cal.getTime()
monthDateFormat = java.text.SimpleDateFormat("MMMM")
cal.setTime(finishDate)
cal.add(java.util.Calendar.DAY_OF_MONTH, -1)
source.setAttribute("finish-date-month-text", monthDateFormat.format(cal.getTime()))
site = organization.getSite(siteId)
data = net.sf.chellow.persistant08.Hiber.session().createQuery("select datum, datum.channel.isImport.boolean from HhDatum datum join datum.channel.supply.siteSupplies siteSupply where siteSupply.site = :site and datum.channel.isKwh.boolean is true and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate and datum.channel.supply.source.code.string != 'sub' order by datum.endDate.date").setEntity("site", site).setTimestamp("startDate", startDate).setTimestamp("finishDate", finishDate).list()
siteElement = site.toXML(doc)
source.appendChild(siteElement)
source.appendChild(inv.requestXml(doc))
hhDate = net.sf.chellow.persistant08.HhEndDate(startDate)
dataPosition = 0
dataSize = data.size()
maxScale = 0
minScale = 0
if not data.isEmpty():
    dataRow = data.get(dataPosition)
    hhDatum = dataRow[0]
    while not hhDate.getDate().after(finishDate):
        complete = "blank"
        hhValue = 0
        hhElement = doc.createElement("hh")
        siteElement.appendChild(hhElement)
        while dataPosition < dataSize and hhDatum.getEndDate().getDate().getTime() == hhDate.getDate().getTime():
            if dataRow[1]:
                hhValue = hhValue + hhDatum.getValue().getFloat()
            else:
                hhValue = hhValue - hhDatum.getValue().getFloat()
            if hhDatum.getStatus().getCharacter() == net.sf.chellow.persistant08.HhDatumStatus.ACTUAL.getCharacter():
                if complete == "blank":
                    complete = "actual"
            else:
                complete = "not-actual"
            dataPosition = dataPosition + 1
            if dataPosition < dataSize:
                dataRow = data.get(dataPosition)
                hhDatum = dataRow[0]
        yearText = hhDate.getYear()
        monthText = hhDate.getMonth()
        dayText = hhDate.getDay()
        hhElement.setAttribute("value", str(int(hhValue)))
        hhElement.setAttribute("year", yearText)
        hhElement.setAttribute("month", monthText)
        hhElement.setAttribute("day", dayText)
        if hhDate.getHour() == "00" and hhDate.getMinute() == "00":
            if hhDate.getDay() == "15":
                hhElement.setAttribute("month-text", monthDateFormat.format(hhDate.getDate()))
            hhElement.setAttribute("day-of-week", str(calendar.weekday(int(yearText), int(monthText), int(dayText))))
        hhElement.setAttribute("hour", hhDate.getHour())
        hhElement.setAttribute("minute", hhDate.getMinute())
        if complete != "actual":
            hhElement.setAttribute("incomplete", "true")
        hhDate = hhDate.getNext()
        maxScale = max(maxScale, hhValue)
        minScale = min(minScale, hhValue)
    maxScale = int(maxScale)
    minScale = min(int(minScale), 0)
    siteElement.setAttribute("max-scale", str(maxScale))
    siteElement.setAttribute("min-scale", str(minScale))
    step = 10**int(math.floor(math.log10(maxScale - minScale)))
    scaleElement = doc.createElement("scale")
    source.appendChild(scaleElement)
    for i in range(0, minScale, -1 * step):
        scalePointElement = doc.createElement("scale-point")
        scaleElement.appendChild(scalePointElement)
        scalePointElement.setAttribute("value", str(i))
    for i in range(0, maxScale, step):
        scalePointElement = doc.createElement("scale-point")
        scaleElement.appendChild(scalePointElement)
        scalePointElement.setAttribute("value", str(i))