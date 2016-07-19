from dateutil.relativedelta import relativedelta
from datetime import datetime as Datetime
import pytz
import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
from chellow.models import Contract, Era, Site, SiteEra
from chellow.utils import (
    HH, hh_after, hh_format, req_date, req_int, send_response)
from chellow.computer import contract_func, SupplySource
import chellow.computer


def content(start_date, finish_date, contract_id, sess):
    caches = {}
    try:
        contract = Contract.get_supplier_by_id(sess, contract_id)
        forecast_date = chellow.computer.forecast_date()

        month_start = Datetime(
            start_date.year, start_date.month, 1, tzinfo=pytz.utc)

        month_finish = month_start + relativedelta(months=1) - HH

        bill_titles = contract_func(
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
                    data_source = SupplySource(
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

                    contract_func(
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


def do_get(sess):
    start_date = req_date('start')
    finish_date = req_date('finish')
    contract_id = req_int('supplier_contract_id')

    return send_response(
        content, args=(start_date, finish_date, contract_id, sess),
        file_name='virtual_bills.csv')
