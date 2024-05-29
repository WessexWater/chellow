import csv
import threading
import traceback

from flask import g, request

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.models import (
    Batch,
    Bill,
    BillType,
    Era,
    RSession,
    RegisterRead,
    Supply,
    User,
)
from chellow.utils import c_months_u, csv_make_val, req_int
from chellow.views import chellow_redirect


def content(year, month, months, supply_id, user_id):
    f = None
    try:
        with RSession() as sess:
            user = User.get_by_id(sess, user_id)

            f = open_file("register_reads.csv", user, mode="w", newline="")
            w = csv.writer(f, lineterminator="\n")
            titles = (
                "duration_start",
                "duration_finish",
                "site_code",
                "site_name",
                "supply_id",
                "imp_mpan_core",
                "exp_mpan_core",
                "batch_reference",
                "bill_id",
                "bill_reference",
                "bill_issue_date",
                "bill_type",
                "register_read_id",
                "tpr",
                "coefficient",
                "prev_read_date",
                "prev_read_value",
                "prev_read_type",
                "pres_read_date",
                "pres_read_value",
                "pres_read_type",
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

                    site = era.get_physical_site(sess)

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
                        vals = {
                            "duration_start": start_date,
                            "duration_finish": finish_date,
                            "site_code": site.code,
                            "site_name": site.name,
                            "supply_id": supply_id,
                            "imp_mpan_core": era.imp_mpan_core,
                            "exp_mpan_core": era.exp_mpan_core,
                            "batch_reference": batch.reference,
                            "bill_id": bill.id,
                            "bill_reference": bill.reference,
                            "bill_issue_date": bill.issue_date,
                            "bill_type": bill_type.code,
                            "register_read_id": read.id,
                            "tpr": "md" if read.tpr is None else read.tpr.code,
                            "coefficient": read.coefficient,
                            "prev_read_date": read.previous_date,
                            "prev_read_value": read.previous_value,
                            "prev_read_type": read.previous_type.code,
                            "pres_read_date": read.present_date,
                            "pres_read_value": read.present_value,
                            "pres_read_type": read.present_type.code,
                        }
                        w.writerow(csv_make_val(vals.get(t)) for t in titles)

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


def do_get(sess):
    year = req_int("end_year")
    month = req_int("end_month")
    months = req_int("months")
    supply_id = req_int("supply_id") if "supply_id" in request.values else None
    args = year, month, months, supply_id, g.user.id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
