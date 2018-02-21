from dateutil.relativedelta import relativedelta
from datetime import datetime as Datetime
import pytz
import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
from chellow.models import (
    Session, Contract, Era, Site, SiteEra, Tpr, MeasurementRequirement, Ssc)
from chellow.utils import (
    HH, hh_min, hh_max, hh_format, req_date, req_int, make_val)
from chellow.computer import contract_func, SupplySource
from chellow.views import chellow_redirect
import chellow.computer
import chellow.dloads
from werkzeug.exceptions import BadRequest
import csv
import os
import threading
from flask import g


def content(start_date, finish_date, contract_id, user):
    caches = {}
    sess = f = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'virtual_bills.csv', user)

        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        contract = Contract.get_supplier_by_id(sess, contract_id)
        forecast_date = chellow.computer.forecast_date()

        month_start = Datetime(
            start_date.year, start_date.month, 1, tzinfo=pytz.utc)

        month_finish = month_start + relativedelta(months=1) - HH

        bill_titles = contract_func(caches, contract, 'virtual_bill_titles')()

        for tpr in sess.query(Tpr).join(MeasurementRequirement).join(Ssc). \
                join(Era).filter(
                    Era.start_date <= finish_date, or_(
                        Era.finish_date == null(),
                        Era.finish_date >= start_date), or_(
                        Era.imp_supplier_contract == contract,
                        Era.exp_supplier_contract == contract)
                ).order_by(Tpr.code).distinct():
            for suffix in ('-kwh', '-rate', '-gbp'):
                bill_titles.append(tpr.code + suffix)
        writer.writerow(
            ['MPAN Core', 'Site Code', 'Site Name', 'Account', 'From', 'To'] +
            bill_titles)
        vb_func = contract_func(caches, contract, 'virtual_bill')

        while not month_start > finish_date:
            period_start = hh_max(start_date, month_start)
            period_finish = hh_min(finish_date, month_finish)

            for era in sess.query(Era).distinct().filter(
                    or_(
                        Era.imp_supplier_contract == contract,
                        Era.exp_supplier_contract == contract),
                    Era.start_date <= period_finish,
                    or_(
                        Era.finish_date == null(),
                        Era.finish_date >= period_start)):

                chunk_start = hh_max(period_start, era.start_date)
                chunk_finish = hh_min(period_finish, era.finish_date)

                polarities = []
                if era.imp_supplier_contract == contract:
                    polarities.append(True)
                if era.exp_supplier_contract == contract:
                    polarities.append(False)
                for polarity in polarities:
                    vals = []
                    data_source = SupplySource(
                        sess, chunk_start, chunk_finish, forecast_date, era,
                        polarity, caches)

                    site = sess.query(Site).join(SiteEra).filter(
                        SiteEra.era == era,
                        SiteEra.is_physical == true()).one()

                    vals = [
                        data_source.mpan_core, site.code, site.name,
                        data_source.supplier_account,
                        hh_format(data_source.start_date),
                        hh_format(data_source.finish_date)]

                    vb_func(data_source)
                    bill = data_source.supplier_bill
                    for title in bill_titles:
                        if title in bill:
                            val = make_val(bill[title])
                            del bill[title]
                        else:
                            val = ''
                        vals.append(val)

                    for k in sorted(bill.keys()):
                        vals.append(k)
                        vals.append(str(bill[k]))
                    writer.writerow(vals)

            month_start += relativedelta(months=1)
            month_finish = month_start + relativedelta(months=1) - HH
    except BadRequest as e:
        writer.writerow([e.description])
    except BaseException:
        writer.writerow([traceback.format_exc()])
    finally:
        if sess is not None:
            sess.close()
        f.close()
        os.rename(running_name, finished_name)


def do_get(sess):
    start_date = req_date('start')
    finish_date = req_date('finish')
    contract_id = req_int('supplier_contract_id')

    threading.Thread(
        target=content,
        args=(start_date, finish_date, contract_id, g.user)).start()
    return chellow_redirect("/downloads", 303)
