import csv
import sys
import threading
import traceback
from collections import OrderedDict, defaultdict
from datetime import datetime as Datetime
from decimal import Decimal
from itertools import combinations
from numbers import Number

from flask import g, redirect, request

from sqlalchemy import null, or_, select, true
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest

import chellow.gas.engine
from chellow.dloads import open_file
from chellow.models import (
    GBatch,
    GBill,
    GContract,
    GEra,
    RSession,
    ReportRun,
    Site,
    SiteGEra,
    User,
)
from chellow.utils import csv_make_val, hh_max, hh_min, req_date, req_int, to_utc


def content(
    g_batch_id,
    g_bill_id,
    g_contract_id,
    start_date,
    finish_date,
    user_id,
    report_run_id,
):
    forecast_date = to_utc(Datetime.max)
    report_context = {}
    sess = tmp_file = None
    try:
        with RSession() as sess:
            user = User.get_by_id(sess, user_id)

            tmp_file = open_file("g_bill_check.csv", user, mode="w")
            csv_writer = csv.writer(tmp_file)
            g_bills = (
                select(GBill)
                .order_by(GBill.g_supply_id, GBill.reference)
                .options(
                    joinedload(GBill.g_supply),
                    joinedload(GBill.g_batch),
                )
            )
            if g_batch_id is not None:
                g_batch = GBatch.get_by_id(sess, g_batch_id)
                g_contract = g_batch.g_contract
                g_bills = g_bills.where(GBill.g_batch == g_batch)

            elif g_bill_id is not None:
                g_bill = GBill.get_by_id(sess, g_bill_id)
                g_contract = g_bill.g_batch.g_contract
                g_bills = g_bills.where(GBill.id == g_bill.id)

            elif g_contract_id is not None:
                g_contract = GContract.get_by_id(sess, g_contract_id)
                g_bills = g_bills.join(GBatch).where(
                    GBatch.g_contract == g_contract,
                    GBill.start_date <= finish_date,
                    GBill.finish_date >= start_date,
                )

            vbf = chellow.gas.engine.g_contract_func(
                report_context, g_contract, "virtual_bill"
            )
            if vbf is None:
                raise BadRequest(
                    f"The contract {g_contract.name} doesn't have a function "
                    f"virtual_bill."
                )

            header_titles = [
                "batch",
                "bill_reference",
                "bill_type",
                "bill_start_date",
                "bill_finish_date",
                "mprn",
                "supply_name",
                "site_code",
                "site_name",
                "covered_start",
                "covered_finish",
                "covered_bill_ids",
            ]
            bill_titles = chellow.gas.engine.g_contract_func(
                report_context, g_contract, "virtual_bill_titles"
            )()

            titles = header_titles[:]
            for title in bill_titles:
                for prefix in ("covered_", "virtual_"):
                    titles.append(prefix + title)
                if title.endswith("_gbp"):
                    titles.append("difference_" + title)

            csv_writer.writerow(titles)

            g_bill_map = defaultdict(set, {})
            for b in sess.execute(g_bills).scalars():
                g_bill_map[b.g_supply.id].add(b.id)

            for g_supply_id, g_bill_ids in g_bill_map.items():
                while len(g_bill_ids) > 0:
                    _process_g_bill_ids(
                        sess,
                        report_context,
                        g_contract,
                        g_bill_ids,
                        forecast_date,
                        bill_titles,
                        vbf,
                        titles,
                        csv_writer,
                        report_run_id,
                    )
        ReportRun.w_update(report_run_id, "finished")
    except BadRequest as e:
        tmp_file.write(f"Problem: {e.description}")
        ReportRun.w_update(report_run_id, "problem")
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + "\n")
        tmp_file.write(f"Problem {msg}")
        ReportRun.w_update(report_run_id, "interrupted")
    finally:
        tmp_file.close()


def _process_g_bill_ids(
    sess,
    report_context,
    g_contract,
    g_bill_ids,
    forecast_date,
    bill_titles,
    vbf,
    titles,
    csv_writer,
    report_run_id,
):
    g_bill_id = list(sorted(g_bill_ids))[0]
    g_bill_ids.remove(g_bill_id)
    g_bill = sess.query(GBill).filter(GBill.id == g_bill_id).one()
    g_supply = g_bill.g_supply
    vals = {
        "covered_vat_gbp": Decimal("0.00"),
        "covered_net_gbp": Decimal("0.00"),
        "covered_gross_gbp": Decimal("0.00"),
        "covered_kwh": Decimal(0),
        "covered_start": g_bill.start_date,
        "covered_finish": g_bill.finish_date,
        "covered_bill_ids": [],
        "virtual_problem": "",
    }
    site_id = None
    read_dict = defaultdict(set)
    for g_read in g_bill.g_reads:
        if not all(
            g_read.msn == era.msn
            for era in g_supply.find_g_eras(sess, g_read.prev_date, g_read.pres_date)
        ):
            vals["virtual_problem"] += (
                f"The MSN {g_read.msn} of the register read {g_read.id} doesn't match "
                f"the MSN of all the relevant eras."
            )

        for dt, typ in [
            (g_read.pres_date, g_read.pres_type),
            (g_read.prev_date, g_read.prev_type),
        ]:
            typ_set = read_dict[str(dt) + "-" + g_read.msn]
            typ_set.add(typ)
            if len(typ_set) > 1:
                vals[
                    "virtual_problem"
                ] += f" Reads taken on {dt} have differing read types."

    covered_primary_bill = None
    enlarged = True

    while enlarged:
        enlarged = False
        covered_bills = OrderedDict(
            (b.id, b)
            for b in sess.query(GBill)
            .filter(
                GBill.g_supply == g_supply,
                GBill.start_date <= vals["covered_finish"],
                GBill.finish_date >= vals["covered_start"],
            )
            .order_by(GBill.issue_date.desc(), GBill.start_date)
        )

        num_covered = None
        while num_covered != len(covered_bills):
            num_covered = len(covered_bills)
            for a, b in combinations(tuple(covered_bills.values()), 2):
                if all(
                    (
                        a.start_date == b.start_date,
                        a.finish_date == b.finish_date,
                        a.kwh == -1 * b.kwh,
                        a.net == -1 * b.net,
                        a.vat == -1 * b.vat,
                        a.gross == -1 * b.gross,
                    )
                ):
                    for gb_id in a.id, b.id:
                        del covered_bills[gb_id]
                        if gb_id in g_bill_ids:
                            g_bill_ids.remove(gb_id)
                    break

        for covered_bill in covered_bills.values():
            if covered_primary_bill is None and len(covered_bill.g_reads) > 0:
                covered_primary_bill = covered_bill
            if covered_bill.start_date < vals["covered_start"]:
                vals["covered_start"] = covered_bill.start_date
                enlarged = True
                break
            if covered_bill.finish_date > vals["covered_finish"]:
                vals["covered_finish"] = covered_bill.finish_date
                enlarged = True
                break

    if len(covered_bills) == 0:
        return

    for covered_bill in covered_bills.values():
        if covered_bill.id in g_bill_ids:
            g_bill_ids.remove(covered_bill.id)
        vals["covered_bill_ids"].append(covered_bill.id)
        bdown = covered_bill.make_breakdown()
        vals["covered_kwh"] += covered_bill.kwh
        vals["covered_net_gbp"] += covered_bill.net
        vals["covered_vat_gbp"] += covered_bill.vat
        vals["covered_gross_gbp"] += covered_bill.gross
        for title in bill_titles:
            k = "covered_" + title
            v = bdown.get(title)

            if v is not None:
                if isinstance(v, list):
                    if k not in vals:
                        vals[k] = set()
                    vals[k].update(set(v))
                else:
                    try:
                        vals[k] += v
                    except KeyError:
                        vals[k] = v
                    except TypeError:
                        raise BadRequest(
                            f"Problem with bill {g_bill.id} and key {k} and value {v} "
                            f"for existing {vals[k]}"
                        )

            if title in (
                "correction_factor",
                "calorific_value",
                "unit_code",
                "unit_factor",
            ):
                if k not in vals:
                    vals[k] = set()
                for g_read in covered_bill.g_reads:
                    if title in ("unit_code", "unit_factor"):
                        g_unit = g_read.g_unit
                        if title == "unit_code":
                            v = g_unit.code
                        else:
                            v = g_unit.factor
                    else:
                        v = getattr(g_read, title)
                    vals[k].add(v)
    elements = set()
    for g_era in sess.execute(
        select(GEra).where(
            GEra.g_supply == g_supply,
            GEra.start_date <= vals["covered_finish"],
            or_(GEra.finish_date == null(), GEra.finish_date >= vals["covered_start"]),
        )
    ).scalars():
        if g_era.g_contract != g_contract:
            vals[
                "virtual_problem"
            ] += "The contract of the bill is different from the contract of the era."
            continue
        site = (
            sess.query(Site)
            .join(SiteGEra)
            .filter(SiteGEra.is_physical == true(), SiteGEra.g_era == g_era)
            .one()
        )
        site_id = site.id
        vals["site_code"] = site.code
        vals["site_name"] = site.name

        chunk_start = hh_max(vals["covered_start"], g_era.start_date)
        chunk_finish = hh_min(vals["covered_finish"], g_era.finish_date)

        data_source = chellow.gas.engine.GDataSource(
            sess,
            chunk_start,
            chunk_finish,
            forecast_date,
            g_era,
            report_context,
            covered_primary_bill,
        )

        vbf(data_source)

        for k, v in data_source.bill.items():
            vk = "virtual_" + k
            try:
                if isinstance(v, set):
                    vals[vk].update(v)
                else:
                    vals[vk] += v
            except KeyError:
                vals[vk] = v
            except TypeError as detail:
                raise BadRequest(f"For key {vk} and value {v}. {detail}")

            if k.endswith("_gbp"):
                elements.add(k[:-4])

    if g_bill.id not in covered_bills.keys():
        g_bill = covered_bills[sorted(covered_bills.keys())[0]]

    vals["batch"] = g_bill.g_batch.reference
    vals["bill_reference"] = g_bill.reference
    vals["bill_type"] = g_bill.bill_type.code
    vals["bill_start_date"] = g_bill.start_date
    vals["bill_finish_date"] = g_bill.finish_date
    vals["mprn"] = g_supply.mprn
    vals["supply_name"] = g_supply.name

    for i, title in enumerate(titles):
        if title.startswith("difference_"):
            covered_val = float(vals.get(titles[i - 2], 0))
            virtual_val = float(vals.get(titles[i - 1], 0))
            vals[title] = covered_val - virtual_val

    csv_writer.writerow([csv_make_val(vals.get(k)) for k in titles])
    vals["g_bill_id"] = g_bill.id
    vals["g_batch_id"] = g_bill.g_batch.id
    vals["g_supply_id"] = g_supply.id
    vals["site_id"] = site_id
    for element in sorted(elements):
        for key in tuple(vals.keys()):
            if not key.endswith("_gbp"):
                covered_prefix = f"covered_{element}_"
                virtual_prefix = f"virtual_{element}_"
                if key.startswith(covered_prefix):
                    part_name = key[len(covered_prefix) :]
                elif key.startswith(virtual_prefix):
                    part_name = key[len(virtual_prefix) :]
                else:
                    continue
                virtual_part = vals.get(f"virtual_{element}_{part_name}", {0})
                covered_part = vals.get(f"covered_{element}_{part_name}", {0})
                if isinstance(virtual_part, set) and len(virtual_part) == 1:
                    virtual_part = float(next(iter(virtual_part)))
                if isinstance(covered_part, set) and len(covered_part) == 1:
                    covered_part = float(next(iter(covered_part)))

                if isinstance(virtual_part, Number) and isinstance(
                    covered_part, Number
                ):
                    diff = float(covered_part) - float(virtual_part)
                else:
                    diff = 0

                vals[f"difference_{element}_{part_name}"] = diff

    for suffix in (
        "kwh",
        "units_consumed",
    ):
        try:
            covered = float(vals[f"covered_{suffix}"])
            virtual = float(vals[f"virtual_{suffix}"])
            vals[f"difference_{suffix}"] = covered - virtual
        except KeyError:
            vals[f"difference_{suffix}"] = 0

    for prefix in (
        "correction_factor",
        "unit_code",
        "calorific_value",
    ):
        covered = vals.get(f"covered_{prefix}", [0])
        virtual = vals.get(f"virtual_{prefix}", [0])
        if len(covered) == 1 and len(virtual) == 1:
            if covered == virtual:
                diff = 0
            else:
                try:
                    diff = float(next(iter(covered))) - float(next(iter(virtual)))
                except ValueError:
                    diff = False
        else:
            diff = False
        vals[f"difference_{prefix}"] = diff

    ReportRun.w_insert_row(report_run_id, "", titles, vals, {"is_checked": False})


def do_get(sess):
    g_batch_id = g_bill_id = g_contract_id = start_date = finish_date = None

    if "g_batch_id" in request.values:
        g_batch_id = req_int("g_batch_id")
        g_batch = GBatch.get_by_id(g.sess, g_batch_id)
        run_g_contract_id = g_batch.g_contract.id
    elif "g_bill_id" in request.values:
        g_bill_id = req_int("g_bill_id")
        g_bill = GBill.get_by_id(g.sess, g_bill_id)
        run_g_contract_id = g_bill.g_batch.g_contract.id
    elif "g_contract_id" in request.values:
        g_contract_id = req_int("g_contract_id")
        start_date = req_date("start_date")
        finish_date = req_date("finish_date")
        run_g_contract_id = g_contract_id
    else:
        raise BadRequest(
            "The bill check needs a g_batch_id, g_bill_id or g_contract_id."
        )

    report_run = ReportRun.insert(
        sess,
        "g_bill_check",
        g.user,
        "g_bill_check",
        {"g_contract_id": run_g_contract_id},
    )
    sess.commit()

    args = (
        g_batch_id,
        g_bill_id,
        g_contract_id,
        start_date,
        finish_date,
        g.user.id,
        report_run.id,
    )
    threading.Thread(target=content, args=args).start()
    return redirect(f"/report_runs/{report_run.id}", 303)
