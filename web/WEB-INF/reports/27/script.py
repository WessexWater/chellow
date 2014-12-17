'''
from net.sf.chellow.monad import Hiber, UserException
from net.sf.chellow.monad.types import MonadDate
from java.sql import Timestamp, ResultSet
from java.util import GregorianCalendar, Calendar, TimeZone, Locale, Date
from net.sf.chellow.physical import HhStartDate, Site, Supply
from java.text import SimpleDateFormat, DecimalFormat
from java.lang import Math, System
from net.sf.chellow.billing import Contract
from org.python.util import PythonInterpreter

year = inv.getInteger("end_year")
month = inv.getInteger("end_month")
months = inv.getInteger("months")

if not inv.isValid():
    raise UserException()

if inv.hasParameter('supply_id'):
    supply_id = inv.getLong('supply_id')
    query = Hiber.session().createQuery(
        "select bill, bill.batch, bill.batch.contract, bill.supply from "
        "Bill bill where bill.supply = :supply "
        "and bill.startDate.date >= :startDate "
        "and bill.startDate.date <= :finishDate "
        "order by bill.startDate.date").setEntity(
        'supply', Supply.getSupply(supply_id))
else:
    query = Hiber.session().createQuery(
        "select bill, bill.batch, bill.batch.contract "
        "from Bill bill "
        "where bill.startDate.date >= :startDate "
        "and bill.startDate.date <= :finishDate")

cal = MonadDate.getCalendar()
cal.set(Calendar.YEAR, year)
cal.set(Calendar.MONTH, month - 1)
cal.set(Calendar.DAY_OF_MONTH, 1)
cal.set(Calendar.HOUR_OF_DAY, 0)
cal.set(Calendar.MINUTE, 0)
cal.set(Calendar.SECOND, 0)
cal.set(Calendar.MILLISECOND, 0)
cal.add(Calendar.MONTH, 1)
cal.add(Calendar.MINUTE, -30)
finish_date = HhStartDate(cal.getTime())
cal.add(Calendar.MINUTE, 30)
cal.add(Calendar.MONTH, -1 * months)
start_date = HhStartDate(cal.getTime())

now_date = Date()
file_date_format = SimpleDateFormat("yyyy-MM-dd'_'HHmm")
file_date_format.setCalendar(cal)

inv.getResponse().setContentType("text/csv")
inv.getResponse().setHeader(
    'Content-Disposition',
    'attachment; filename="bills_' +
    file_date_format.format(now_date) + '.csv"')
pw = inv.getResponse().getWriter()
pw.println(
    "Report Start,Report Finish,Supply Id,Import MPAN Core,Export MPAN Core, "
    "Contract Name,Batch Reference,Bill Id,Bill From,Bill To,Bill Reference, "
    "Bill Issue Date,Bill Type, Bill kWh, Bill Net, Bill VAT, Bill Gross")
pw.flush()

issue_format = SimpleDateFormat("yyyy-MM-dd HH:mm")
issue_format.setCalendar(cal)

bills = query.setTimestamp('startDate', start_date.getDate()).setTimestamp(
    'finishDate', finish_date.getDate()).scroll()
while bills.next():
    bill = bills.get(0)
    batch = bills.get(1)
    contract = bills.get(2)
    supply = bill.getSupply()

    era = supply.getEra(bill.getStartDate())
    if era is None:
        imp_mpan_core = 'No Generation'
        exp_mpan_core = 'No Generation'
    else:
        imp_mpan_core = era.getImpMpanCore()
        if imp_mpan_core is None:
            imp_mpan_core = ''
        exp_mpan_core = era.getExpMpanCore()
        if exp_mpan_core is None:
            exp_mpan_core = ''

    pw.println(','.join('"' + str(value) + '"' for value in [
        start_date, finish_date, supply.getId(), imp_mpan_core, exp_mpan_core,
        contract.getName(), batch.getReference(), bill.getId(),
        bill.getStartDate(), bill.getFinishDate(), bill.getReference(),
        issue_format.format(bill.getIssueDate()), bill.getType().getCode(),
        bill.getKwh(), bill.getNet(), bill.getVat(), bill.getGross()]))
    pw.flush()
    Hiber.session().clear()

bills.close()
pw.close()
'''
