import csv
import os
import threading
import traceback

from flask import g

from sqlalchemy.sql import func

import chellow.dloads
from chellow.models import Batch, Bill, Contract, GBatch, GBill, GContract, Session
from chellow.utils import csv_make_val
from chellow.views import chellow_redirect


def content(user):
    sess = f = writer = None
    try:
        sess = Session()
        running_name, finished_name = chellow.dloads.make_names("batches.csv", user)
        f = open(running_name, mode="w", newline="")
        writer = csv.writer(f, lineterminator="\n")

        titles = (
            "utility",
            "chellow_id",
            "reference",
            "description",
            "contract_name",
            "num_bills",
            "net_gbp",
            "vat_gbp",
            "gross_gbp",
            "kwh",
            "min_start_date",
        )
        writer.writerow(titles)

        for batch, contract in (
            sess.query(Batch, Contract)
            .join(Contract)
            .order_by(Batch.contract_id, Batch.reference)
        ):

            (
                num_bills,
                sum_net_gbp,
                sum_vat_gbp,
                sum_gross_gbp,
                sum_kwh,
                min_start_date,
            ) = (
                sess.query(
                    func.count(Bill.id),
                    func.sum(Bill.net),
                    func.sum(Bill.vat),
                    func.sum(Bill.gross),
                    func.sum(Bill.kwh),
                    func.min(Bill.start_date),
                )
                .filter(Bill.batch == batch)
                .one()
            )

            if sum_net_gbp is None:
                sum_net_gbp = sum_vat_gbp = sum_gross_gbp = sum_kwh = 0
            vals = {
                "utility": "electricity",
                "chellow_id": batch.id,
                "reference": batch.reference,
                "description": batch.description,
                "contract_name": contract.name,
                "num_bills": num_bills,
                "net_gbp": sum_net_gbp,
                "vat_gbp": sum_vat_gbp,
                "gross_gbp": sum_gross_gbp,
                "kwh": sum_kwh,
                "min_start_date": min_start_date,
            }

            writer.writerow(csv_make_val(vals[t]) for t in titles)

            # Avoid a long-running transaction
            sess.rollback()

        for g_batch, g_contract in (
            sess.query(GBatch, GContract)
            .join(GContract)
            .order_by(GBatch.g_contract_id, GBatch.reference)
        ):

            (
                num_bills,
                sum_net_gbp,
                sum_vat_gbp,
                sum_gross_gbp,
                sum_kwh,
                min_start_date,
            ) = (
                sess.query(
                    func.count(GBill.id),
                    func.sum(GBill.net),
                    func.sum(GBill.vat),
                    func.sum(GBill.gross),
                    func.sum(GBill.kwh),
                    func.min(GBill.start_date),
                )
                .filter(GBill.g_batch == g_batch)
                .one()
            )

            if sum_net_gbp is None:
                sum_net_gbp = sum_vat_gbp = sum_gross_gbp = sum_kwh = 0
            vals = {
                "utility": "gas",
                "chellow_id": g_batch.id,
                "reference": g_batch.reference,
                "description": g_batch.description,
                "contract_name": g_contract.name,
                "num_bills": num_bills,
                "net_gbp": sum_net_gbp,
                "vat_gbp": sum_vat_gbp,
                "gross_gbp": sum_gross_gbp,
                "kwh": sum_kwh,
                "min_start_date": min_start_date,
            }

            writer.writerow(csv_make_val(vals[t]) for t in titles)

            # Avoid a long-running transaction
            sess.rollback()

    except BaseException:
        writer.writerow([traceback.format_exc()])
    finally:
        if sess is not None:
            sess.close()
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    args = (g.user,)
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
