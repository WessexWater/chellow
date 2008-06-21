from net.sf.chellow.monad import Hiber, UserException, XmlTree
from java.util import Calendar, GregorianCalendar, TimeZone, Locale, Date
from net.sf.chellow.monad.types import MonadDate
from java.sql import Timestamp, ResultSet
from java.text import SimpleDateFormat
from net.sf.chellow.physical import HhEndDate, HhDatumStatus

cal = GregorianCalendar(TimeZone.getTimeZone("GMT"), Locale.UK)
supplyId = inv.getLong("supply-id")
startDateYear = inv.getInteger("start-year")
startDateMonth = inv.getInteger("start-month")
if not inv.isValid():
    raise UserException.newInvalidParameter()

cal.clear()
cal.set(Calendar.YEAR, startDateYear)
cal.set(Calendar.MONTH, startDateMonth - 1)
cal.set(Calendar.DAY_OF_MONTH, 1)
startDate = cal.getTime()
cal.add(Calendar.MONTH, 1)
finishDate = cal.getTime()
dateFormat = SimpleDateFormat("yyyy-MM-dd' 'HH:mm'Z'")
dateFormat.setCalendar(cal)
supply = Hiber.session().createQuery("select supply from Supply supply join supply.generations generation join generation.siteSupplyGenerations siteSupplyGeneration where siteSupplyGeneration.site.organization = :organization and supply.id = :supplyId").setEntity("organization", organization).setLong("supplyId", supplyId).uniqueResult()
supplyElement = supply.toXml(XmlTree("generationLast", XmlTree("mpans", XmlTree("mpanCore"))).put("source"), doc)
source.appendChild(supplyElement)
source.appendChild(MonadDate.getMonthsXml(doc))
source.appendChild(MonadDate.getDaysXml(doc))
con = Hiber.session().connection()
stmt = con.prepareStatement("select hh_datum.value, hh_datum.end_date, hh_datum.status, channel.is_import, channel.is_kwh from hh_datum hh_datum, channel channel where hh_datum.channel_id = channel.id and channel.supply_id = ? and hh_datum.end_date > ? and hh_datum.end_date <= ? order by hh_datum.end_date", ResultSet.TYPE_FORWARD_ONLY, ResultSet.CONCUR_READ_ONLY, ResultSet.CLOSE_CURSORS_AT_COMMIT)
stmt.setInt(1, supply.getId())
stmt.setTimestamp(2, Timestamp(startDate.getTime()))
stmt.setTimestamp(3, Timestamp(finishDate.getTime()))
stmt.setFetchSize(100)
rs = stmt.executeQuery()
hhDate = HhEndDate(startDate).getNext().getDate().getTime()
actualStatus = HhDatumStatus.ACTUAL
if rs.next():
    value = rs.getFloat("value")
    hhChannelEndDate = rs.getTimestamp("end_date")
    isImport = rs.getBoolean("is_import")
    isKwh = rs.getBoolean("is_kwh")
    status = rs.getString("status")
    finishDateMillis = finishDate.getTime()
    cal = MonadDate.getCalendar()
    while hhDate <= finishDateMillis:
        datumElement = doc.createElement("datum")
        supplyElement.appendChild(datumElement)
        datumElement.setAttribute("timestamp", dateFormat.format(Date(hhDate)))
        while hhChannelEndDate != None and hhChannelEndDate.getTime() == hhDate:
            if isImport:
                if isKwh:
                    datumElement.setAttribute("import-kwh-value", str(round(value, 2)))
                    datumElement.setAttribute("import-kwh-status", status)
                else:
                    datumElement.setAttribute("import-kvarh-value", str(round(value, 2)))
                    datumElement.setAttribute("import-kvarh-status", status)
            else:
                if isKwh:
                    datumElement.setAttribute("export-kwh-value", str(round(value, 2)))
                    datumElement.setAttribute("export-kwh-status", status)
                else:
                    datumElement.setAttribute("export-kvarh-value", str(round(value, 2)))
                    datumElement.setAttribute("export-kvarh-status", status)
            if rs.next():
                value = rs.getFloat("value")
                hhChannelEndDate = rs.getTimestamp("end_date")
                isImport = rs.getBoolean("is_import")
                isKwh = rs.getBoolean("is_kwh")
                status = rs.getString("status")
            else:
                hhChannelEndDate = None

        hhDate = HhEndDate.getNext(cal, hhDate)
rs.close()