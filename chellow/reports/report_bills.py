import threading
import traceback
from collections import defaultdict

from flask import g, redirect

from odio import create_spreadsheet

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from chellow.dloads import open_file
from chellow.models import Batch, Bill, Session, User
from chellow.utils import make_val, req_int


def _make_rows(sess, batch_id):
    batch = Batch.get_by_id(sess, batch_id)
    bill_titles = [
        "contract",
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
        "breakdown",
    ]
    element_titles = [
        "contract",
        "batch_reference",
        "bill_reference",
        "name",
        "start_date",
        "finish_date",
        "net",
        "breakdown",
    ]
    bill_rows = [bill_titles]
    element_rows = [element_titles]

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

        bill_vals = {
            "contract": batch.contract.name,
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
            "breakdown": bill.breakdown,
        }
        for i, (percentage, vbd) in enumerate(sorted(vat_breakdown.items()), 1):
            bill_vals[f"vat_{i}_percentage"] = percentage
            bill_vals[f"vat_{i}_net"] = vbd["net"]
            bill_vals[f"vat_{i}_vat"] = vbd["vat"]
        for element in bill.elements:
            element_vals = {
                "contract": batch.contract.name,
                "batch_reference": batch.reference,
                "bill_reference": bill.reference,
                "name": element.name,
                "start_date": element.start_date,
                "finish_date": element.finish_date,
                "net": element.net,
                "breakdown": element.breakdown,
            }
            element_rows.append([make_val(element_vals[t]) for t in element_titles])

        bill_rows.append([make_val(bill_vals[t]) for t in bill_titles])
    return bill_rows, element_rows


def content(user_id, batch_id):
    f = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file(f"bills_batch_{batch_id}.ods", user, mode="wb")
            bill_rows, element_rows = _make_rows(sess, batch_id)
            with create_spreadsheet(f, compressed=True) as sheet:
                for title, rows in (("bills", bill_rows), ("elements", element_rows)):
                    prep_rows = [[make_val(v) for v in row] for row in rows]
                    sheet.append_table(title, prep_rows)

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
    return redirect("/downloads", 303)
