import csv
import threading
import traceback
from collections import defaultdict

from flask import g

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from chellow.dloads import open_file
from chellow.models import Batch, Bill, Session, User
from chellow.utils import csv_make_val, req_int
from chellow.views import chellow_redirect


def _content(sess, writer, batch_id):
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
        "vat",
        "gross",
        "type",
        "vat_1_percent",
        "vat_1_net",
        "vat_1_vat",
        "vat_2_percent",
        "vat_2_net",
        "vat_2_vat",
    ]
    writer.writerow(titles)

    for bill in sess.scalars(
        select(Bill)
        .where(Bill.batch == batch)
        .order_by(Bill.reference, Bill.start_date)
        .options(joinedload(Bill.bill_type), joinedload(Bill.supply))
    ):
        era = bill.supply.find_era_at(sess, bill.start_date)
        vat_breakdown = {}

        bd = bill.bd
        if "vat" in bd:
            for vat_percentage, vat_vals in bd["vat"].items():
                try:
                    vbd = vat_breakdown[vat_percentage]
                except KeyError:
                    vbd = vat_breakdown[vat_percentage] = defaultdict(int)

                vbd["vat"] += vat_vals["vat"]
                vbd["net"] += vat_vals["net"]

        vals = {
            "supplier_contract": batch.contract.name,
            "batch_reference": batch.reference,
            "bill_reference": bill.reference,
            "imp_mpan_core": None if era is None else era.imp_mpan_core,
            "account": bill.account,
            "issued": bill.issue_date,
            "from": bill.start_date,
            "to": bill.finish_date,
            "kwh": bill.kwh,
            "net": bill.net,
            "vat": bill.vat,
            "gross": bill.gross,
            "type": bill.bill_type.code,
            "vat_1_percent": None,
            "vat_1_net": None,
            "vat_1_vat": None,
            "vat_2_percent": None,
            "vat_2_net": None,
            "vat_2_vat": None,
        }
        for i, (percentage, vbd) in enumerate(sorted(vat_breakdown.items()), 1):
            vals[f"vat_{i}_percentage"] = percentage
            vals[f"vat_{i}_net"] = vbd["net"]
            vals[f"vat_{i}_vat"] = vbd["vat"]

        writer.writerow(csv_make_val(vals[t]) for t in titles)


def content(user_id, batch_id):
    f = writer = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file(f"bills_batch_{batch_id}.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            _content(sess, writer, batch_id)

    except BaseException:
        msg = traceback.format_exc()
        print(msg)
        if f is not None:
            f.write(msg)
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    batch_id = req_int("batch_id")
    args = g.user.id, batch_id
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
