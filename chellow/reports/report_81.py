from sqlalchemy import or_
from sqlalchemy.sql.expression import null
from sqlalchemy.orm import joinedload
import traceback
from chellow.models import Session, Contract, Era
import chellow.computer
from chellow.utils import (
    HH, hh_min, hh_max, hh_format, req_int, utc_datetime, MONTH, csv_make_val)
from werkzeug.exceptions import BadRequest
import os
from flask import g
import threading
from chellow.views import chellow_redirect
import csv
import chellow.dloads
from dateutil.relativedelta import relativedelta


def content(contract_id, end_year, end_month, months, user):
    caches = {}
    sess = f = None
    try:
        sess = Session()
        contract = Contract.get_dc_by_id(sess, contract_id)

        finish_date = utc_datetime(end_year, end_month, 1) + MONTH - HH
        start_date = utc_datetime(end_year, end_month, 1) - relativedelta(
            months=months - 1)

        forecast_date = chellow.computer.forecast_date()
        running_name, finished_name = chellow.dloads.make_names(
            'dc_virtual_bills.csv', user)

        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')

        bill_titles = chellow.computer.contract_func(
            caches, contract, 'virtual_bill_titles')()
        header_titles = [
            'Import MPAN Core', 'Export MPAN Core', 'Start Date',
            'Finish Date']

        vb_func = chellow.computer.contract_func(
            caches, contract, 'virtual_bill')

        writer.writerow(header_titles + bill_titles)

        for era in sess.query(Era).distinct().filter(
                or_(
                    Era.finish_date == null(),
                    Era.finish_date >= start_date),
                Era.start_date <= finish_date,
                Era.dc_contract == contract).options(
                joinedload(Era.channels)).order_by(Era.supply_id):

            imp_mpan_core = era.imp_mpan_core
            if imp_mpan_core is None:
                imp_mpan_core_str = ''
                is_import = False
            else:
                is_import = True
                imp_mpan_core_str = imp_mpan_core

            exp_mpan_core = era.exp_mpan_core
            exp_mpan_core_str = '' if exp_mpan_core is None else exp_mpan_core

            chunk_start = hh_max(era.start_date, start_date)
            chunk_finish = hh_min(era.finish_date, finish_date)

            vals = [
                imp_mpan_core_str, exp_mpan_core_str, hh_format(chunk_start),
                hh_format(chunk_finish)]

            supply_source = chellow.computer.SupplySource(
                sess, chunk_start, chunk_finish, forecast_date, era, is_import,
                caches)
            vb_func(supply_source)
            bill = supply_source.dc_bill

            for title in bill_titles:
                vals.append(csv_make_val(bill.get(title)))
                if title in bill:
                    del bill[title]

            for k in sorted(bill.keys()):
                vals.append(k)
                vals.append(csv_make_val(bill[k]))

            writer.writerow(vals)

            # Avoid long-running transactions
            sess.rollback()
    except BadRequest as e:
        f.write("Problem " + e.description + traceback.format_exc() + '\n')
    except BaseException:
        msg = "Problem " + traceback.format_exc() + '\n'
        f.write(msg)
    finally:
        f.close()
        os.rename(running_name, finished_name)
        if sess is not None:
            sess.close()


def do_get(sess):
    end_year = req_int("end_year")
    end_month = req_int("end_month")
    months = req_int("months")
    contract_id = req_int('dc_contract_id')

    user = g.user

    threading.Thread(
        target=content, args=(contract_id, end_year, end_month, months, user)
        ).start()
    return chellow_redirect("/downloads", 303)
