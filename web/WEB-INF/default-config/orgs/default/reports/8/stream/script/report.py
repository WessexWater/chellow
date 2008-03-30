import sys
import net.sf.chellow.persistant08
import org.hibernate
import net.sf.chellow.monad.ui
import calendar
import java.util
import net.sf.chellow.data08

inv.getResponse().setContentType("text/csv")
pw = inv.getResponse().getWriter()

pw.println("Account number,MPANs,Reconciliation")
pw.flush()
year = inv.getInteger('year')
month = inv.getInteger('month')
reconciliation = inv.getInteger('reconciliation')
totalKwh = 0
if not inv.isValid():
    raise net.sf.chellow.monad.ui.UserException.newInvalidArgument()
accounts = {'18894375': ['209578838', '228568878']}
cal = java.util.GregorianCalendar(java.util.TimeZone.getTimeZone("GMT"), java.util.Locale.UK)
cal.clear()
cal.set(java.util.Calendar.YEAR, year)
cal.set(java.util.Calendar.MONTH, month)
cal.add(java.util.Calendar.MINUTE, 30)
startDate = cal.getTime()
cal.add(java.util.Calendar.MONTH, 1)
cal.add(java.util.Calendar.MINUTE, -30)
finishDate = cal.getTime()

for accountNumber, mpanList in accounts:
    for mpanStr in mpanlist:
        supply = net.sf.chellow.persistant08.MpanCore.getMpanCore(mpanStr).getSupply()
        totalKwh = totalKwh + net.sf.chellow.persistant08.Hiber.session().createQuery("select sum(datum.value.float) from HhDatum datum where datum.supply.organization = :organization and datum.supply = :supply and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate").setEntity("organization", organization).setEntity('supply', supply).setTimestamp('startDate', startDate).setTimestamp('finishDate', finishDate).uniqueResult()

gbpPerKwh = reconciliation / double(totalKwh)
for accountNumber, mpanList in accounts:
    accountKwh = 0
    for mpanStr in mpanlist:
        supply = net.sf.chellow.persistant08.MpanCore.getMpanCore(mpanStr).getSupply()
        accountKwh = accountKwh + net.sf.chellow.persistant08.Hiber.session().createQuery("select sum(datum.value.float) from HhDatum datum where datum.supply.organization = :organization and datum.supply = :supply and datum.endDate.date >= :startDate and datum.endDate.date <= :finishDate").setEntity("organization", organization).setEntity('supply', supply).setTimestamp('startDate', startDate).setTimestamp('finishDate', finishDate).uniqueResult()
        pw.println(accountNumber + ',' + str(mpanList) + ',' + accountKwh * gbpPerKwh)
        pw.flush()
pw.close()