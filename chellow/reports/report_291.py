from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true
import traceback
from chellow.models import (
    Session, Supply, Era, Site, SiteEra, Tpr, MeasurementRequirement, Ssc)
from chellow.utils import (
    hh_min, hh_max, hh_format, req_int, req_date, csv_make_val)
from chellow.views import chellow_redirect
import chellow.computer
from werkzeug.exceptions import BadRequest
import csv
import os
from flask import g
import threading


def content(supply_id, file_name, start_date, finish_date, user):
    caches = {}
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'supply_virtual_bills_' + str(supply_id) + '.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')

        supply = Supply.get_by_id(sess, supply_id)

        forecast_date = chellow.computer.forecast_date()

        prev_titles = None

        for era in sess.query(Era).filter(
                Era.supply == supply, Era.start_date < finish_date, or_(
                    Era.finish_date == null(),
                    Era.finish_date > start_date)).order_by(Era.start_date):

            chunk_start = hh_max(era.start_date, start_date)
            chunk_finish = hh_min(era.finish_date, finish_date)
            site = sess.query(Site).join(SiteEra).filter(
                SiteEra.era == era, SiteEra.is_physical == true()).one()

            ds = chellow.computer.SupplySource(
                sess, chunk_start, chunk_finish, forecast_date, era,
                era.imp_supplier_contract is not None, caches)

            titles = [
                'Imp MPAN Core', 'Exp MPAN Core', 'Site Code', 'Site Name',
                'Account', 'From', 'To', ''
            ]

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
                era.dc_contract, 'virtual_bill_titles')()
            titles.append('')
            titles.extend(['dc-' + t for t in dc_titles])

            ds.contract_func(era.dc_contract, 'virtual_bill')(ds)
            bill = ds.dc_bill
            for title in dc_titles:
                output_line.append(bill.get(title, ''))
                if title in bill:
                    del bill[title]
            for k in sorted(bill.keys()):
                output_line.extend([k, bill[k]])

            tpr_query = sess.query(Tpr).join(MeasurementRequirement). \
                join(Ssc).join(Era).filter(
                    Era.start_date <= chunk_finish, or_(
                        Era.finish_date == null(),
                        Era.finish_date >= chunk_start)
                ).order_by(Tpr.code).distinct()

            if era.imp_supplier_contract is not None:
                output_line.append('')
                supplier_titles = ds.contract_func(
                    era.imp_supplier_contract, 'virtual_bill_titles')()
                for tpr in tpr_query.filter(
                        Era.imp_supplier_contract != null()):
                    for suffix in ('-kwh', '-rate', '-gbp'):
                        supplier_titles.append(tpr.code + suffix)
                titles.append('')
                titles.extend(['imp-supplier-' + t for t in supplier_titles])

                ds.contract_func(era.imp_supplier_contract, 'virtual_bill')(ds)
                bill = ds.supplier_bill

                for title in supplier_titles:
                    if title in bill:
                        output_line.append(bill[title])
                        del bill[title]
                    else:
                        output_line.append('')

                for k in sorted(bill.keys()):
                    output_line.extend([k, bill[k]])

            if era.exp_supplier_contract is not None:
                ds = chellow.computer.SupplySource(
                    sess, chunk_start, chunk_finish, forecast_date, era, False,
                    caches)

                output_line.append('')
                supplier_titles = ds.contract_func(
                    era.exp_supplier_contract, 'virtual_bill_titles')()
                for tpr in tpr_query.filter(
                        Era.exp_supplier_contract != null()):
                    for suffix in ('-kwh', '-rate', '-gbp'):
                        supplier_titles.append(tpr.code + suffix)
                titles.append('')
                titles.extend(['exp-supplier-' + t for t in supplier_titles])

                ds.contract_func(
                    era.exp_supplier_contract, 'virtual_bill')(ds)
                bill = ds.supplier_bill
                for title in supplier_titles:
                    output_line.append(bill.get(title, ''))
                    if title in bill:
                        del bill[title]

                for k in sorted(bill.keys()):
                    output_line.extend([k, bill[k]])

            if titles != prev_titles:
                prev_titles = titles
                writer.writerow([str(v) for v in titles])
            for i, val in enumerate(output_line):
                output_line[i] = csv_make_val(val)
            writer.writerow(output_line)
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
    supply_id = req_int('supply_id')
    file_name = 'supply_virtual_bills_' + str(supply_id) + '.csv'
    start_date = req_date('start')
    finish_date = req_date('finish')
    args = (supply_id, file_name, start_date, finish_date, g.user)

    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
