import csv
import threading
import traceback

from flask import g, redirect


from sqlalchemy import null, or_, select
from sqlalchemy.orm import joinedload

from chellow.dloads import open_file
from chellow.models import Batch, Bill, Contract, Era, RSession, ReportRun, User
from chellow.utils import (
    c_months_u,
    csv_make_val,
    hh_max,
    hh_min,
    hh_range,
    req_date,
    req_int,
    to_ct,
)


def content(user_id, report_run_id, contract_id, months_length, finish_date):
    f = writer = None
    try:
        with RSession() as sess:
            caches = {}
            contract = Contract.get_by_id(sess, contract_id)
            user = User.get_by_id(sess, user_id)
            f = open_file(
                f"missing_bills_{contract.id}.csv", user, mode="w", newline=""
            )
            writer = csv.writer(f, lineterminator="\n")
            titles = (
                "contract_name",
                "month_start",
                "month_finish",
                "site_code",
                "site_name",
                "imp_mpan_core",
                "exp_mpan_core",
                "account",
            )
            writer.writerow(titles)

            finish_date_ct = to_ct(finish_date)

            for month_start, month_finish in c_months_u(
                finish_year=finish_date_ct.year,
                finish_month=finish_date_ct.month,
                months=months_length,
            ):
                missing_bills = {}
                missing_account = {}
                account_missing_tuple = hh_range(caches, month_start, month_finish)
                for era in sess.scalars(
                    select(Era)
                    .where(
                        Era.start_date <= month_finish,
                        or_(Era.finish_date == null(), Era.finish_date >= month_start),
                        or_(
                            Era.mop_contract == contract,
                            Era.dc_contract == contract,
                            Era.imp_supplier_contract == contract,
                            Era.exp_supplier_contract == contract,
                        ),
                    )
                    .options(joinedload(Era.supply))
                ):
                    chunk_start = hh_max(era.start_date, month_start)
                    chunk_finish = hh_min(era.finish_date, month_finish)
                    missing_set = set(hh_range(caches, chunk_start, chunk_finish))
                    if era.mop_contract == contract:
                        account = ""
                    elif era.dc_contract == contract:
                        account = ""
                    elif era.imp_supplier_contract == contract:
                        account = era.imp_supplier_account
                    elif era.imp_supplier_contract == contract:
                        account = era.exp_supplier_account

                    try:
                        account_missing_set = missing_account[account]
                    except KeyError:
                        account_missing_set = missing_account[account] = set(
                            account_missing_tuple
                        )
                    supply = era.supply

                    for bill in sess.scalars(
                        select(Bill)
                        .join(Batch)
                        .where(
                            Batch.contract == contract,
                            Bill.supply == supply,
                            Bill.start_date <= chunk_finish,
                            Bill.finish_date >= chunk_start,
                        )
                    ):
                        found_set = set(
                            hh_range(caches, bill.start_date, bill.finish_date)
                        )
                        missing_set.difference_update(found_set)
                        account_missing_set.difference_update(found_set)

                    if len(missing_set) > 0:
                        site = era.get_physical_site(sess)

                        values = {
                            "contract_id": contract.id,
                            "contract_name": contract.name,
                            "month_start": month_start,
                            "month_finish": month_finish,
                            "era_id": era.id,
                            "supply_id": supply.id,
                            "imp_mpan_core": era.imp_mpan_core,
                            "exp_mpan_core": era.exp_mpan_core,
                            "site_id": site.id,
                            "site_code": site.code,
                            "site_name": site.name,
                            "account": account,
                            "market_role_code": contract.market_role.code,
                        }
                        missing_bills[era.id] = values
                for era_id, values in missing_bills.items():
                    if len(missing_account[values["account"]]) > 0:
                        writer.writerow(csv_make_val(values[t]) for t in titles)
                        ReportRun.w_insert_row(report_run_id, "", titles, values, {})

    except BaseException:
        msg = traceback.format_exc()
        print(msg)
        if writer is not None:
            writer.writerow([msg])
    finally:
        ReportRun.w_update(report_run_id, "finished")
        if f is not None:
            f.close()


def do_get(sess):
    contract_id = req_int("contract_id")
    months = req_int("months")
    finish_date = req_date("finish", resolution="month")
    report_run = ReportRun.insert(
        sess,
        "missing_e_bills",
        g.user,
        "missing_e_bills",
        {},
    )
    sess.commit()
    args = g.user.id, report_run.id, contract_id, months, finish_date
    threading.Thread(target=content, args=args).start()
    return redirect(f"/report_runs/{report_run.id}", 303)
