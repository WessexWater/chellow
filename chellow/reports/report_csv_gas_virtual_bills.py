from dateutil.relativedelta import relativedelta
from datetime import datetime as Datetime
import pytz
import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
import chellow.computer
import chellow.g_engine
from chellow.models import Session, GContract, GEra, Site, SiteGEra
import chellow.downloads
import csv
from chellow.utils import HH, hh_after, hh_format, req_date, req_int
import sys
import os
import threading
from flask import g
from chellow.views import chellow_redirect


def content(start_date, finish_date, g_contract_id, user):
    report_context = {}
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'gas_virtual_bills.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')

        g_contract = GContract.get_by_id(sess, g_contract_id)
        forecast_date = chellow.computer.forecast_date()

        month_start = Datetime(
            start_date.year, start_date.month, 1, tzinfo=pytz.utc)

        month_finish = month_start + relativedelta(months=1) - HH

        bill_titles = chellow.computer.contract_func(
            report_context, g_contract, 'virtual_bill_titles', None)()
        writer.writerow(
            [
                'MPRN', 'Site Code', 'Site Name', 'Account', 'From', 'To'] +
            bill_titles)

        while not month_start > finish_date:
            period_start = start_date \
                if month_start < start_date else month_start

            if month_finish > finish_date:
                period_finish = finish_date
            else:
                period_finish = month_finish

            for g_era in sess.query(GEra).distinct().filter(
                    or_(
                        GEra.imp_g_contract == g_contract,
                        GEra.exp_g_contract == g_contract),
                    GEra.start_date <= period_finish,
                    or_(
                        GEra.finish_date == null(),
                        GEra.finish_date >= period_start)):

                g_era_start = g_era.start_date
                if period_start < g_era_start:
                    chunk_start = g_era_start
                else:
                    chunk_start = period_start
                g_era_finish = g_era.finish_date
                if hh_after(period_finish, g_era_finish):
                    chunk_finish = g_era_finish
                else:
                    chunk_finish = period_finish

                polarities = []
                if g_era.imp_g_contract == g_contract:
                    polarities.append(True)
                if g_era.exp_g_contract == g_contract:
                    polarities.append(False)
                for polarity in polarities:
                    data_source = chellow.g_engine.DataSource(
                        sess, chunk_start, chunk_finish, forecast_date, g_era,
                        polarity, None, report_context)

                    site = sess.query(Site).join(SiteGEra).filter(
                        SiteGEra.g_era == g_era,
                        SiteGEra.is_physical == true()).one()

                    vals = [
                        data_source.mprn, site.code, site.name,
                        data_source.supplier_account,
                        hh_format(data_source.start_date),
                        hh_format(data_source.finish_date)]

                    chellow.computer.contract_func(
                        report_context, g_contract, 'virtual_bill',
                        None)(data_source)
                    bill = data_source.bill
                    for title in bill_titles:
                        if title in bill:
                            val = str(bill[title])
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
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    start_date = req_date('start')
    finish_date = req_date('finish')
    g_contract_id = req_int('g_contract_id')

    threading.Thread(
        target=content, args=(start_date, finish_date, g_contract_id, g.user)
        ).start()
    return chellow_redirect("/downloads", 303)
