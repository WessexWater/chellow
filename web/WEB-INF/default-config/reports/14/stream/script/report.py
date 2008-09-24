from java.util import GregorianCalendar, TimeZone, Locale, Calendar, Date
from net.sf.chellow.monad import Hiber, UserException
from org.hibernate import CacheMode, ScrollMode
from java.text import DateFormat
from net.sf.chellow.physical import HhEndDate
from java.sql import ResultSet, Timestamp

TYPES = ['used', 'generated', 'exported', 'displaced', 'parasitic', 'imported']
siteId = inv.getLong("site-id")
year = inv.getInteger("year")
type = inv.getString("type")
if not inv.isValid():
    raise UserException.newInvalidParameter()
if not type in TYPES:
    raise UserException.newInvalidParameter('The type must be one of ' + str(TYPES))
site = organization.getSite(siteId)
cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
cal.set(Calendar.MILLISECOND, 0)
cal.set(Calendar.SECOND, 0)
cal.set(Calendar.MINUTE, 30)
cal.set(Calendar.HOUR_OF_DAY, 0)
cal.set(Calendar.DAY_OF_MONTH, 1)
cal.set(Calendar.MONTH, Calendar.JANUARY)
cal.set(Calendar.YEAR, year)
startDate = cal.getTime()
cal.add(Calendar.MINUTE, -30)
cal.add(Calendar.YEAR, 1)
finishDate = cal.getTime()
inv.getResponse().setContentType("text/csv")
pw = inv.getResponse().getWriter()
pw.print("Site Code,Type,Date,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48")
dateFormat = DateFormat.getDateInstance(DateFormat.LONG, Locale.UK)
dateFormat.applyLocalizedPattern("yyyy-MM-dd")

con = Hiber.session().connection()
supplies = Hiber.session().createQuery("select distinct supply from Supply supply join supply.generations supplyGeneration join supplyGeneration.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site = :site and supply.source.code != 'sub'").setEntity('site', site).list()
suppliesSQL = ''
for supply in supplies:
    suppliesSQL = suppliesSQL + str(supply.getId()) + ','
stmt = con.prepareStatement("select hh_datum.value, hh_datum.end_date, hh_datum.status, channel.is_import, supply.name, source.code from hh_datum, channel, supply_generation, supply, source where hh_datum.channel_id = channel.id and channel.supply_generation_id = supply_generation.id and supply_generation.supply_id = supply.id and supply.source_id = source.id and channel.is_kwh is true and hh_datum.end_date >= ? and hh_datum.end_date <= ? and supply.id in (" + suppliesSQL[:-1] + ") order by hh_datum.end_date", ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY, ResultSet.CLOSE_CURSORS_AT_COMMIT)
stmt.setTimestamp(1, Timestamp(startDate.getTime()))
stmt.setTimestamp(2, Timestamp(finishDate.getTime()))
stmt.setFetchSize(100)
rs = stmt.executeQuery()
hhDate = startDate.getTime()
siteSnagQuery = Hiber.session().createQuery("select count(*) from SiteSnag snag where snag.site = :site and snag.startDate.date <= :finishDate and snag.finishDate.date >= :startDate and (snag.dateResolved is null or (snag.dateResolved is not null and snag.isIgnored is true))").setEntity("site", site)
if rs.next():
    hhChannelKwh = rs.getFloat("value")
    hhChannelEndDate = rs.getTimestamp("end_date")
    isImport = rs.getBoolean("is_import")
    status = rs.getString("status")
    sourceCode = rs.getString("code")
    supplyName = rs.getString("name")
    finishDateMillis = finishDate.getTime()
    startDateMillis = startDate.getTime()
    while hhDate <= finishDateMillis:
        exportedKwh = 0
        importedKwh = 0
        parasiticKwh = 0
        generatedKwh = 0
        displacedKwh = 0
        while hhChannelEndDate != None and hhChannelEndDate.getTime() == hhDate:
            if not isImport and sourceCode == "net":
                exportedKwh = exportedKwh + hhChannelKwh
            if isImport and sourceCode == "net":
                importedKwh = importedKwh + hhChannelKwh
            if isImport and (sourceCode == "lm" or sourceCode == "chp" or sourceCode == "turb"):
                generatedKwh = generatedKwh + hhChannelKwh
            if not isImport and (sourceCode == "lm" or sourceCode == "chp" or sourceCode == "turb"):
                parasiticKwh = parasiticKwh + hhChannelKwh
            if rs.next():
                sourceCode = rs.getString("code")
                supplyName = rs.getString("name")
                hhChannelKwh = rs.getFloat("value")
                hhChannelEndDate = rs.getTimestamp("end_date")
                isImport = rs.getBoolean("is_import")
                status = rs.getString("status")
            else:
                hhChannelEndDate = None
        displacedKwh = generatedKwh - exportedKwh - parasiticKwh
        usedKwh = importedKwh + displacedKwh
        '''
        if siteSnagQuery.setTimestamp("startDate", startDate).setTimestamp("finishDate", monthFinishDate).uniqueResult() > 0:
            monthElement.setAttribute("has-site-snags", "true")
        '''
        cal.clear()
        cal.setTimeInMillis(hhDate)
        if cal.get(Calendar.HOUR_OF_DAY) == 0 and cal.get(Calendar.MINUTE) == 30:
            pw.print('\r\n' + site.getCode().toString() + ',' + type + ',' + dateFormat.format(Date(hhDate)))
            pw.flush()
        pw.print(",")
        if type == 'used':
            hh_value = usedKwh
        elif type == 'imported':
            hh_value = importedKwh
        elif type == 'exported':
            hh_value = exportedKwh
        elif type == 'parasitic':
            hh_value = parasiticKwh
        elif type == 'displaced':
            hh_value = displacedKwh
        pw.print(str(round(hh_value, 1)))
        hhDate = HhEndDate.getNext(cal, hhDate)
        Hiber.session().clear()
pw.close()