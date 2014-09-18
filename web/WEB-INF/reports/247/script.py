from net.sf.chellow.monad import Hiber, UserException
from net.sf.chellow.monad.types import MonadDate
from java.util import GregorianCalendar, TimeZone, Locale, Calendar, Date
from net.sf.chellow.physical import MpanCore, HhStartDate, Supply
from net.sf.chellow.billing import SupplierContract, NonCoreContract, Dno
from java.text import DecimalFormat, SimpleDateFormat
from java.lang import System

df = SimpleDateFormat("yyyyMMdd'T'HHmm'Z'")
cal = MonadDate.getCalendar()
df.setCalendar(cal)

inv.getResponse().setContentType("text/csv")
inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="scenario_' + df.format(Date()) + '.csv"')
pw = inv.getResponse().getWriter()
pw.flush()

to_date = inv.getDateTime('to')
from_date = inv.getDateTime('from')
contract_id = inv.getLong('contract-id')
replaced_contract_id = inv.getLong('replaced-contract-id')

if not inv.isValid():
    raise UserException()

to_date = HhStartDate(to_date)
from_date = HhStartDate(from_date)

contract = SupplierContract.getSupplierContract(contract_id)
replaced_contract = SupplierContract.getSupplierContract(replaced_contract_id)

computer = NonCoreContract.getNonCoreContract('computer')
comterp = computer.callFunction('create_comterp', [])

site_query = Hiber.session().createQuery("select supGen.site from SiteEra supGen where supGen.era = :era and supGen.isPhysical = true")

pw.print('Original Contract,New Contract,MPAN Core,Site Code,Site Name,Account,From,To')
pw.flush()
contract_function = comterp.get('contract_function') 
vb_func = contract_function(contract, 'virtual_bill', pw)
if vb_func is None:
    raise UserException("There isn't a virtual_bill function in the contract " + contract.getName())

titles_func = contract_function(contract, 'virtual_bill_titles', pw)
if titles_func is None:
    raise UserException("There isn't a virtual_bill_titles function in the contract " + contract.getName())

bill_titles = titles_func()
for title in bill_titles:
    pw.print(',' + title)
pw.println('')
pw.flush()

supply_source_class = comterp.get('SupplySource')

forecast_date = comterp.get('forecast_date')()
timing = System.currentTimeMillis()

cal = MonadDate.getCalendar()
cal.setTime(from_date.getDate())
cal.set(Calendar.DAY_OF_MONTH, 1)
cal.set(Calendar.HOUR_OF_DAY, 0)
cal.set(Calendar.MINUTE, 0)
month_start = HhStartDate(cal.getTime())

while not month_start.after(to_date):
    cal.setTime(month_start.getDate())
    cal.add(Calendar.MONTH, 1)
    cal.add(Calendar.MINUTE, -30)
    month_finish = HhStartDate(cal.getTime())
    period_from = from_date if from_date.after(month_start) else month_start
    period_to = to_date if to_date.before(month_finish) else month_finish

    eras = Hiber.session().createQuery("from Era era where ((era.importMpan is not null and era.importMpan.supplierContract = :replacedContract) or (era.exportMpan is not null and era.exportMpan.supplierContract = :replacedContract)) and era.startDate.date <= :monthFinish and (era.finishDate is null or era.finishDate.date >= :monthStart)").setEntity('replacedContract', replaced_contract).setTimestamp('monthFinish', period_to.getDate()).setTimestamp('monthStart', period_from.getDate()).scroll()
    while eras.next():
        era = eras.get(0)

        gen_start = era.getStartDate()
        chunk_start = gen_start if period_from.before(gen_start) else period_from
        gen_finish = era.getFinishDate()
        chunk_finish = gen_finish if period_to.after(gen_finish) else period_to
        import_mpan = era.getImportMpan()
        if import_mpan is not None and import_mpan.getSupplierContract().equals(contract):
            mpan = import_mpan
        else:
            mpan = era.getExportMpan()

        data_source = supply_source_class(chunk_start, chunk_finish, forecast_date, mpan, comterp, pw)

        site = site_query.setEntity('era', data_source.supply_era).uniqueResult()
        pw.print(','.join('"' + str(value) + '"' for value in [replaced_contract.getName(), contract.getName(), data_source.mpan_core_str, site.getCode() , site.getName(), data_source.supplier_account, data_source.start_date, data_source.finish_date]))
        pw.flush()
        bill = vb_func(data_source)
        for title in bill_titles:
            if title in bill:
                pw.print(',"' + str(bill[title]) + '"')
                del bill[title]
            else:
                pw.print(',')                
        keys = bill.keys()
        keys.sort()
        for k in keys:
            pw.print(',"' + k + '","' + str(bill[k]) + '"')
        pw.println('')
        pw.flush()
        Hiber.session().clear()
    eras.close()
    cal.setTime(month_start.getDate())
    cal.add(Calendar.MONTH, 1)
    month_start = HhStartDate(cal.getTime())
pw.close()