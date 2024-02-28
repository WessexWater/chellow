import csv
import threading
import traceback

from flask import g

from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.e.computer import SupplySource, contract_func, forecast_date
from chellow.models import Contract, Era, Session, User
from chellow.utils import c_months_u, csv_make_val, hh_format, hh_max, hh_min, req_int
from chellow.views import chellow_redirect


def content(user_id, contract_id, end_year, end_month, months):
    caches = {}
    f = supply_source = None
    try:
        with Session() as sess:
            contract = Contract.get_dc_by_id(sess, contract_id)

            month_list = list(
                c_months_u(finish_year=end_year, finish_month=end_month, months=months)
            )
            start_date, finish_date = month_list[0][0], month_list[-1][-1]

            f_date = forecast_date()

            user = User.get_by_id(sess, user_id)
            f = open_file("dc_virtual_bills.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")

            bill_titles = contract_func(caches, contract, "virtual_bill_titles")()
            header_titles = [
                "Import MPAN Core",
                "Export MPAN Core",
                "Start Date",
                "Finish Date",
                "energisation_status",
                "gsp_group",
                "dno",
                "site_code",
                "imp_is_substation",
                "imp_llfc_code",
                "imp_llfc_description",
                "exp_is_substation",
                "exp_llfc_code",
                "exp_llfc_description",
            ]

            vb_func = contract_func(caches, contract, "virtual_bill")

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
                is_import = era.imp_mpan_core is not None

                chunk_start = hh_max(era.start_date, start_date)
                chunk_finish = hh_min(era.finish_date, finish_date)
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

                vals = [
                    era.imp_mpan_core,
                    era.exp_mpan_core,
                    chunk_start,
                    chunk_finish,
                    supply_source.energisation_status_code,
                    supply_source.gsp_group_code,
                    supply_source.dno_code,
                    era.get_physical_site(sess).code,
                    imp_is_substation,
                    imp_llfc_code,
                    imp_llfc_description,
                    exp_is_substation,
                    exp_llfc_code,
                    exp_llfc_description,
                ]

                vb_func(supply_source)
                bill = supply_source.dc_bill

                for title in bill_titles:
                    vals.append(bill.get(title))
                    if title in bill:
                        del bill[title]

                for k in sorted(bill.keys()):
                    vals.append(k)
                    vals.append(bill[k])

                writer.writerow(csv_make_val(v) for v in vals)

                # Avoid long-running transactions
                sess.rollback()
    except BadRequest as e:
        msg = "Problem "
        if supply_source is not None:
            msg += (
                f"with supply {supply_source.mpan_core} starting at "
                + f"{hh_format(supply_source.start_date)} "
            )
        msg += str(e)
        writer.writerow([msg])
    except BaseException:
        msg = "Problem " + traceback.format_exc() + "\n"
        print(msg)
        if f is not None:
            f.write(msg)
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    end_year = req_int("end_year")
    end_month = req_int("end_month")
    months = req_int("months")
    contract_id = req_int("dc_contract_id")

    args = g.user.id, contract_id, end_year, end_month, months
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
