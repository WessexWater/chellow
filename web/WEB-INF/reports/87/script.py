from net.sf.chellow.monad import Monad
from java.lang import System
from dateutil.relativedelta import relativedelta
import datetime
import pytz
from sqlalchemy import or_

Monad.getUtils()['impt'](globals(), 'utils', 'db', 'computer')

Contract, Era, Site, SiteEra = db.Contract, db.Era, db.Site, db.SiteEra
HH, hh_after, hh_format = utils.HH, utils.hh_after, utils.hh_format

caches = {}

sess = None

try:
    sess = db.session()

    inv.getResponse().setContentType("text/csv")
    inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="virtual_bills.csv"')
    pw = inv.getResponse().getWriter()

    start_date = utils.form_date(inv, 'start')
    finish_date = utils.form_date(inv, 'finish')

    contract_id = inv.getLong('supplier_contract_id')
    contract = Contract.get_supplier_by_id(sess, contract_id)

    forecast_date = computer.forecast_date()
    timing = System.currentTimeMillis()

    month_start = datetime.datetime(start_date.year, start_date.month, 1, tzinfo=pytz.utc)

    month_finish = month_start + relativedelta(months=1) - HH

    bill_titles = computer.contract_func(caches, contract, 'virtual_bill_titles', pw)()
    pw.print('MPAN Core,Site Code,Site Name,Account,From,To,' + ','.join(bill_titles))
    pw.println('')
    pw.flush()

    while not month_start > finish_date:
        period_start = start_date if month_start < start_date else month_start

        if month_finish > finish_date:
            period_finish = finish_date
        else:
            period_finish = month_finish

        for era in sess.query(Era).distinct().filter(or_(Era.imp_supplier_contract_id==contract.id, Era.exp_supplier_contract_id==contract.id), Era.start_date<=period_finish, or_(Era.finish_date==None, Era.finish_date>=period_start)):

            era_start = era.start_date
            if period_start < era_start:
                chunk_start = era_start
            else:
                chunk_start = period_start
            era_finish = era.finish_date
            if hh_after(period_finish, era_finish):
                chunk_finish = era_finish
            else:
                chunk_finish = period_finish
            
            polarities = []
            if era.imp_supplier_contract == contract:
                polarities.append(True)
            if era.exp_supplier_contract == contract:
                polarities.append(False)
            for polarity in polarities:
                data_source = computer.SupplySource(sess, chunk_start, chunk_finish, forecast_date, era, polarity, pw, caches)
            
                site = sess.query(Site).join(SiteEra).filter(SiteEra.era_id==era.id, SiteEra.is_physical==True).one()

                pw.print(','.join('"' + str(value) + '"' for value in [data_source.mpan_core, site.code , site.name, data_source.supplier_account, hh_format(data_source.start_date), hh_format(data_source.finish_date)]))
                pw.flush()

                computer.contract_func(caches, contract, 'virtual_bill', pw)(data_source)
                bill = data_source.supplier_bill
                for title in bill_titles:
                    pw.print(',"' + str(bill.get(title, '')) + '"')
                    if title in bill:
                        del bill[title]
                keys = bill.keys()
                keys.sort()
                for k in keys:
                    pw.print(',"' + k + '","' + str(bill[k]) + '"')
                pw.println('')
                pw.flush()

        month_start += relativedelta(months=1)
        month_finish = month_start + relativedelta(months=1) - HH
    pw.close()
finally:
    if sess is not None:
        sess.close()