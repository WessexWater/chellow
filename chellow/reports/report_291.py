import csv
import threading
import traceback

from flask import g, redirect

from sqlalchemy import or_, select
from sqlalchemy.sql.expression import null, true

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.e.computer import SupplySource, forecast_date
from chellow.models import (
    Era,
    MeasurementRequirement,
    Session,
    Site,
    SiteEra,
    Ssc,
    Supply,
    Tpr,
    User,
)
from chellow.utils import csv_make_val, date_format, hh_max, hh_min, req_date, req_int


def content(supply_id, start_date, finish_date, user_id):
    caches = {}
    f = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            f = open_file(
                f"supply_virtual_bills_{supply_id}.csv", user, mode="w", newline=""
            )
            writer = csv.writer(f, lineterminator="\n")

            supply = Supply.get_by_id(sess, supply_id)

            forecast_dt = forecast_date()

            prev_titles = None

            for era in sess.scalars(
                select(Era)
                .where(
                    Era.supply == supply,
                    Era.start_date <= finish_date,
                    or_(Era.finish_date == null(), Era.finish_date >= start_date),
                )
                .order_by(Era.start_date)
            ):
                chunk_start = hh_max(era.start_date, start_date)
                chunk_finish = hh_min(era.finish_date, finish_date)
                site = sess.scalars(
                    select(Site)
                    .join(SiteEra)
                    .where(SiteEra.era == era, SiteEra.is_physical == true())
                ).one()

                ds = SupplySource(
                    sess,
                    chunk_start,
                    chunk_finish,
                    forecast_dt,
                    era,
                    era.imp_supplier_contract is not None,
                    caches,
                )

                titles = [
                    "imp_mpan_core",
                    "exp_mpan_core",
                    "site_code",
                    "site_name",
                    "account",
                    "from",
                    "to",
                ]

                vals = {
                    "imp_mpan_core": era.imp_mpan_core,
                    "exp_mpan_core": era.exp_mpan_core,
                    "site_code": site.code,
                    "site_name": site.name,
                    "account": ds.supplier_account,
                    "from": date_format(ds.start_date),
                    "to": date_format(ds.finish_date),
                }

                mop_titles = ds.contract_func(era.mop_contract, "virtual_bill_titles")()
                titles.extend(["mop-" + t for t in mop_titles])

                ds.contract_func(era.mop_contract, "virtual_bill")(ds)
                bill = ds.mop_bill
                for k, v in bill.items():
                    if k == "elements":
                        for elname, parts in v.items():
                            for part_name, part_value in parts.items():
                                vals[f"mop-{elname}-{part_name}"] = part_value
                    else:
                        vals[f"mop-{k}"] = v

                dc_titles = ds.contract_func(era.dc_contract, "virtual_bill_titles")()
                titles.extend(["dc-" + t for t in dc_titles])

                ds.contract_func(era.dc_contract, "virtual_bill")(ds)
                bill = ds.dc_bill
                for k, v in bill.items():
                    if k == "elements":
                        for elname, parts in v.items():
                            for part_name, part_value in parts.items():
                                vals[f"dc-{elname}-{part_name}"] = part_value
                    else:
                        vals[f"dc-{k}"] = v

                tpr_query = (
                    select(Tpr)
                    .join(MeasurementRequirement)
                    .join(Ssc)
                    .join(Era)
                    .where(
                        Era.start_date <= chunk_finish,
                        or_(Era.finish_date == null(), Era.finish_date >= chunk_start),
                    )
                    .order_by(Tpr.code)
                    .distinct()
                )

                if era.imp_supplier_contract is not None:
                    supplier_titles = ds.contract_func(
                        era.imp_supplier_contract, "virtual_bill_titles"
                    )()
                    for tpr in sess.scalars(
                        tpr_query.where(Era.imp_supplier_contract != null())
                    ):
                        for suffix in ("-kwh", "-rate", "-gbp"):
                            supplier_titles.append(tpr.code + suffix)
                    titles.extend(["imp-supplier-" + t for t in supplier_titles])

                    ds.contract_func(era.imp_supplier_contract, "virtual_bill")(ds)
                    bill = ds.supplier_bill
                    for k, v in bill.items():
                        if k == "elements":
                            for elname, parts in v.items():
                                for part_name, part_value in parts.items():
                                    vals[f"imp-supplier-{elname}-{part_name}"] = (
                                        part_value
                                    )
                        else:
                            vals[f"imp-supplier-{k}"] = v

                if era.exp_supplier_contract is not None:
                    ds = SupplySource(
                        sess, chunk_start, chunk_finish, forecast_dt, era, False, caches
                    )

                    supplier_titles = ds.contract_func(
                        era.exp_supplier_contract, "virtual_bill_titles"
                    )()
                    for tpr in sess.scalars(
                        tpr_query.filter(Era.exp_supplier_contract != null())
                    ):
                        for suffix in ("-kwh", "-rate", "-gbp"):
                            supplier_titles.append(tpr.code + suffix)
                    titles.extend(["exp-supplier-" + t for t in supplier_titles])

                    ds.contract_func(era.exp_supplier_contract, "virtual_bill")(ds)
                    bill = ds.supplier_bill
                    for k, v in bill.items():
                        if k == "elements":
                            for elname, parts in v.items():
                                for part_name, part_value in parts.items():
                                    vals[f"exp-supplier-{elname}-{part_name}"] = (
                                        part_value
                                    )
                        else:
                            vals[f"exp-supplier-{k}"] = v

                if titles != prev_titles:
                    prev_titles = titles
                    writer.writerow([str(v) for v in titles])
                writer.writerow([csv_make_val(vals.get(t)) for t in titles])
    except BadRequest as e:
        writer.writerow(["Problem: " + e.description])
    except BaseException:
        msg = traceback.format_exc()
        if f is not None:
            writer.writerow([msg])
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    supply_id = req_int("supply_id")
    start_date = req_date("start")
    finish_date = req_date("finish")
    args = supply_id, start_date, finish_date, g.user.id

    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
