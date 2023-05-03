import csv
import os
import threading
import traceback

from flask import g

from sqlalchemy import select
from sqlalchemy.orm import joinedload

import chellow.dloads
from chellow.models import Batch, Bill, Session, User
from chellow.utils import csv_make_val, req_int
from chellow.views import chellow_redirect


def content(user_id, batch_id):
    sess = f = writer = None
    try:
        sess = Session()
        user = User.get_by_id(sess, user_id)
        running_name, finished_name = chellow.dloads.make_names(
            f"bills_batch_{batch_id}.csv", user
        )
        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")
        batch = Batch.get_by_id(sess, batch_id)
        titles = [
            "supplier_contract",
            "batch_reference",
            "bill_reference",
            "imp_mpan_core",
            "account",
            "issued",
            "from",
            "to",
            "kwh",
            "net",
            "vAT",
            "gross",
            "type",
        ]
        writer.writerow(titles)

        for bill in sess.execute(
            select(Bill)
            .where(Bill.batch == batch)
            .order_by(Bill.reference, Bill.start_date)
            .options(joinedload(Bill.bill_type), joinedload(Bill.supply))
        ).scalars():
            era = bill.supply.find_era_at(sess, bill.start_date)
            vals = [
                batch.contract.name,
                batch.reference,
                bill.reference,
                None if era is None else era.imp_mpan_core,
                bill.account,
                bill.issue_date,
                bill.start_date,
                bill.finish_date,
                bill.kwh,
                bill.net,
                bill.vat,
                bill.gross,
                bill.bill_type.code,
            ]
            writer.writerow(csv_make_val(v) for v in vals)

    except BaseException:
        msg = traceback.format_exc()
        print(msg)
        if f is not None:
            f.write(msg)
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    batch_id = req_int("batch_id")
    args = g.user.id, batch_id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
