import csv
import os
import threading
import traceback

from flask import g, request

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest

import chellow.dloads
from chellow.models import (
    Batch,
    Bill,
    BillType,
    Era,
    RegisterRead,
    Session,
    Supply,
    User,
)
from chellow.utils import c_months_u, csv_make_val, req_int
from chellow.views import chellow_redirect


def content(year, month, months, supply_id, user_id):
    f = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)

            running_name, finished_name = chellow.dloads.make_names(
                "register_reads.csv", user
            )
            f = open(running_name, mode="w", newline="")
            w = csv.writer(f, lineterminator="\n")
            titles = (
                "Duration Start",
                "Duration Finish",
                "Supply Id",
                "Import MPAN Core",
                "Export MPAN Core",
                "Batch Reference",
                "Bill Id",
                "Bill Reference",
                "Bill Issue Date",
                "Bill Type",
                "Register Read Id",
                "TPR",
                "Coefficient",
                "Previous Read Date",
                "Previous Read Value",
                "Previous Read Type",
                "Present Read Date",
                "Present Read Value",
                "Present Read Type",
            )
            w.writerow(titles)

            month_pairs = list(
                c_months_u(finish_year=year, finish_month=month, months=months)
            )
            start_date, finish_date = month_pairs[0][0], month_pairs[-1][-1]

            supplies = (
                select(Supply)
                .join(Bill)
                .join(RegisterRead)
                .where(
                    or_(
                        and_(
                            RegisterRead.present_date >= start_date,
                            RegisterRead.present_date <= finish_date,
                        ),
                        and_(
                            RegisterRead.previous_date >= start_date,
                            RegisterRead.previous_date <= finish_date,
                        ),
                    )
                )
                .order_by(Supply.id)
                .distinct()
            )

            if supply_id is not None:
                supply = Supply.get_by_id(sess, supply_id)
                supplies = supplies.where(Supply.id == supply.id)

            for supply in sess.scalars(supplies):
                supply_id = supply.id
                for bill, batch, bill_type in sess.execute(
                    select(Bill, Batch, BillType)
                    .join(Batch)
                    .join(BillType)
                    .join(RegisterRead)
                    .filter(
                        Bill.supply == supply,
                        or_(
                            and_(
                                RegisterRead.present_date >= start_date,
                                RegisterRead.present_date <= finish_date,
                            ),
                            and_(
                                RegisterRead.previous_date >= start_date,
                                RegisterRead.previous_date <= finish_date,
                            ),
                        ),
                    )
                ):
                    era = supply.find_era_at(sess, bill.start_date)
                    if era is None:
                        eras = (
                            sess.query(Era)
                            .filter(Era.supply == supply)
                            .order_by(Era.start_date)
                            .all()
                        )
                        if bill.start_date < eras[0].start_date:
                            era = eras[0]
                        else:
                            era = eras[-1]

                    for read in (
                        sess.query(RegisterRead)
                        .filter(
                            RegisterRead.bill == bill,
                            or_(
                                and_(
                                    RegisterRead.present_date >= start_date,
                                    RegisterRead.present_date <= finish_date,
                                ),
                                and_(
                                    RegisterRead.previous_date >= start_date,
                                    RegisterRead.previous_date <= finish_date,
                                ),
                            ),
                        )
                        .options(
                            joinedload(RegisterRead.tpr),
                            joinedload(RegisterRead.previous_type),
                            joinedload(RegisterRead.present_type),
                        )
                    ):
                        vals = [
                            start_date,
                            finish_date,
                            supply_id,
                            era.imp_mpan_core,
                            era.exp_mpan_core,
                            batch.reference,
                            bill.id,
                            bill.reference,
                            bill.issue_date,
                            bill_type.code,
                            read.id,
                            "md" if read.tpr is None else read.tpr.code,
                            read.coefficient,
                            read.previous_date,
                            read.previous_value,
                            read.previous_type.code,
                            read.present_date,
                            read.present_value,
                            read.present_type.code,
                        ]
                        w.writerow(csv_make_val(v) for v in vals)

                    # Avoid a long-running transaction
                    sess.rollback()

    except BadRequest as e:
        w.writerow([e.description])
    except BaseException:
        msg = traceback.format_exc()
        print(msg)
        f.write(msg)
    finally:
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    year = req_int("end_year")
    month = req_int("end_month")
    months = req_int("months")
    supply_id = req_int("supply_id") if "supply_id" in request.values else None
    args = year, month, months, supply_id, g.user.id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
