import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import calendar
import java.util
import net.sf.chellow.data08

cal = java.util.GregorianCalendar(java.util.TimeZone.getTimeZone("GMT"), java.util.Locale.UK)
cal.set(java.util.Calendar.MILLISECOND, 0)
cal.set(java.util.Calendar.SECOND, 0)
cal.set(java.util.Calendar.MINUTE, 0)
cal.set(java.util.Calendar.HOUR_OF_DAY, 0)
cal.set(java.util.Calendar.DAY_OF_MONTH, 1)
finishDate = cal.getTime()
cal.add(java.util.Calendar.MILLISECOND, 1)
cal.add(java.util.Calendar.YEAR, -1)
startDate = cal.getTime()
inv.getResponse().setContentType("text/csv")
pw = inv.getResponse().getWriter()
pw.print("MPAN Core,Date,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48")
dateFormat = java.text.DateFormat.getDateInstance(java.text.DateFormat.LONG, java.util.Locale.UK)
dateFormat.applyLocalizedPattern("yyyy-MM-dd")

channels = net.sf.chellow.persistant08.Hiber.session().createQuery("from Channel channel join channel.supply.generations generation where (generation.finishDate.date is null or generation.finishDate.date > :finishDate) and channel.supply.source.code.string = 'net' and channel.isImport.boolean is true and channel.isKwh.boolean is true and channel.supply.id = 33").setTimestamp("finishDate", finishDate).setCacheMode(org.hibernate.CacheMode.IGNORE).scroll(org.hibernate.ScrollMode.FORWARD_ONLY)

while channels.next():
    channel = channels.get(0)
    generation = channel.getSupply().getGeneration(net.sf.chellow.persistant08.HhEndDate(finishDate))
    if generation == None:
        mpanCoreStr = "NA"
    else:
        mpanCoreStr = generation.getImportMpan().getMpanCore().toString()
    pw.flush()
    #net.sf.chellow.persistant08.Hiber.session().clear()
    currentDate = net.sf.chellow.persistant08.HhEndDate.roundUp(startDate)
    hhData = net.sf.chellow.persistant08.Hiber.session().createQuery("select datum.value.float, datum.endDate.date from HhDatum datum where datum.channel = :channel and datum.endDate.date > :startDate and datum.endDate.date <= :finishDate order by datum.endDate.date").setEntity("channel", channel).setTimestamp("startDate", startDate).setTimestamp("finishDate", finishDate).setCacheMode(org.hibernate.CacheMode.IGNORE).scroll(org.hibernate.ScrollMode.FORWARD_ONLY)
    datumEndDate = None
    datumValue = None
    while not currentDate.getDate().after(finishDate):
        cal.setTime(currentDate.getDate())
        if cal.get(java.util.Calendar.HOUR_OF_DAY) == 0 and cal.get(java.util.Calendar.MINUTE) == 30:
            pw.print("\r\n" + mpanCoreStr + "," + dateFormat.format(currentDate.getDate()))
            pw.flush()
            #net.sf.chellow.persistant08.Hiber.session().clear()
        pw.print(",")
        if (datumEndDate == None or datumEndDate.before(currentDate.getDate())) and hhData.next():
            row = hhData.get()
            datumValue = row[0]
            datumEndDate = row[1]
        if datumEndDate.getTime() == currentDate.getDate().getTime():
            pw.print(str(round(datumValue,1)))
        currentDate = currentDate.getNext()
        net.sf.chellow.persistant08.Hiber.session().clear()
pw.close()