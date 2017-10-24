from datetime import datetime as Datetime
from dateutil.relativedelta import relativedelta
import pytz
import traceback
from sqlalchemy.sql.expression import true
from chellow.utils import (
    HH, hh_min, hh_max, hh_format, req_int, req_bool, csv_make_val)
from chellow.views import chellow_redirect
from chellow.models import Supply, Site, SiteEra, Session
import chellow.computer
from flask import g
import csv
from werkzeug.exceptions import BadRequest
import os
import threading


def content(
        start_year, start_month, start_day, finish_year, finish_month,
        finish_day, is_import, supply_id, user):
    caches = {}
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'daily_supplier_virtual_bill.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        start_date = Datetime(
            start_year, start_month, start_day, tzinfo=pytz.utc)
        finish_date = Datetime(
            finish_year, finish_month, finish_day, tzinfo=pytz.utc) + \
            relativedelta(days=1) - HH

        supply = Supply.get_by_id(sess, supply_id)
        forecast_date = chellow.computer.forecast_date()
        day_start = start_date
        prev_bill_titles = []

        while not day_start > finish_date:
            day_finish = day_start + relativedelta(days=1) - HH

            for era in supply.find_eras(sess, day_start, day_finish):
                chunk_start = hh_max(era.start_date, day_start)
                chunk_finish = hh_min(era.finish_date, day_finish)

                ss = chellow.computer.SupplySource(
                    sess, chunk_start, chunk_finish, forecast_date, era,
                    is_import, caches)

                sup_con = ss.supplier_contract
                bill_titles = chellow.computer.contract_func(
                    caches, sup_con, 'virtual_bill_titles')()
                if bill_titles != prev_bill_titles:
                    writer.writerow(
                        [
                            'MPAN Core', 'Site Code', 'Site Name', 'Account',
                            'From', 'To'] + bill_titles)
                    prev_bill_titles = bill_titles

                site = sess.query(Site).join(SiteEra).filter(
                    SiteEra.era == era, SiteEra.is_physical == true()).one()
                row = [
                    ss.mpan_core, site.code, site.name, ss.supplier_account,
                    hh_format(ss.start_date), hh_format(ss.finish_date)]

                chellow.computer.contract_func(
                    caches, sup_con, 'virtual_bill')(ss)
                bill = ss.supplier_bill
                for title in bill_titles:
                    if title in bill:
                        row.append(csv_make_val(bill[title]))
                        del bill[title]
                    else:
                        row.append('')

                for k in sorted(bill.keys()):
                    row.append(k)
                    row.append(csv_make_val(bill[k]))
                writer.writerow(row)

            day_start += relativedelta(days=1)
    except BadRequest as e:
        writer.writerow(["Problem: " + e.description])
    except BaseException:
        writer.writerow([traceback.format_exc()])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    start_year = req_int('start_year')
    start_month = req_int('start_month')
    start_day = req_int("start_day")

    finish_year = req_int('finish_year')
    finish_month = req_int('finish_month')
    finish_day = req_int('finish_day')

    is_import = req_bool('is_import')
    supply_id = req_int('supply_id')

    threading.Thread(
        target=content, args=(
            start_year, start_month, start_day, finish_year, finish_month,
            finish_day, is_import, supply_id, g.user)).start()
    return chellow_redirect("/downloads", 303)
