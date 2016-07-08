import datetime
import pytz
from dateutil.relativedelta import relativedelta
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
import traceback
from chellow.models import db, Supply, Era, Site, SiteEra
from chellow.utils import (
    HH, hh_before, hh_format, req_int, req_date, send_response)
import chellow.computer
from werkzeug.exceptions import BadRequest


def content(supply_id, file_name, start_date, finish_date):
    caches = {}
    sess = None
    try:
        sess = db.session()
        supply = Supply.get_by_id(sess, supply_id)

        forecast_date = chellow.computer.forecast_date()

        prev_titles = None

        month_start = datetime.datetime(
            start_date.year, start_date.month, 1, tzinfo=pytz.utc)

        while not month_start > finish_date:
            month_finish = month_start + relativedelta(months=1) - HH
            if month_start > start_date:
                period_start = month_start
            else:
                period_start = start_date

            if month_finish > finish_date:
                period_finish = finish_date
            else:
                period_finish = month_finish

            for era in sess.query(Era).filter(
                    Era.supply == supply, Era.start_date < period_finish, or_(
                        Era.finish_date == null(),
                        Era.finish_date > period_start
                    )).order_by(Era.start_date):

                chunk_start = era.start_date \
                    if era.start_date > period_start else period_start

                chunk_finish = period_finish \
                    if hh_before(period_finish, era.finish_date) \
                    else era.finish_date

                site = sess.query(Site).join(SiteEra).filter(
                    SiteEra.era == era, SiteEra.is_physical == true()).one()

                ds = chellow.computer.SupplySource(
                    sess, chunk_start, chunk_finish, forecast_date, era, True,
                    None, caches)

                titles = [
                    'Imp MPAN Core', 'Exp MPAN Core', 'Site Code', 'Site Name',
                    'Account', 'From', 'To', '']

                output_line = [
                    era.imp_mpan_core, era.exp_mpan_core, site.code,
                    site.name, ds.supplier_account, hh_format(ds.start_date),
                    hh_format(ds.finish_date), '']

                mop_titles = ds.contract_func(
                    era.mop_contract, 'virtual_bill_titles')()
                titles.extend(['mop-' + t for t in mop_titles])

                ds.contract_func(era.mop_contract, 'virtual_bill')(ds)
                bill = ds.mop_bill
                for title in mop_titles:
                    if title in bill:
                        output_line.append(bill[title])
                        del bill[title]
                    else:
                        output_line.append('')

                for k in sorted(bill.keys()):
                    output_line.extend([k, bill[k]])

                output_line.append('')
                dc_titles = ds.contract_func(
                    era.hhdc_contract, 'virtual_bill_titles')()
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
                    imp_supplier_titles = ds.contract_func(
                        era.imp_supplier_contract, 'virtual_bill_titles')()
                    titles.append('')
                    titles.extend(
                        ['imp-supplier-' + t for t in imp_supplier_titles])

                    ds.contract_func(
                        era.imp_supplier_contract, 'virtual_bill')(ds)
                    bill = ds.supplier_bill

                    for title in imp_supplier_titles:
                        if title in bill:
                            output_line.append(bill[title])
                            del bill[title]
                        else:
                            output_line.append('')

                    for k in sorted(bill.keys()):
                        output_line.extend([k, bill[k]])

                if era.exp_supplier_contract is not None:
                    ds = chellow.computer.SupplySource(
                        sess, chunk_start, chunk_finish, forecast_date, era,
                        False, None, caches)

                    output_line.append('')
                    exp_supplier_titles = ds.contract_func(
                        era.exp_supplier_contract, 'virtual_bill_titles')()
                    titles.append('')
                    titles.extend(
                        ['exp-supplier-' + t for t in exp_supplier_titles])

                    ds.contract_func(
                        era.exp_supplier_contract, 'virtual_bill')(ds)
                    bill = ds.supplier_bill
                    for title in exp_supplier_titles:
                        output_line.append(bill.get(title, ''))
                        if title in bill:
                            del bill[title]

                    for k in sorted(bill.keys()):
                        output_line.extend([k, bill[k]])

                if titles != prev_titles:
                    prev_titles != titles
                    yield ','.join('"' + str(v) + '"' for v in titles) + '\n'
                for i, val in enumerate(output_line):
                    if isinstance(val, datetime.datetime):
                        output_line[i] = hh_format(val)
                    elif val is None:
                        output_line[i] = ''
                    else:
                        output_line[i] = str(val)
                yield ','.join(
                    '"' + str('' if v is None else v) +
                    '"' for v in output_line) + '\n'

            month_start += relativedelta(months=1)
    except BadRequest as e:
        yield "Problem: " + e.description + '\n'
    except:
        yield traceback.format_exc()
    finally:
        if sess is not None:
            sess.close()


def do_get(sess):
    supply_id = req_int('supply_id')
    file_name = 'supply_virtual_bills_' + str(supply_id) + '.csv'
    start_date = req_date('start')
    finish_date = req_date('finish')
    args = (supply_id, file_name, start_date, finish_date)
    return send_response(content, args=args, file_name=file_name)
