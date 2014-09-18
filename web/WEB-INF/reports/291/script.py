from net.sf.chellow.monad import Monad
import datetime
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from java.lang import System

Monad.getUtils()['impt'](globals(), 'db', 'utils', 'templater', 'computer')

Supply, Era, Site, SiteEra = db.Supply, db.Era, db.Site, db.SiteEra
HH, hh_format = utils.HH, utils.hh_format

caches = {}

supply_id = inv.getLong('supply_id')

sess = None
try:
    sess = db.session()
    supply = Supply.get_by_id(sess, supply_id)

    start_date = utils.form_date(inv, 'start')
    finish_date = utils.form_date(inv, 'finish')

    file_name = 'supply_virtual_bills_' + str(supply.id)

    inv.getResponse().setContentType("text/csv")
    inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="' + file_name + '.csv"')
    pw = inv.getResponse().getWriter()

    forecast_date = computer.forecast_date()

    prev_titles = None

    month_start = datetime.datetime(start_date.year, start_date.month, 1, tzinfo=pytz.utc)

    output = {}
    while not month_start > finish_date:
        month_finish = month_start + relativedelta(months=1) - HH
        period_start = month_start if month_start > start_date else start_date
        period_finish = finish_date if month_finish > finish_date else month_finish
        for era in sess.query(Era).filter(Era.supply_id==supply.id, Era.start_date<period_finish, or_(Era.finish_date==None, Era.finish_date>period_start)).order_by(Era.start_date):

            chunk_start = era.start_date if era.start_date > period_start else period_start

            chunk_finish = period_finish if utils.hh_before(period_finish, era.finish_date) else era.finish_date

            site = sess.query(Site).join(SiteEra).filter(SiteEra.era_id==era.id, SiteEra.is_physical==True).one()

            ds = computer.SupplySource(sess, chunk_start, chunk_finish, forecast_date, era, True, pw, caches)

            titles = ['Imp MPAN Core', 'Exp MPAN Core', 'Site Code', 'Site Name', 'Account', 'From', 'To', '']

            output_line = [era.imp_mpan_core, era.exp_mpan_core, site.code , site.name, ds.supplier_account, hh_format(ds.start_date), hh_format(ds.finish_date), '']
            
            mop_titles = ds.contract_func(era.mop_contract, 'virtual_bill_titles')()
            titles.extend(['mop-' + t for t in mop_titles])

            ds.contract_func(era.mop_contract, 'virtual_bill')(ds)
            bill = ds.mop_bill
            for title in mop_titles:
                output_line.append(bill.get(title, ''))
                if title in bill:
                    del bill[title]
            for k in sorted(bill.keys()):
                output_line.extend([k, bill[k]]) 

            output_line.append('')
            dc_titles = ds.contract_func(era.hhdc_contract, 'virtual_bill_titles')()
            titles.append('')
            titles.extend(['dc-' + t for t in dc_titles])

            ds.contract_func(era.hhdc_contract, 'virtual_bill')(ds)
            bill = ds.dc_bill
            for title in dc_titles:
                output_line.append(bill.get(title, ''))
                if title in bill:
                    del bill[title]
            for k in sorted(bill.keys()):
                output_line.extend([k, bill[k]])

            if era.imp_supplier_contract is not None:
                output_line.append('')
                imp_supplier_titles = ds.contract_func(era.imp_supplier_contract, 'virtual_bill_titles')()
                titles.append('')
                titles.extend(['imp-supplier-' + t for t in imp_supplier_titles])

                ds.contract_func(era.imp_supplier_contract, 'virtual_bill')(ds)
                bill = ds.supplier_bill
                for title in imp_supplier_titles:
                    output_line.append(bill.get(title, ''))
                    if title in bill:
                        del bill[title]

                for k in sorted(bill.keys()):
                    output_line.extend([k, bill[k]]) 

            if era.exp_supplier_contract is not None:
                ds = computer.SupplySource(sess, chunk_start, chunk_finish, forecast_date, era, False, pw, caches)

                output_line.append('')
                exp_supplier_titles = ds.contract_func(era.exp_supplier_contract, 'virtual_bill_titles')()
                titles.append('')
                titles.extend(['exp-supplier-' + t for t in exp_supplier_titles])

                ds.contract_func(era.exp_supplier_contract, 'virtual_bill')(ds)
                bill = ds.supplier_bill
                for title in exp_supplier_titles:
                    output_line.append(bill.get(title, ''))
                    if title in bill:
                        del bill[title]

                for k in sorted(bill.keys()):
                    output_line.extend([k, bill[k]]) 

            if titles != prev_titles:
                prev_titles != titles
                pw.println(','.join('"' + str(v) + '"' for v in titles)) 
            pw.println(','.join('"' + str('' if v is None else v) + '"' for v in output_line))
            pw.flush()

        month_start += relativedelta(months=1)

finally:
    if sess is not None:
        sess.close()

pw.close()