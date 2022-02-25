import csv
import os
import threading
import traceback

from flask import g

from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

import chellow.computer
import chellow.dloads
from chellow.models import Contract, Era, Session
from chellow.utils import c_months_u, csv_make_val, hh_format, hh_max, hh_min, req_int
from chellow.views.home import chellow_redirect


def content(contract_id, end_year, end_month, months, user):
    caches = {}
    sess = f = supply_source = None
    try:
        sess = Session()
        contract = Contract.get_dc_by_id(sess, contract_id)

        month_list = list(
            c_months_u(finish_year=end_year, finish_month=end_month, months=months)
        )
        start_date, finish_date = month_list[0][0], month_list[-1][-1]

        forecast_date = chellow.computer.forecast_date()
        running_name, finished_name = chellow.dloads.make_names(
            "dc_virtual_bills.csv", user
        )

        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")

        bill_titles = chellow.computer.contract_func(
            caches, contract, "virtual_bill_titles"
        )()
        header_titles = [
            "Import MPAN Core",
            "Export MPAN Core",
            "Start Date",
            "Finish Date",
        ]

        vb_func = chellow.computer.contract_func(caches, contract, "virtual_bill")

        writer.writerow(header_titles + bill_titles)

        for era in (
            sess.query(Era)
            .distinct()
            .filter(
                or_(Era.finish_date == null(), Era.finish_date >= start_date),
                Era.start_date <= finish_date,
                Era.dc_contract == contract,
            )
            .options(joinedload(Era.channels))
            .order_by(Era.supply_id)
        ):

            imp_mpan_core = era.imp_mpan_core
            if imp_mpan_core is None:
                imp_mpan_core_str = ""
                is_import = False
            else:
                is_import = True
                imp_mpan_core_str = imp_mpan_core

            exp_mpan_core = era.exp_mpan_core
            exp_mpan_core_str = "" if exp_mpan_core is None else exp_mpan_core

            chunk_start = hh_max(era.start_date, start_date)
            chunk_finish = hh_min(era.finish_date, finish_date)

            vals = [
                imp_mpan_core_str,
                exp_mpan_core_str,
                hh_format(chunk_start),
                hh_format(chunk_finish),
            ]

            supply_source = chellow.computer.SupplySource(
                sess, chunk_start, chunk_finish, forecast_date, era, is_import, caches
            )
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
        msg = "Problem "
        if supply_source is not None:
            msg += (
                "with supply "
                + supply_source.mpan_core
                + " starting at "
                + hh_format(supply_source.start_date)
                + " "
            )
        msg += str(e)
        writer.writerow([msg])
    except BaseException:
        msg = "Problem " + traceback.format_exc() + "\n"
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
    contract_id = req_int("dc_contract_id")

    args = contract_id, end_year, end_month, months, g.user
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
