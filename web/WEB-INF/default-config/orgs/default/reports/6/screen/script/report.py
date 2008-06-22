from net.sf.chellow.monad import Hiber, UserException, XmlTree
from java.lang import System
from net.sf.chellow.monad.types import MonadDate
import math
from java.sql import Timestamp, ResultSet
from java.util import GregorianCalendar, Calendar, TimeZone, Locale, Date
from net.sf.chellow.physical import HhEndDate

siteId = inv.getLong("site-id")
cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
if inv.hasParameter("finish-date-year"):
    year = inv.getInteger("finish-date-year")
    cal.set(Calendar.YEAR, year)
if inv.hasParameter("finish-date-month"):
    month = inv.getInteger("finish-date-month")
    cal.set(Calendar.MONTH, month)
for i in range(12):
    month_element = doc.createElement("month-in-year")
    source.appendChild(month_element)
    month_element.setAttribute('value', '%02d' % (i + 1))
#source.appendChild(inv.requestXml(doc))
if not inv.isValid():
    raise UserException()

cal.set(Calendar.DAY_OF_MONTH, 1)
cal.set(Calendar.HOUR_OF_DAY, 0)
cal.set(Calendar.MINUTE, 0)
cal.set(Calendar.SECOND, 0)
cal.set(Calendar.MILLISECOND, 0)
finishDate = HhEndDate(cal.getTime()).getDate()
cal.add(Calendar.MONTH, -1)
source.setAttribute("finish-date-year", str(cal.get(Calendar.YEAR)))
source.setAttribute("finish-date-month", str(cal.get(Calendar.MONTH) + 1))
cal.add(Calendar.MONTH, -11)
cal.add(Calendar.MINUTE, 30)
startDate = HhEndDate(cal.getTime()).getDate()
site = organization.getSite(siteId)
source.appendChild(site.toXml(doc, XmlTree('organization')))
supplies = Hiber.session().createQuery("select distinct supply from Supply supply join supply.generations supplyGeneration join supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site = :site and supply.source.code != 'sub'").setEntity('site', site).list()
suppliesSQL = ''
for supply in supplies:
    suppliesSQL = suppliesSQL + str(supply.getId()) + ','
con = Hiber.session().connection()
stmt = con.prepareStatement("select hh_datum.value, hh_datum.end_date, hh_datum.status, channel.is_import, supply.name, source.code from hh_datum, channel, supply, source where hh_datum.channel_id = channel.id and channel.supply_id = supply.id and supply.source_id = source.id and channel.is_kwh is true and hh_datum.end_date >= ? and hh_datum.end_date <= ? and supply.id in (" + suppliesSQL[:-1] + ") order by hh_datum.end_date desc", ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY, ResultSet.CLOSE_CURSORS_AT_COMMIT)
stmt.setTimestamp(1, Timestamp(startDate.getTime()))
stmt.setTimestamp(2, Timestamp(finishDate.getTime()))
stmt.setFetchSize(100)
rs = stmt.executeQuery()
hhDate = finishDate.getTime()
maxExportedKw = 0
maxExportedKwDate = None
maxExportedKwYear = 0
maxExportedKwYearDate = None
exportedKwhMonth = 0
exportedKwhYear = 0
exportedKwh = 0
maxImportedKw = 0
maxImportedKwDate = None
maxImportedKwYear = 0
maxImportedKwYearDate = None
importedKwhMonth = 0
importedKwhYear = 0
importedKwh = 0
maxGeneratedKw = 0
maxGeneratedKwDate = None
maxGeneratedKwYear = 0
maxGeneratedKwYearDate = None
generatedKwhMonth = 0
generatedKwhYear = 0
generatedKwh = 0
maxParasiticKw = 0
maxParasiticKwDate = None
maxParasiticKwYear = 0
maxParasiticKwYearDate = None
parasiticKwhMonth = 0
parasiticKwhYear = 0
parasiticKwh = 0
maxDisplacedKw = 0
maxDisplacedKwDate = None
maxDisplacedKwYear = 0
maxDisplacedKwYearDate = None
displacedKwhMonth = 0
displacedKwhYear = 0
displacedKwh = 0
maxUsedKw = 0
maxUsedKwDate = None
maxUsedKwYear = 0
maxUsedKwYearDate = None
usedKwhMonth = 0
usedKwhYear = 0
usedKwh = 0

siteSnagQuery = Hiber.session().createQuery("select count(*) from SiteSnag snag where snag.site = :site and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and (snag.dateResolved is null or (snag.dateResolved is not null and snag.isIgnored is true))").setEntity("site", site)

if rs.next():
    #raise net.sf.chellow.monad.ui.UserException.newInvalidParameter("got to rs next")
    hhChannelKw = rs.getFloat("value") * 2
    hhChannelEndDate = rs.getTimestamp("end_date")
    isImport = rs.getBoolean("is_import")
    status = rs.getString("status")
    sourceCode = rs.getString("code")
    supplyName = rs.getString("name")
    finishDateMillis = finishDate.getTime()
    startDateMillis = startDate.getTime()
    cal.clear()
    cal.setTime(hhChannelEndDate)
    previousMonth = cal.get(Calendar.MONTH)
    #cal = net.sf.chellow.monad.vf.bo.MonadDate.getCalendar()
    while hhDate >= startDateMillis:
        exportedKw = 0
        importedKw = 0
        parasiticKw = 0
        generatedKw = 0
        while hhChannelEndDate != None and hhChannelEndDate.getTime() == hhDate:
            if not isImport and sourceCode == "net":
                exportedKw = exportedKw + hhChannelKw
            if isImport and sourceCode == "net":
                importedKw = importedKw + hhChannelKw
            if isImport and (sourceCode == "lm" or sourceCode == "chp" or sourceCode == "turb"):
                generatedKw = generatedKw + hhChannelKw
            if not isImport and (sourceCode == "lm" or sourceCode == "chp" or sourceCode == "turb"):
                parasiticKw = parasiticKw + hhChannelKw
            if rs.next():
                sourceCode = rs.getString("code")
                supplyName = rs.getString("name")
                hhChannelKw = rs.getFloat("value") * 2
                hhChannelEndDate = rs.getTimestamp("end_date")
                isImport = rs.getBoolean("is_import")
                status = rs.getString("status")
                cal.clear()
                cal.setTime(hhChannelEndDate)
                month = cal.get(Calendar.MONTH)
            else:
                hhChannelEndDate = None
        if exportedKw > maxExportedKw:
            maxExportedKw = exportedKw
            maxExportedKwDate = hhDate
        if importedKw > maxImportedKw:
            maxImportedKw = importedKw
            maxImportedKwDate = hhDate
        if generatedKw > maxGeneratedKw:
            maxGeneratedKw = generatedKw
            maxGeneratedKwDate = hhDate
        if parasiticKw > maxParasiticKw:
            maxParasiticKw = parasiticKw
            maxParasiticKwDate = hhDate
        displacedKw = generatedKw - parasiticKw - exportedKw
        if displacedKw > maxDisplacedKw:
            maxDisplacedKw = displacedKw
            maxDisplacedKwDate = hhDate
        usedKw = importedKw + displacedKw
        if usedKw > maxUsedKw:
            maxUsedKw = usedKw
            maxUsedKwDate = hhDate
        exportedKwhMonth = exportedKwhMonth + exportedKw / 2
        importedKwhMonth = importedKwhMonth + importedKw / 2
        generatedKwhMonth = generatedKwhMonth + generatedKw / 2
        parasiticKwhMonth = parasiticKwhMonth + parasiticKw / 2
        displacedKwhMonth = displacedKwhMonth + displacedKw / 2
        usedKwhMonth = usedKwhMonth + usedKw / 2
        cal.clear()
        cal.setTimeInMillis(hhDate)
        hhDate = HhEndDate.getPrevious(cal, hhDate)
        cal.clear()
        cal.setTimeInMillis(hhDate)
        if cal.get(Calendar.DAY_OF_MONTH) == 1 and cal.get(Calendar.HOUR_OF_DAY) == 0 and cal.get(Calendar.MINUTE) == 0:
            monthElement = doc.createElement("month")
            source.appendChild(monthElement)
            cal.add(Calendar.MINUTE, 30)
            monthStartDate = cal.getTime()
            cal.add(Calendar.MONTH, 1)
            cal.add(Calendar.MINUTE, -30)
            monthFinishDate = cal.getTime()
            if siteSnagQuery.setTimestamp("startDate", monthStartDate).setTimestamp("finishDate", monthFinishDate).uniqueResult() > 0:
                monthElement.setAttribute("has-site-snags", "true")
            monthStartMonadDate = HhEndDate(monthStartDate)
            monthStartMonadDate.setLabel("start")
            monthElement.appendChild(monthStartMonadDate.toXml(doc))
            monthFinishMonadDate = HhEndDate(monthFinishDate)
            monthFinishMonadDate.setLabel("finish")
            monthElement.appendChild(monthFinishMonadDate.toXml(doc))
            monthElement.setAttribute("max-exported-kw", str(int(round(maxExportedKw))))
            if maxExportedKwDate != None:
                monthElement.setAttribute("max-exported-kw-date", MonadDate(Date(maxExportedKwDate)).toString())
            monthElement.setAttribute("exported-kwh", str(int(round(exportedKwhMonth))))
            monthElement.setAttribute("max-imported-kw", str(int(round(maxImportedKw))))
            if maxImportedKwDate != None:
                monthElement.setAttribute("max-imported-kw-date", MonadDate(Date(maxImportedKwDate)).toString())
            monthElement.setAttribute("imported-kwh", str(int(round(importedKwhMonth))))
            monthElement.setAttribute("max-generated-kw", str(int(round(maxGeneratedKw))))
            if maxGeneratedKwDate != None:
                monthElement.setAttribute("max-generated-kw-date", MonadDate(Date(maxGeneratedKwDate)).toString())
            monthElement.setAttribute("generated-kwh", str(int(round(generatedKwhMonth))))
            monthElement.setAttribute("max-parasitic-kw", str(int(round(maxParasiticKw))))
            if maxParasiticKwDate != None:
                monthElement.setAttribute("max-parasitic-kw-date", MonadDate(Date(maxParasiticKwDate)).toString())
            monthElement.setAttribute("parasitic-kwh", str(int(round(parasiticKwhMonth))))
            monthElement.setAttribute("max-displaced-kw", str(int(round(maxDisplacedKw))))
            if maxDisplacedKwDate != None:
                monthElement.setAttribute("max-displaced-kw-date", MonadDate(Date(maxDisplacedKwDate)).toString())
            monthElement.setAttribute("displaced-kwh", str(int(round(displacedKwhMonth))))
            monthElement.setAttribute("max-used-kw", str(int(round(maxUsedKw))))
            if maxUsedKwDate != None:
                monthElement.setAttribute("max-used-kw-date", MonadDate(Date(maxUsedKwDate)).toString())
            monthElement.setAttribute("used-kwh", str(int(round(usedKwhMonth))))
            if maxExportedKw > maxExportedKwYear:
                maxExportedKwYear = maxExportedKw
                maxExportedKwYearDate = maxExportedKwDate
            maxExportedKw = 0
            maxExportedKwDate = None
            exportedKwhYear = exportedKwhYear + exportedKwhMonth
            exportedKwhMonth = 0
            if maxImportedKw > maxImportedKwYear:
                maxImportedKwYear = maxImportedKw
                maxImportedKwYearDate = maxImportedKwDate
            maxImportedKw = 0
            maxImportedKwDate = None
            importedKwhYear = importedKwhYear + importedKwhMonth
            importedKwhMonth = 0
            if maxGeneratedKw > maxGeneratedKwYear:
                maxGeneratedKwYear = maxGeneratedKw
                maxGeneratedKwYearDate = maxGeneratedKwDate
            maxGeneratedKw = 0
            maxGeneratedKwDate = None
            generatedKwhYear = generatedKwhYear + generatedKwhMonth
            generatedKwhMonth = 0
            if maxParasiticKw > maxParasiticKwYear:
                maxParasiticKwYear = maxParasiticKw
                maxParasiticKwYearDate = maxParasiticKwDate
            maxParasiticKw = 0
            maxParasiticKwDate = None
            parasiticKwhYear = parasiticKwhYear + parasiticKwhMonth
            parasiticKwhMonth = 0
            if maxDisplacedKw > maxDisplacedKwYear:
                maxDisplacedKwYear = maxDisplacedKw
                maxDisplacedKwYearDate = maxDisplacedKwDate
            maxDisplacedKw = 0
            maxDisplacedKwDate = None
            displacedKwhYear = displacedKwhYear + displacedKwhMonth
            displacedKwhMonth = 0
            if maxUsedKw > maxUsedKwYear:
                maxUsedKwYear = maxUsedKw
                maxUsedKwYearDate = maxUsedKwDate
            maxUsedKw = 0
            maxUsedKwDate = None
            usedKwhYear = usedKwhYear + usedKwhMonth
            usedKwhMonth = 0
    source.setAttribute("max-exported-kw", str(int(round(maxExportedKwYear))))
    if maxExportedKwYearDate != None:
        source.setAttribute("max-exported-kw-date", MonadDate(Date(maxExportedKwYearDate)).toString())
    source.setAttribute("exported-kwh", str(int(round(exportedKwhYear))))
    source.setAttribute("max-imported-kw", str(int(round(maxImportedKwYear))))
    if maxImportedKwYearDate != None:
        source.setAttribute("max-imported-kw-date", MonadDate(Date(maxImportedKwYearDate)).toString())
    source.setAttribute("imported-kwh", str(int(round(importedKwhYear))))
    source.setAttribute("max-generated-kw", str(int(round(maxGeneratedKwYear))))
    if maxGeneratedKwYearDate != None:
        source.setAttribute("max-generated-kw-date", MonadDate(Date(maxGeneratedKwYearDate)).toString())
    source.setAttribute("generated-kwh", str(int(round(generatedKwhYear))))
    source.setAttribute("max-parasitic-kw", str(int(round(maxParasiticKwYear))))
    if maxParasiticKwYearDate != None:
        source.setAttribute("max-parasitic-kw-date", MonadDate(Date(maxParasiticKwYearDate)).toString())
    source.setAttribute("parasitic-kwh", str(int(round(parasiticKwhYear))))
    source.setAttribute("max-displaced-kw", str(int(round(maxDisplacedKwYear))))
    if maxDisplacedKwYearDate != None:
        source.setAttribute("max-displaced-kw-date", MonadDate(Date(maxDisplacedKwYearDate)).toString())
    source.setAttribute("displaced-kwh", str(int(round(displacedKwhYear))))
    source.setAttribute("max-used-kw", str(int(round(maxUsedKwYear))))
    if maxUsedKwYearDate != None:
        source.setAttribute("max-used-kw-date", MonadDate(Date(maxUsedKwYearDate)).toString())
    source.setAttribute("used-kwh", str(int(round(usedKwhYear))))