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

    file_name = 'supply_virtual_bills_hh_' + str(supply.id)

    inv.getResponse().setContentType("text/csv")
    inv.getResponse().addHeader('Content-Disposition', 'attachment; filename="' + file_name + '.csv"')
    pw = inv.getResponse().getWriter()

    forecast_date = computer.forecast_date()

    prev_titles = None

    hh_start = start_date

    output = {}
    while not hh_start > finish_date:
        era = sess.query(Era).filter(Era.supply_id==supply.id, Era.start_date <= hh_start, or_(Era.finish_date == None, Era.finish_date >= hh_start)).one()

        site = sess.query(Site).join(SiteEra).filter(SiteEra.era_id == era.id, SiteEra.is_physical == True).one()

        ds = computer.SupplySource(sess, hh_start, hh_start, forecast_date, era, True, pw, caches)

        titles = ['MPAN Core', 'Site Code', 'Site Name', 'Account', 'HH Start', '']

        output_line = [ds.mpan_core, site.code , site.name, ds.supplier_account, hh_format(ds.start_date), '']
            
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

        if era.imp_supplier_contract != None:
            contract = era.imp_supplier_contract
            output_line.append('')
            supplier_titles = ds.contract_func(contract, 'virtual_bill_titles')()
            titles.append('')
            titles.extend(['imp-supplier-' + t for t in supplier_titles])

            ds.contract_func(contract, 'virtual_bill')(ds)
            bill = ds.supplier_bill
            for title in supplier_titles:
                output_line.append(bill.get(title, ''))
                if title in bill:
                    del bill[title]

            for k in sorted(bill.keys()):
                output_line.extend([k, bill[k]]) 


        if era.exp_supplier_contract != None:
            contract = era.exp_supplier_contract
            ds = computer.SupplySource(sess, hh_start, hh_start, forecast_date, era, False, pw, caches)
            output_line.append('')
            supplier_titles = ds.contract_func(contract, 'virtual_bill_titles')()
            titles.append('')
            titles.extend(['exp-supplier-' + t for t in supplier_titles])

            ds.contract_func(contract, 'virtual_bill')(ds)
            bill = ds.supplier_bill
            for title in supplier_titles:
                output_line.append(bill.get(title, ''))
                if title in bill:
                    del bill[title]

            for k in sorted(bill.keys()):
                output_line.extend([k, bill[k]]) 

        if titles != prev_titles:
            prev_titles = titles
            pw.println(','.join('"' + str(v) + '"' for v in titles)) 
        pw.println(','.join('"' + str(v) + '"' for v in output_line))
        pw.flush()

        hh_start += HH
finally:
    if sess is not None:
        sess.close()

pw.close()