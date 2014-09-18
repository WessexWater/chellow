from net.sf.chellow.monad import Monad
import datetime
from dateutil.relativedelta import relativedelta
import pytz

Monad.getUtils()['impt'](globals(), 'utils', 'db', 'computer')

HH, hh_after = utils.HH, utils.hh_after
Supply, Site, SiteEra = db.Supply, db.Site, db.SiteEra

sess = None
try:
    sess = db.session()

    inv.getResponse().setContentType("text/csv")
    inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="daily_supplier_virtual_bill.csv"')
    pw = inv.getResponse().getWriter()

    start_year = inv.getInteger("start_year")
    start_month = inv.getInteger("start_month")
    start_day = inv.getInteger("start_day")

    finish_year = inv.getInteger("finish_year")
    finish_month = inv.getInteger("finish_month")
    finish_day = inv.getInteger("finish_day")

    start_date = datetime.datetime(start_year, start_month, start_day, tzinfo=pytz.utc)
    finish_date = datetime.datetime(finish_year, finish_month, finish_day, tzinfo=pytz.utc) + relativedelta(months=1) - HH

    caches = {}

    is_import = inv.getBoolean('is_import')

    supply_id = inv.getLong('supply_id')
    supply = Supply.get_by_id(sess, supply_id)

    forecast_date = computer.forecast_date()

    day_start = start_date

    prev_bill_titles = []

    while not day_start > finish_date:
        day_finish = day_start + relativedelta(days=1) - HH

        for era in supply.find_eras(sess, day_start, day_finish):
            if era.start_date > day_start:
                chunk_start = era.start_date
            else:
                chunk_start = day_start

            if hh_after(era.finish_date, day_finish):
                chunk_finish = day_finish
            else:
                chunk_finish = era.finish_date

            ss = computer.SupplySource(sess, chunk_start, chunk_finish, forecast_date, era, is_import, pw, caches)
 
            sup_con = ss.supplier_contract
            bill_titles = computer.contract_func(caches, sup_con, 'virtual_bill_titles', pw)()
            if bill_titles != prev_bill_titles:
                pw.println('MPAN Core,Site Code,Site Name,Account,From,To,' + ','.join(bill_titles))
                pw.flush()
                prev_bill_titles = bill_titles

            site = sess.query(Site).join(SiteEra).filter(SiteEra.era_id==era.id, SiteEra.is_physical==True).one()
            pw.print(','.join('"' + str(value) + '"' for value in [ss.mpan_core, site.code , site.name, ss.supplier_account, ss.start_date, ss.finish_date]))
            pw.flush()

            bill = computer.contract_func(caches, sup_con, 'virtual_bill', pw)(ss)
            for title in bill_titles:
                pw.print(',"' + str(bill.get(title, '')) + '"')
                if title in bill:
                    del bill[title]

            for k in sorted(bill.keys()):
                pw.print(',"' + k + '","' + str(bill[k]) + '"')
            pw.println('')
            pw.flush()

        day_start += relativedelta(days=1)
    pw.close()
finally:
    if sess is not None:
        sess.close()