import csv
import sys
import threading
import traceback

from flask import g, redirect

from sqlalchemy import or_
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.e.computer import SupplySource, contract_func, forecast_date
from chellow.models import Contract, Era, Session, User
from chellow.utils import csv_make_val, hh_format, hh_max, hh_min, req_date, req_int


def content(user_id, start_date, finish_date, contract_id):
    caches = {}
    supply_source = f = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file("mop_virtual_bills.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            contract = Contract.get_mop_by_id(sess, contract_id)

            f_date = forecast_date()
            header_titles = [
                "imp_mpan_core",
                "exp_mpan_core",
                "start_date",
                "finish_date",
                "energisation_status",
                "gsp_group",
                "dno",
                "era_start",
                "pc",
                "meter_type",
                "site_code",
                "imp_is_substation",
                "imp_llfc_code",
                "imp_llfc_description",
                "exp_is_substation",
                "exp_llfc_code",
                "exp_llfc_description",
            ]

            bill_titles = contract_func(caches, contract, "virtual_bill_titles")()
            titles = header_titles + bill_titles
            writer.writerow(titles)
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
                is_import = era.imp_mpan_core is not None

                supply_source = SupplySource(
                    sess, chunk_start, chunk_finish, f_date, era, is_import, caches
                )

                if is_import:
                    imp_is_substation = supply_source.is_substation
                    imp_llfc_code = supply_source.llfc_code
                    imp_llfc_description = supply_source.llfc.description
                    exp_is_substation = exp_llfc_code = exp_llfc_description = None
                else:
                    exp_is_substation = supply_source.is_substation
                    exp_llfc_code = supply_source.llfc_code
                    exp_llfc_description = supply_source.llfc.description
                    imp_is_substation = imp_llfc_code = imp_llfc_description = None

                out = {
                    "imp_mpan_core": era.imp_mpan_core,
                    "exp_mpan_core": era.exp_mpan_core,
                    "start_date": chunk_start,
                    "finish_date": chunk_finish,
                    "energisation_status": supply_source.energisation_status_code,
                    "gsp_group": supply_source.gsp_group_code,
                    "dno": supply_source.dno_code,
                    "era_start": era.start_date,
                    "pc": supply_source.pc_code,
                    "meter_type": supply_source.meter_type_code,
                    "site_code": era.get_physical_site(sess).code,
                    "imp_is_substation": imp_is_substation,
                    "imp_llfc_code": imp_llfc_code,
                    "imp_llfc_description": imp_llfc_description,
                    "exp_is_substation": exp_is_substation,
                    "exp_llfc_code": exp_llfc_code,
                    "exp_llfc_description": exp_llfc_description,
                }
                vb_func(supply_source)
                bill = supply_source.mop_bill
                for title in bill_titles:
                    if title in bill:
                        out[title] = bill[title]
                writer.writerow(csv_make_val(out.get(t)) for t in titles)

                sess.rollback()  # Avoid long-running transactions
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
        if f is not None:
            f.close()


def do_get(sess):
    start_date = req_date("start")
    finish_date = req_date("finish")
    contract_id = req_int("mop_contract_id")

    args = g.user.id, start_date, finish_date, contract_id
    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
