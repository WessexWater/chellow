import csv
import sys
import threading
import traceback
from collections import defaultdict
from datetime import datetime as Datetime
from decimal import Decimal
from itertools import combinations
from numbers import Number

from dateutil.relativedelta import relativedelta

from flask import g, redirect, request

from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

from zish import ZishException


from chellow.dloads import open_file
from chellow.e.computer import SupplySource, contract_func
from chellow.models import (
    Batch,
    Bill,
    Contract,
    Element,
    Era,
    Llfc,
    MtcParticipant,
    RSession,
    RegisterRead,
    ReportRun,
    Supply,
    User,
)
from chellow.utils import (
    HH,
    csv_make_val,
    hh_format,
    hh_max,
    hh_min,
    hh_range,
    parse_mpan_core,
    req_date,
    req_int,
    req_str,
    to_utc,
)


def _add_gap_hh(gaps, hh_start, gap_type):
    try:
        hh = gaps[hh_start]
        match (hh, gap_type):
            case ("middle", _):
                pass
            case (_, "middle"):
                gaps[hh_start] = "middle"
            case ("start", "start"):
                pass
            case ("start", "finish"):
                gaps[hh_start] = "start_finish"
            case ("finish", "finish"):
                pass
            case ("finish", "start"):
                gaps[hh_start] = "start_finish"
            case ("start_finish", "finish"):
                pass
            case ("start_finish", "start"):
                pass
            case _:
                raise BadRequest(f"Gap combination ({hh}, {gap_type}) not recognized.")

    except KeyError:
        hh = gaps[hh_start] = gap_type


def _add_gap(caches, gaps, start_date, finish_date):
    hhs = hh_range(caches, start_date, finish_date)
    _add_gap_hh(gaps, hhs[0], "start")
    _add_gap_hh(gaps, hhs[-1] + HH, "finish")
    for hh_start in hhs[1:]:
        _add_gap_hh(gaps, hh_start, "middle")


def find_gaps(gaps):
    if len(gaps) > 0:
        gap_start = None
        for ghh, gtype in sorted(gaps.items()):
            if "finish" in gtype:
                yield gap_start, ghh - HH
            if "start" in gtype:
                gap_start = ghh


def content(
    batch_id,
    bill_id,
    contract_id,
    start_date,
    finish_date,
    user_id,
    mpan_cores,
    fname_additional,
    report_run_id,
):
    caches = {}
    tmp_file = sess = supply_id = None
    forecast_date = to_utc(Datetime.max)

    try:
        with RSession() as sess:
            user = User.get_by_id(sess, user_id)
            tmp_file = open_file(
                f"bill_check_{fname_additional}.csv", user, mode="w", newline=""
            )
            writer = csv.writer(tmp_file, lineterminator="\n")

            bills_q = (
                select(Bill)
                .order_by(Bill.supply_id, Bill.reference)
                .options(
                    joinedload(Bill.supply),
                    subqueryload(Bill.reads).joinedload(RegisterRead.present_type),
                    subqueryload(Bill.reads).joinedload(RegisterRead.previous_type),
                    joinedload(Bill.batch),
                )
            )

            if len(mpan_cores) > 0:
                mpan_cores = list(map(parse_mpan_core, mpan_cores))
                supply_ids = sess.scalars(
                    select(Era.supply_id)
                    .where(
                        or_(
                            Era.imp_mpan_core.in_(mpan_cores),
                            Era.exp_mpan_core.in_(mpan_cores),
                        )
                    )
                    .distinct()
                ).all()

                bills_q = bills_q.join(Supply).where(Supply.id.in_(supply_ids))

            if batch_id is not None:
                batch = Batch.get_by_id(sess, batch_id)
                bills_q = bills_q.where(Bill.batch == batch)
                contract = batch.contract
            elif bill_id is not None:
                bill = Bill.get_by_id(sess, bill_id)
                bills_q = bills_q.where(Bill.id == bill.id)
                contract = bill.batch.contract
            elif contract_id is not None:
                contract = Contract.get_by_id(sess, contract_id)
                bills_q = bills_q.join(Batch).where(
                    Batch.contract == contract,
                    Bill.start_date <= finish_date,
                    Bill.finish_date >= start_date,
                )

            vbf = contract_func(caches, contract, "virtual_bill")
            if vbf is None:
                raise BadRequest(
                    f"The contract {contract.name} doesn't have a function "
                    f"virtual_bill."
                )

            virtual_bill_titles_func = contract_func(
                caches, contract, "virtual_bill_titles"
            )
            if virtual_bill_titles_func is None:
                raise BadRequest(
                    f"The contract {contract.name} doesn't have a function "
                    f"virtual_bill_titles."
                )
            virtual_bill_titles = virtual_bill_titles_func()

            titles = []
            header_titles = [
                "imp_mpan_core",
                "exp_mpan_core",
                "site_code",
                "site_name",
                "period_start",
                "period_finish",
                "actual_net_gbp",
                "virtual_net_gbp",
                "difference_net_gbp",
            ]
            titles.extend(header_titles)
            for t in virtual_bill_titles:
                if t not in ("net-gbp", "vat-gbp", "gross-gbp"):
                    titles.append("actual-" + t)
                    titles.append("virtual-" + t)
                    if t.endswith("-gbp"):
                        titles.append("difference-" + t)

            writer.writerow(titles)

            bill_map = defaultdict(set, {})
            for bill in sess.scalars(bills_q):
                bill_map[bill.supply.id].add(bill.id)

            for supply_id, bill_ids in bill_map.items():
                for data in _process_supply(
                    sess, caches, supply_id, bill_ids, forecast_date, contract, vbf
                ):
                    vals = {}
                    for title in header_titles:
                        vals[title] = data[title]
                    for el_name, el in data["elements"].items():
                        for part_name, part in el["parts"].items():
                            for typ, value in part.items():
                                vals[f"{typ}-{el_name}-{part_name}"] = value

                    writer.writerow(csv_make_val(vals.get(title)) for title in titles)
                    ReportRun.w_insert_row(
                        report_run_id,
                        "",
                        titles,
                        vals,
                        {"is_checked": False},
                        data=data,
                    )
        ReportRun.w_update(report_run_id, "finished")

    except BadRequest as e:
        if supply_id is None:
            prefix = "Problem: "
        else:
            prefix = f"Problem with supply {supply_id}:"
        tmp_file.write(prefix + e.description)
        ReportRun.w_update(report_run_id, "problem")
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + "\n")
        if supply_id is None:
            prefix = "Problem: "
        else:
            prefix = f"Problem with supply {supply_id}:"
        tmp_file.write(prefix + msg)
        ReportRun.w_update(report_run_id, "interrupted")
    finally:
        if tmp_file is not None:
            tmp_file.close()


def do_get(sess):
    return do_post(sess)


def do_post(sess):
    batch_id = bill_id = contract_id = start_date = finish_date = None
    if "mpan_cores" in request.values:
        mpan_cores = req_str("mpan_cores").splitlines()
    else:
        mpan_cores = []

    fname_additional = ""

    if "batch_id" in request.values:
        batch_id = req_int("batch_id")
        batch = Batch.get_by_id(sess, batch_id)
        fname_additional = f"_batch_{batch.reference}"
    elif "bill_id" in request.values:
        bill_id = req_int("bill_id")
        bill = Bill.get_by_id(sess, bill_id)
        fname_additional = "bill_" + str(bill.id)
    elif "contract_id" in request.values:
        contract_id = req_int("contract_id")
        contract = Contract.get_by_id(sess, contract_id)

        start_date = req_date("start_date")
        finish_date = req_date("finish_date")

        s = ["contract", str(contract.id)]
        for dt in (start_date, finish_date):
            s.append(hh_format(dt).replace(" ", "T").replace(":", ""))
        fname_additional = "_".join(s)
    else:
        raise BadRequest(
            "The bill check needs a batch_id, a bill_id or a start_date and "
            "finish_date."
        )

    report_run = ReportRun.insert(
        sess,
        "bill_check",
        g.user,
        fname_additional,
        {},
    )
    sess.commit()

    args = (
        batch_id,
        bill_id,
        contract_id,
        start_date,
        finish_date,
        g.user.id,
        mpan_cores,
        fname_additional,
        report_run.id,
    )
    threading.Thread(target=content, args=args).start()
    return redirect(f"/report_runs/{report_run.id}", 303)


def _get_bill_status(sess, bill_statuses, bill):
    try:
        bill_status = bill_statuses[bill.id]
    except KeyError:
        covered_bills = dict(
            (b.id, b)
            for b in sess.scalars(
                select(Bill)
                .join(Batch)
                .join(Contract)
                .where(
                    Bill.supply == bill.supply,
                    Bill.start_date <= bill.finish_date,
                    Bill.finish_date >= bill.start_date,
                    Contract.market_role == bill.batch.contract.market_role,
                )
                .order_by(Bill.start_date, Bill.issue_date)
            )
        )
        while True:
            to_del = None
            for a, b in combinations(covered_bills.values(), 2):
                if all(
                    (
                        a.start_date == b.start_date,
                        a.finish_date == b.finish_date,
                        a.net == -1 * b.net,
                        a.vat == -1 * b.vat,
                        a.gross == -1 * b.gross,
                    )
                ):
                    to_del = (a.id, b.id)
                    break
            if to_del is None:
                break
            else:
                for k in to_del:
                    del covered_bills[k]
                    bill_statuses[k] = None

        for k, v in covered_bills.items():
            bill_statuses[k] = v

        bill_status = bill_statuses[bill.id]

    return bill_status


def _process_period(
    sess,
    caches,
    supply,
    contract,
    bill_statuses,
    forecast_date,
    vbf,
    period_start,
    period_finish,
):
    actual_elems = {}
    vels = {}
    val_elems = {}
    virtual_bill = {"problem": "", "elements": vels}
    market_role_code = contract.market_role.code

    vals = {
        "supply_id": supply.id,
        "period_start": period_start,
        "period_finish": period_finish,
        "contract_id": contract.id,
        "contract_name": contract.name,
        "market_role_code": contract.market_role.code,
        "elements": val_elems,
        "virtual_net_gbp": 0,
        "actual_net_gbp": 0,
        "actual_bills": [],
        "problem": "",
    }

    for bill in sess.scalars(
        select(Bill)
        .join(Batch)
        .where(
            Bill.supply == supply,
            Bill.start_date <= period_finish,
            Bill.finish_date >= period_start,
            Batch.contract == contract,
        )
    ):
        if _get_bill_status(sess, bill_statuses, bill) is not None:
            actual_bill = {
                "id": bill.id,
                "start_date": bill.start_date,
                "finish_date": bill.finish_date,
                "problem": "",
                "net": bill.net,
                "vat": bill.vat,
                "gross": bill.gross,
                "kwh": bill.kwh,
                "breakdown": bill.breakdown,
                "batch_id": bill.batch_id,
                "batch_reference": bill.batch.reference,
            }

            read_dict = {}
            for read in bill.reads:
                gen_start = read.present_date.replace(hour=0).replace(minute=0)
                gen_finish = gen_start + relativedelta(days=1) - HH
                msn_match = False
                read_msn = read.msn
                for read_era in supply.find_eras(sess, gen_start, gen_finish):
                    if read_msn == read_era.msn:
                        msn_match = True
                        break

                if not msn_match:
                    virtual_bill["problem"] += (
                        f"The MSN {read_msn} of the register read {read.id} "
                        f"doesn't match the MSN of the era."
                    )

                for dt, typ in [
                    (read.present_date, read.present_type),
                    (read.previous_date, read.previous_type),
                ]:
                    key = f"{dt}-{read.msn}"
                    try:
                        if typ != read_dict[key]:
                            virtual_bill[
                                "problem"
                            ] += f" Reads taken on {dt} have differing read types."
                    except KeyError:
                        read_dict[key] = typ

            element_net = sum(el.net for el in bill.elements)
            vals["actual_bills"].append(actual_bill)
            if element_net != bill.net:
                actual_bill["problem"] += (
                    f"The Net GBP total of the elements is {element_net} doesn't "
                    f"match the bill Net GBP value of {bill.net}. "
                )
            if bill.gross != bill.vat + bill.net:
                actual_bill["problem"] += (
                    f"The Gross GBP ({bill.gross}) of the bill isn't equal to "
                    f"the Net GBP ({bill.net}) + VAT GBP ({bill.vat}) of the bill."
                )

            vat_net = Decimal("0.00")
            vat_vat = Decimal("0.00")

            try:
                bd = bill.bd

                if "vat" in bd:
                    for vat_percentage, vat_vals in bd["vat"].items():
                        vat_net += vat_vals["net"]
                        vat_vat += vat_vals["vat"]
            except ZishException as e:
                actual_bill["problem"] += f"Problem parsing the breakdown: {e}"

            if vat_net != bill.net:
                actual_bill["problem"] += (
                    f"The total 'net' {vat_net} in the VAT breakdown doesn't "
                    f"match the 'net' {bill.net} of the bill."
                )
            if vat_vat != bill.vat:
                actual_bill["problem"] += (
                    f"The total VAT {vat_vat} in the VAT breakdown doesn't "
                    f"match the VAT {bill.vat} of the bill."
                )

            if len(actual_bill["problem"]) > 0:
                vals["problem"] += "Bills have problems. "

    for element in sess.scalars(
        select(Element)
        .join(Bill)
        .join(Batch)
        .where(
            Bill.supply == supply,
            Element.start_date <= period_finish,
            Element.finish_date >= period_start,
            Batch.contract == contract,
        )
    ):
        if _get_bill_status(sess, bill_statuses, element.bill) is None:
            continue

        try:
            actual_elem = actual_elems[element.name]
        except KeyError:
            actual_elem = actual_elems[element.name] = {
                "parts": {"gbp": Decimal("0.00")},
                "elements": [],
            }
        parts = actual_elem["parts"]
        actual_elem["elements"].append(
            {
                "id": element.id,
                "start_date": element.start_date,
                "finish_date": element.finish_date,
                "net": element.net,
                "breakdown": element.breakdown,
                "bill": {
                    "id": element.bill.id,
                    "batch": {
                        "id": element.bill.batch.id,
                        "reference": element.bill.batch.reference,
                    },
                },
            }
        )

        parts["gbp"] += element.net
        vals["actual_net_gbp"] += float(element.net)

        for k, v in element.bd.items():
            if isinstance(v, Decimal):
                v = float(v)

            if isinstance(v, list):
                v = set(v)

            try:
                if isinstance(v, set):
                    parts[k].update(v)
                else:
                    parts[k] += v
            except KeyError:
                parts[k] = v
            except TypeError as detail:
                raise BadRequest(
                    f"For key {k} in {element.bd} the value {v} can't be added to "
                    f"the existing value {parts[k]}. {detail}"
                )

    first_era = None
    for era in sess.scalars(
        select(Era)
        .where(
            Era.supply == supply,
            Era.start_date <= period_finish,
            or_(Era.finish_date == null(), Era.finish_date >= period_start),
        )
        .order_by(Era.start_date)
        .distinct()
        .options(
            joinedload(Era.channels),
            joinedload(Era.cop),
            joinedload(Era.dc_contract),
            joinedload(Era.exp_llfc),
            joinedload(Era.exp_llfc).joinedload(Llfc.voltage_level),
            joinedload(Era.exp_supplier_contract),
            joinedload(Era.imp_llfc),
            joinedload(Era.imp_llfc).joinedload(Llfc.voltage_level),
            joinedload(Era.imp_supplier_contract),
            joinedload(Era.mop_contract),
            joinedload(Era.mtc_participant).joinedload(MtcParticipant.meter_type),
            joinedload(Era.pc),
            joinedload(Era.supply).joinedload(Supply.dno),
            joinedload(Era.supply).joinedload(Supply.gsp_group),
            joinedload(Era.supply).joinedload(Supply.source),
        )
    ).unique():
        first_era = era
        chunk_start = hh_max(period_start, era.start_date)
        chunk_finish = hh_min(period_finish, era.finish_date)

        if contract not in (
            era.mop_contract,
            era.dc_contract,
            era.imp_supplier_contract,
            era.exp_supplier_contract,
        ):
            virtual_bill["problem"] += (
                f"From {hh_format(chunk_start)} to {hh_format(chunk_finish)} "
                f"the contract of the era doesn't match the contract of the bill."
            )
            continue

        if contract.market_role.code == "X":
            polarity = contract != era.exp_supplier_contract
        else:
            polarity = era.imp_supplier_contract is not None

        data_source = SupplySource(
            sess,
            chunk_start,
            chunk_finish,
            forecast_date,
            era,
            polarity,
            caches,
            bill=True,
        )
        vbf(data_source)

        match market_role_code:
            case "X":
                vb = data_source.supplier_bill
            case "C":
                vb = data_source.dc_bill
            case "M":
                vb = data_source.mop_bill
            case _:
                raise BadRequest(f"Odd market role {market_role_code}")

        for k, v in vb.items():
            if k.endswith("-gbp") and k not in ("net-gbp", "vat-gbp", "gross-gbp"):
                vel_name = k[:-4]
                try:
                    vel = vels[vel_name]
                except KeyError:
                    vel = vels[vel_name] = {"parts": {}, "elements": []}

                vals["virtual_net_gbp"] += v

        for k, v in vb.items():
            if k == "problem":
                virtual_bill["problem"] += v
            else:
                for vel_name in sorted(vels.keys(), key=len, reverse=True):
                    pref = f"{vel_name}-"
                    if k.startswith(pref):
                        vel = vels[vel_name]["parts"]
                        vel_k = k[len(pref) :]
                        try:
                            if isinstance(vel[vel_k], set):
                                vel[vel_k].update(v)
                            else:
                                vel[vel_k] += v
                        except KeyError:
                            vel[vel_k] = v
                        except TypeError as detail:
                            raise BadRequest(f"For key {vel_k} and value {v}. {detail}")

                        break
    for typ, els in (("virtual", vels), ("actual", actual_elems)):
        for el_k, el in els.items():
            try:
                val_elem = val_elems[el_k]
            except KeyError:
                val_elem = val_elems[el_k] = {}

            for k, v in el["parts"].items():
                try:
                    val_parts = val_elem["parts"]
                except KeyError:
                    val_parts = val_elem["parts"] = {}

                try:
                    val_part = val_parts[k]
                except KeyError:
                    val_part = val_parts[k] = {}

                val_part[typ] = v

            for el in el["elements"]:
                try:
                    elements = val_elem[f"{typ}_elements"]
                except KeyError:
                    elements = val_elem[f"{typ}_elements"] = []

                elements.append(el)

    for elname, val_elem in val_elems.items():
        for part_name, part in val_elem["parts"].items():
            if part_name == "gbp":
                virtual_part = round(part.get("virtual", 0), 2)
                actual_part = part.get("actual", 0)
            else:
                virtual_part = part.get("virtual")
                actual_part = part.get("actual")

            if isinstance(virtual_part, set) and len(virtual_part) == 1:
                virtual_part = next(iter(virtual_part))
            if isinstance(actual_part, set) and len(actual_part) == 1:
                actual_part = next(iter(actual_part))

            if virtual_part is None or actual_part is None:
                diff = None
                passed = "❔"
            elif isinstance(virtual_part, Number) and isinstance(actual_part, Number):
                diff = float(actual_part) - float(virtual_part)
                passed = "✅" if diff == 0 else "❌"
            else:
                diff = None
                passed = "✅" if virtual_part == actual_part else "❌"

            part["difference"] = diff
            part["passed"] = passed

    if first_era is None:
        vals["problem"] += "No eras for this period of the supply. "
        first_era = supply.find_last_era(sess)

    site = first_era.get_physical_site(sess)

    vals["site_id"] = site.id
    vals["site_code"] = site.code
    vals["site_name"] = site.name
    vals["imp_mpan_core"] = first_era.imp_mpan_core
    vals["exp_mpan_core"] = first_era.exp_mpan_core
    vals["difference_net_gbp"] = vals["actual_net_gbp"] - vals["virtual_net_gbp"]
    vals["problem"] += virtual_bill["problem"]

    return vals


def _process_supply(sess, caches, supply_id, bill_ids, forecast_date, contract, vbf):
    gaps = {}
    bill_statuses = {}
    supply = Supply.get_by_id(sess, supply_id)
    market_role_code = contract.market_role.code  # noqa: F841

    # Find seed gaps
    while len(bill_ids) > 0:
        bill_id = list(sorted(bill_ids))[0]
        bill_ids.remove(bill_id)
        bill = Bill.get_by_id(sess, bill_id)
        if _get_bill_status(sess, bill_statuses, bill) is not None:
            _add_gap(caches, gaps, bill.start_date, bill.finish_date)
            for element in sess.scalars(
                select(Element)
                .join(Bill)
                .join(Batch)
                .where(
                    Batch.contract == contract,
                    Bill.supply == supply,
                    Bill.start_date <= bill.finish_date,
                    Bill.finish_date >= bill.start_date,
                )
            ):
                _add_gap(caches, gaps, element.start_date, element.finish_date)

    # Find enlarged gaps
    enlarged = True
    while enlarged:
        enlarged = False
        for gap_start, gap_finish in find_gaps(gaps):
            for element in sess.scalars(
                select(Element)
                .join(Bill)
                .join(Batch)
                .where(
                    Bill.supply == supply,
                    Bill.start_date <= gap_finish,
                    Bill.finish_date >= gap_start,
                    Batch.contract == contract,
                )
            ):
                if _add_gap(caches, gaps, element.start_date, element.finish_date):
                    enlarged = True

    for period_start, period_finish in find_gaps(gaps):
        yield _process_period(
            sess,
            caches,
            supply,
            contract,
            bill_statuses,
            forecast_date,
            vbf,
            period_start,
            period_finish,
        )

        # Avoid long-running transactions
        sess.rollback()
