import traceback
from sqlalchemy import or_
from sqlalchemy.sql.expression import null
import chellow.computer
from chellow.models import Contract, Era, Session
from chellow.utils import hh_format, req_date, req_int
import csv
import sys
import os
from chellow.views import chellow_redirect
import threading
from flask import g


def content(start_date, finish_date, contract_id, user):
    caches = {}
    sess = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names(
            'mop_virtual_bills.csv', user)
        f = open(running_name, mode='w', newline='')
        writer = csv.writer(f, lineterminator='\n')
        contract = Contract.get_mop_by_id(sess, contract_id)

        forecast_date = chellow.computer.forecast_date()
        header_titles = [
            'Import MPAN Core', 'Export MPAN Core', 'Start Date',
            'Finish Date']

        bill_titles = chellow.computer.contract_func(
            caches, contract, 'virtual_bill_titles', None)()
        writer.writerow(header_titles + bill_titles)

        for era in sess.query(Era).filter(
                or_(
                    Era.finish_date == null(), Era.finish_date >= start_date),
                Era.start_date <= finish_date, Era.mop_contract == contract). \
                order_by(Era.supply_id):
            import_mpan_core = era.imp_mpan_core
            if import_mpan_core is None:
                import_mpan_core_str = ''
            else:
                mpan_core = import_mpan_core
                is_import = True
                import_mpan_core_str = mpan_core

            export_mpan_core = era.exp_mpan_core
            if export_mpan_core is None:
                export_mpan_core_str = ''
            else:
                is_import = False
                mpan_core = export_mpan_core
                export_mpan_core_str = mpan_core

            out = [
                import_mpan_core_str, export_mpan_core_str,
                hh_format(start_date), hh_format(finish_date)]
            supply_source = chellow.computer.SupplySource(
                sess, start_date, finish_date, forecast_date, era, is_import,
                None, caches)
            chellow.computer.contract_func(
                caches, contract, 'virtual_bill', None)(supply_source)
            bill = supply_source.mop_bill
            for title in bill_titles:
                if title in bill:
                    out.append(str(bill[title]))
                    del bill[title]
                else:
                    out.append('')
            for k in sorted(bill.keys()):
                out.append(k)
                out.append(str(bill[k]))
            writer.writerow(out)
    except:
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
    contract_id = req_int('mop_contract_id')
    args = (start_date, finish_date, contract_id, g.user)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
