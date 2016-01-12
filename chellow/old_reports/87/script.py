from net.sf.chellow.monad import Monad
from dateutil.relativedelta import relativedelta
import datetime
import pytz
import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
import db
import utils
import computer
Monad.getUtils()['impt'](globals(), 'utils', 'db', 'computer')
Contract, Era, Site, SiteEra = db.Contract, db.Era, db.Site, db.SiteEra
HH, hh_after, hh_format = utils.HH, utils.hh_after, utils.hh_format
inv = globals()['inv']

caches = {}
sess = None
start_date = utils.form_date(inv, 'start')
finish_date = utils.form_date(inv, 'finish')
contract_id = inv.getLong('supplier_contract_id')


def content():
    try:
        sess = db.session()

        contract = Contract.get_supplier_by_id(sess, contract_id)
        forecast_date = computer.forecast_date()

        month_start = datetime.datetime(
            start_date.year, start_date.month, 1, tzinfo=pytz.utc)

        month_finish = month_start + relativedelta(months=1) - HH

        bill_titles = computer.contract_func(
            caches, contract, 'virtual_bill_titles', None)()
        yield 'MPAN Core,Site Code,Site Name,Account,From,To,' + \
            ','.join(bill_titles) + '\n'

        while not month_start > finish_date:
            period_start = start_date \
                if month_start < start_date else month_start

            if month_finish > finish_date:
                period_finish = finish_date
            else:
                period_finish = month_finish

            for era in sess.query(Era).distinct().filter(
                    or_(
                        Era.imp_supplier_contract_id == contract.id,
                        Era.exp_supplier_contract_id == contract.id),
                    Era.start_date <= period_finish,
                    or_(
                        Era.finish_date == null(),
                        Era.finish_date >= period_start)):

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
                    data_source = computer.SupplySource(
                        sess, chunk_start, chunk_finish, forecast_date, era,
                        polarity, None, caches)

                    site = sess.query(Site).join(SiteEra).filter(
                        SiteEra.era == era,
                        SiteEra.is_physical == true()).one()

                    yield ','.join('"' + str(value) + '"' for value in [
                        data_source.mpan_core, site.code, site.name,
                        data_source.supplier_account,
                        hh_format(data_source.start_date),
                        hh_format(data_source.finish_date)])

                    computer.contract_func(
                        caches, contract, 'virtual_bill', None)(data_source)
                    bill = data_source.supplier_bill
                    for title in bill_titles:
                        if title in bill:
                            val = str(bill[title])
                            del bill[title]
                        else:
                            val = ''
                        yield ',"' + val + '"'

                    for k in sorted(bill.keys()):
                        yield ',"' + k + '","' + str(bill[k]) + '"'
                    yield '\n'

            month_start += relativedelta(months=1)
            month_finish = month_start + relativedelta(months=1) - HH
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()

utils.send_response(inv, content, file_name='virtual_bills.csv')
