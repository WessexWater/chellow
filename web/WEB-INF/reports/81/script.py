from net.sf.chellow.monad import Monad
import datetime
import pytz
from sqlalchemy import or_
from dateutil.relativedelta import relativedelta

Monad.getUtils()['impt'](globals(), 'computer', 'db', 'utils')

hh_before, HH, hh_format = utils.hh_before, utils.HH, utils.hh_format
Contract, Era = db.Contract, db.Era

caches = {}

def content():
    sess = None
    try:
        sess = db.session()

        inv.getResponse().setContentType("text/csv")
        inv.getResponse().setHeader('Content-Disposition', 'attachment;filename="hhdc_vbs.csv"')
        pw = inv.getResponse().getWriter()
        end_year = inv.getInteger("end_year")
        end_month = inv.getInteger("end_month")
        months = inv.getInteger("months")
        contract_id = inv.getLong('hhdc_contract_id')

        contract = Contract.get_by_id(sess, contract_id)

        finish_date = datetime.datetime(end_year, end_month, 1, tzinfo=pytz.utc) + relativedelta(months=1) - HH

        start_date = datetime.datetime(end_year, end_month, 1, tzinfo=pytz.utc) - relativedelta(months=months - 1)

        forecast_date = computer.forecast_date()

        yield 'Import MPAN Core, Export MPAN Core, Start Date, Finish Date'
        bill_titles = computer.contract_func(
            caches, contract, 'virtual_bill_titles', pw)()
        for title in bill_titles:
            yield ',' + title
        yield '\n'

        for era in sess.query(Era).distinct().join(Era.hhdc_contract).filter(or_(Era.finish_date==None,Era.finish_date>=start_date), Era.start_date<=finish_date, Contract.id==contract.id).order_by(Era.supply_id):
            imp_mpan_core = era.imp_mpan_core
            if imp_mpan_core is None:
                imp_mpan_core_str = ''
                is_import = False
            else:
                is_import = True
                imp_mpan_core_str = imp_mpan_core

            exp_mpan_core = era.exp_mpan_core
            exp_mpan_core_str = '' if exp_mpan_core is None else exp_mpan_core

            if era.start_date > start_date:
                chunk_start = era.start_date
            else:
                chunk_start = start_date

            if hh_before(era.finish_date, finish_date):
                chunk_finish = era.finish_date
            else:
                chunk_finish = finish_date

            yield imp_mpan_core_str + ',' + exp_mpan_core_str + ',' + \
                hh_format(chunk_start) + ',' + hh_format(chunk_finish) + ','
            supply_source = computer.SupplySource(
                sess, chunk_start, chunk_finish, forecast_date, era, is_import,
                pw, caches)
            bill = supply_source.contract_func(contract, 'virtual_bill')(
                supply_source)
            for title in bill_titles:
                yield '"' + str(bill.get(title, '')) + '",'
                if title in bill:
                    del bill[title]
            keys = bill.keys()
            keys.sort()
            for k in keys:
                yield ',"' + k + '","' + str(bill[k]) + '"'
            yield '\n'

    finally:
        if sess is not None:
            sess.close()
