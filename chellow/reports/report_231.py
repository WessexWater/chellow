import csv
import os
import sys
import threading
import traceback

from flask import g

from sqlalchemy import or_
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

import chellow.dloads
from chellow.e.computer import SupplySource, contract_func, forecast_date
from chellow.models import Contract, Era, Session
from chellow.utils import csv_make_val, hh_format, hh_max, hh_min, req_date, req_int
from chellow.views import chellow_redirect


def content(running_name, finished_name, start_date, finish_date, contract_id):
    caches = {}
    sess = supply_source = None
    try:
        sess = Session()
        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")
        contract = Contract.get_mop_by_id(sess, contract_id)

        f_date = forecast_date()
        header_titles = [
            "Import MPAN Core",
            "Export MPAN Core",
            "Start Date",
            "Finish Date",
        ]

        bill_titles = contract_func(caches, contract, "virtual_bill_titles")()
        writer.writerow(header_titles + bill_titles)
        vb_func = contract_func(caches, contract, "virtual_bill")

        for era in (
            sess.query(Era)
            .filter(
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
                Era.start_date <= finish_date,
                Era.mop_contract == contract,
            )
            .order_by(Era.imp_mpan_core, Era.exp_mpan_core, Era.start_date)
        ):
            chunk_start = hh_max(era.start_date, start_date)
            chunk_finish = hh_min(era.finish_date, finish_date)
            import_mpan_core = era.imp_mpan_core
            if import_mpan_core is None:
                import_mpan_core_str = ""
            else:
                is_import = True
                import_mpan_core_str = import_mpan_core

            export_mpan_core = era.exp_mpan_core
            if export_mpan_core is None:
                export_mpan_core_str = ""
            else:
                is_import = False
                export_mpan_core_str = export_mpan_core

            out = [
                import_mpan_core_str,
                export_mpan_core_str,
                hh_format(chunk_start),
                hh_format(chunk_finish),
            ]
            supply_source = SupplySource(
                sess, chunk_start, chunk_finish, f_date, era, is_import, caches
            )
            vb_func(supply_source)
            bill = supply_source.mop_bill
            for title in bill_titles:
                if title in bill:
                    out.append(csv_make_val(bill[title]))
                    del bill[title]
                else:
                    out.append("")
            for k in sorted(bill.keys()):
                out.append(k)
                out.append(str(bill[k]))
            writer.writerow(out)
    except BadRequest as e:
        msg = "Problem "
        if supply_source is not None:
            msg += (
                f"with supply {supply_source.mpan_core} starting at "
                f"{hh_format(supply_source.start_date)} "
            )
        msg += str(e)
        sys.stderr.write(msg)
        writer.writerow([msg])
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
    start_date = req_date("start")
    finish_date = req_date("finish")
    contract_id = req_int("mop_contract_id")

    running_name, finished_name = chellow.dloads.make_names(
        "mop_virtual_bills.csv", g.user
    )
    args = running_name, finished_name, start_date, finish_date, contract_id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
