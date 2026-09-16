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

from odio import create_spreadsheet

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
    DC_MARKET_ROLE_CODES,
    Element,
    Era,
    Llfc,
    MOP_MARKET_ROLE_CODES,
    MtcParticipant,
    Party,
    RSession,
    RegisterRead,
    ReportRun,
    Supply,
    User,
)
from chellow.utils import (
    HH,
    date_format,
    hh_max,
    hh_min,
    hh_range,
    make_val,
    parse_mpan_core,
    req_date,
    req_int,
    req_str,
    to_utc,
)


def write_spreadsheet(fl, compressed, bill_rows, element_rows):
    fl.seek(0)
    fl.truncate()
    with create_spreadsheet(fl, compressed=compressed) as sheet:
        sheet.append_table("bills", bill_rows)
        sheet.append_table("elements", element_rows)


def _add_gap_hh(gaps, element_name, hh_start, gap_type):
    try:
        elgaps = gaps[element_name]
    except KeyError:
        elgaps = gaps[element_name] = {}

    try:
        hh = elgaps[hh_start]
        match (hh, gap_type):
            case ("middle", _):
                pass
            case (_, "middle"):
                elgaps[hh_start] = "middle"
            case ("start", "start"):
                pass
            case ("start", "finish"):
                elgaps[hh_start] = "start_finish"
            case ("finish", "finish"):
                pass
            case ("finish", "start"):
                elgaps[hh_start] = "start_finish"
            case ("start_finish", "finish"):
                pass
            case ("start_finish", "start"):
                pass
            case _:
                raise BadRequest(f"Gap combination ({hh}, {gap_type}) not recognized.")

    except KeyError:
        hh = elgaps[hh_start] = gap_type


def _add_el(caches, gaps, element):
    hhs = hh_range(caches, element.start_date, element.finish_date)
    _add_gap_hh(gaps, element.name, hhs[0], "start")
    _add_gap_hh(gaps, element.name, hhs[-1] + HH, "finish")
    for hh_start in hhs[1:]:
        _add_gap_hh(gaps, element.name, hh_start, "middle")


def find_blocks(blockvals):
    if len(blockvals) > 0:
        block_start = None
        for ghh, gtype in sorted(blockvals.items()):
            if "finish" in gtype:
                yield block_start, ghh - HH
            if "start" in gtype:
                block_start = ghh


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
    bill_rows = []
    element_rows = []

    try:
        with RSession() as sess:
            user = User.get_by_id(sess, user_id)
            tmp_file = open_file(f"bill_check_{fname_additional}.ods", user, mode="wb")

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

            bill_titles = [
                "reference",
                "start_date",
                "finish_date",
                "problem",
                "net",
                "vat",
                "gross",
                "kwh",
                "breakdown",
                "batch_reference",
                "imp_mpan_core",
                "exp_mpan_core",
                "site_code",
                "site_name",
            ]
            bill_rows.append(bill_titles)

            element_titles = []
            element_header_titles = [
                "imp_mpan_core",
                "exp_mpan_core",
                "site_code",
                "site_name",
                "period_start",
                "period_finish",
                "element_name",
            ]
            element_titles.extend(element_header_titles)
            for t in virtual_bill_titles:
                if t not in ("net-gbp", "vat-gbp", "gross-gbp"):
                    element_titles.append("actual-" + t)
                    element_titles.append("virtual-" + t)
                    if t.endswith("-gbp"):
                        element_titles.append("difference-" + t)

            element_rows.append(element_titles)

            bill_map = defaultdict(set, {})
            for bill in sess.scalars(bills_q):
                bill_map[bill.supply.id].add(bill.id)

            for supply_id, bill_ids in bill_map.items():
                data_bills, data_elements = _process_supply(
                    sess, caches, supply_id, bill_ids, forecast_date, contract, vbf
                )
                for data in data_bills:
                    vals = {}

                    for title in bill_titles:
                        vals[title] = data[title]

                    bill_row = [make_val(vals.get(title)) for title in bill_titles]
                    bill_rows.append(bill_row)

                    ReportRun.w_insert_row(
                        report_run_id,
                        "bills",
                        bill_titles,
                        vals,
                        {"is_checked": False},
                        data=data,
                    )

                for data in data_elements:
                    vals = {}

                    for title in element_header_titles:
                        vals[title] = data[title]

                    for part_name, part in data["parts"].items():
                        for typ, value in part.items():
                            vals[f"{typ}-{part_name}"] = value

                    row = [make_val(vals.get(title)) for title in element_titles]
                    element_rows.append(row)

                    ReportRun.w_insert_row(
                        report_run_id,
                        "elements",
                        element_titles,
                        vals,
                        {"is_checked": False},
                        data=data,
                    )

        write_spreadsheet(
            tmp_file,
            True,
            bill_rows,
            element_rows,
        )
        ReportRun.w_update(report_run_id, "finished")

    except BadRequest as e:
        if supply_id is None:
            prefix = "Problem: "
        else:
            prefix = f"Problem with supply {supply_id}:"
        msg = prefix + e.description + traceback.format_exc()
        sys.stderr.write(msg + "\n")
        bill_rows.append(["Problem " + msg])
        write_spreadsheet(tmp_file, True, bill_rows, element_rows)
        if report_run_id is not None:
            ReportRun.w_update(report_run_id, "interrupted")
            ReportRun.w_insert_row(
                report_run_id, "bills", ["problem"], {"problem": msg}, {}
            )
    except BaseException:
        if supply_id is None:
            prefix = "Problem: "
        else:
            prefix = f"Problem with supply {supply_id}:"

        msg = prefix + traceback.format_exc()
        sys.stderr.write(msg + "\n")
        bill_rows.append(["Problem " + msg])
        if tmp_file is None:
            msg = traceback.format_exc()
            ef = open_file("error.txt", None, mode="w")
            ef.write(msg + "\n")
            ef.close()
        else:
            write_spreadsheet(tmp_file, True, bill_rows, element_rows)
        if report_run_id is not None:
            ReportRun.w_update(report_run_id, "interrupted")
            ReportRun.w_insert_row(
                report_run_id, "bills", ["problem"], {"problem": msg}, {}
            )
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
            s.append(date_format(dt).replace(" ", "T").replace(":", ""))
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
                .join(Party)
                .where(
                    Bill.supply == bill.supply,
                    Bill.start_date <= bill.finish_date,
                    Bill.finish_date >= bill.start_date,
                    Party.market_role == bill.batch.contract.party.market_role,
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


def _format_part(name, value):
    if value is None:
        return ""

    if isinstance(value, Number):
        if name in ("kwh", "kvarh") or name.endswith("-kwh"):
            format_str = "{:0,.1f}"
        elif name == "gbp" or name.endswith("-kw"):
            format_str = "{:0,.2f}"
        else:
            format_str = "{}"
        return format_str.format(value)
    elif isinstance(value, (str, bool)):
        return "{}".format(value)
    elif isinstance(value, Datetime):
        return date_format(value)
    else:
        return " | ".join([_format_part(name, v) for v in value])


def _process_period(
    sess,
    caches,
    supply,
    vb_cache,
    contract,
    bill_statuses,
    forecast_date,
    vbf,
    elname,
    period_start,
    period_finish,
):
    virtual_parts = {}
    market_role_code = contract.party.market_role.code

    vals = {
        "supply_id": supply.id,
        "period_start": period_start,
        "period_finish": period_finish,
        "contract_id": contract.id,
        "contract_name": contract.name,
        "market_role_code": market_role_code,
        "element_name": elname,
        "parts": {},
        "actual_elements": [],
        "problem": "",
    }

    actual_parts = {"gbp": Decimal("0.00")}
    for element in sess.scalars(
        select(Element)
        .join(Bill)
        .join(Batch)
        .where(
            Bill.supply == supply,
            Element.start_date <= period_finish,
            Element.finish_date >= period_start,
            Batch.contract == contract,
            Element.name == elname,
        )
    ):
        if _get_bill_status(sess, bill_statuses, element.bill) is None:
            continue

        vals["actual_elements"].append(
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

        actual_parts["gbp"] += element.net

        for k, v in element.bd.items():
            if isinstance(v, Decimal):
                v = float(v)

            if isinstance(v, list):
                v = set(v)

            try:
                if isinstance(v, set):
                    actual_parts[k].update(v)
                else:
                    actual_parts[k] += v
            except KeyError:
                actual_parts[k] = v
            except TypeError as detail:
                raise BadRequest(
                    f"For key {k} in {element.bd} the value {v} can't be added to "
                    f"the existing value {actual_parts[k]}. {detail}"
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
            vals["problem"] += (
                f"From {date_format(chunk_start)} to {date_format(chunk_finish)} "
                f"the contract of the era doesn't match the contract of the bill."
            )
            continue

        if market_role_code == "X":
            polarity = contract != era.exp_supplier_contract
        else:
            polarity = era.imp_supplier_contract is not None

        cache_key = (chunk_start, chunk_finish, era, polarity)
        try:
            vb = vb_cache[cache_key]
        except KeyError:
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
                case v if v in DC_MARKET_ROLE_CODES:
                    vb = data_source.dc_bill
                case v if v in MOP_MARKET_ROLE_CODES:
                    vb = data_source.mop_bill
                case _:
                    raise BadRequest(f"Odd market role {market_role_code}")
            vb_cache[cache_key] = vb

        if "problem" in vb:
            vals["problem"] += vb["problem"]

        if elname in vb["elements"]:
            eldict = vb["elements"][elname]

            for k, v in eldict.items():
                try:
                    if isinstance(virtual_parts[k], set):
                        virtual_parts[k].update(v)
                    else:
                        virtual_parts[k] += v
                except KeyError:
                    virtual_parts[k] = v
                except TypeError as detail:
                    raise BadRequest(f"For key {k} and value {v}. {detail}")

    val_parts = vals["parts"]
    for typ, parts in (("virtual", virtual_parts), ("actual", actual_parts)):
        for k, v in parts.items():
            try:
                val_part = val_parts[k]
            except KeyError:
                val_part = val_parts[k] = {}

            val_part[typ] = v

    for part_name, part in vals["parts"].items():
        if part_name == "gbp":
            virt_part = round(part.get("virtual", 0), 2)
            actual_part = part.get("actual", 0)
        else:
            virt_part = part.get("virtual")
            actual_part = part.get("actual")

        if isinstance(virt_part, set) and len(virt_part) == 1:
            virt_part = next(iter(virt_part))
        if isinstance(actual_part, set) and len(actual_part) == 1:
            actual_part = next(iter(actual_part))

        if virt_part is None or actual_part is None:
            diff = None
        elif isinstance(virt_part, Number) and isinstance(actual_part, Number):
            diff = float(actual_part) - float(virt_part)
        else:
            diff = None

        actual_str = _format_part(part_name, actual_part)
        virt_str = _format_part(part_name, virt_part)
        diff_str = _format_part(part_name, diff)

        if actual_str == "" or virt_str == "":
            passed = "❔"
        else:
            passed = "✅" if virt_str == actual_str else "❌"

        part["actual_str"] = actual_str
        part["virtual_str"] = virt_str
        part["difference_str"] = diff_str
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

    return vals


def _process_supply(sess, caches, supply_id, bill_ids, forecast_date, contract, vbf):
    elblocks = {}
    bill_statuses = {}
    supply = Supply.get_by_id(sess, supply_id)
    market_role_code = contract.party.market_role.code  # noqa: F841
    data_bills = []
    data_elements = []

    # Find seed gaps
    while len(bill_ids) > 0:
        bill_id = list(sorted(bill_ids))[0]
        bill_ids.remove(bill_id)
        bill = Bill.get_by_id(sess, bill_id)
        if _get_bill_status(sess, bill_statuses, bill) is not None:
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
                _add_el(caches, elblocks, element)

            supply = bill.supply
            era = supply.find_last_era(sess)
            site = era.get_physical_site(sess)
            batch = bill.batch
            contract = batch.contract
            problems = []

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
                    problems.append(
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
                            problems.append(
                                f" Reads taken on {dt} have differing read types."
                            )
                    except KeyError:
                        read_dict[key] = typ

            element_net = sum(el.net for el in bill.elements)
            if element_net != bill.net:
                problems.append(
                    f"The Net GBP total of the elements is {element_net} doesn't "
                    f"match the bill Net GBP value of {bill.net}."
                )
            if bill.gross != bill.vat + bill.net:
                problems.append(
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
                problems.append(f"Problem parsing the breakdown: {e}")

            if vat_net != bill.net:
                problems.append(
                    f"The total 'net' {vat_net} in the VAT breakdown doesn't "
                    f"match the 'net' {bill.net} of the bill."
                )
            if vat_vat != bill.vat:
                problems.append(
                    f"The total VAT {vat_vat} in the VAT breakdown doesn't "
                    f"match the VAT {bill.vat} of the bill."
                )

            if len(problems) > 0:
                data_bill = {
                    "id": bill.id,
                    "supply_id": supply.id,
                    "reference": bill.reference,
                    "start_date": bill.start_date,
                    "finish_date": bill.finish_date,
                    "problem": " ".join(problems),
                    "net": bill.net,
                    "vat": bill.vat,
                    "gross": bill.gross,
                    "kwh": bill.kwh,
                    "breakdown": bill.breakdown,
                    "batch_id": batch.id,
                    "batch_reference": bill.batch.reference,
                    "imp_mpan_core": era.imp_mpan_core,
                    "exp_mpan_core": era.exp_mpan_core,
                    "site_id": site.id,
                    "site_code": site.code,
                    "site_name": site.name,
                    "contract_id": contract.id,
                    "contract_name": contract.name,
                    "market_role_code": contract.party.market_role.code,
                }

                data_bills.append(data_bill)

    vb_cache = {}

    # Find enlarged blocks
    for elname, blockvals in elblocks.items():
        enlarged = True
        while enlarged:
            enlarged = False
            for block_start, block_finish in find_blocks(blockvals):
                for element in sess.scalars(
                    select(Element)
                    .join(Bill)
                    .join(Batch)
                    .where(
                        Bill.supply == supply,
                        Bill.start_date <= block_finish,
                        Bill.finish_date >= block_start,
                        Batch.contract == contract,
                        Element.name == elname,
                    )
                ):
                    if _add_el(caches, elblocks, element):
                        enlarged = True

        for period_start, period_finish in find_blocks(blockvals):
            data_element = _process_period(
                sess,
                caches,
                supply,
                vb_cache,
                contract,
                bill_statuses,
                forecast_date,
                vbf,
                elname,
                period_start,
                period_finish,
            )
            data_elements.append(data_element)

            # Avoid long-running transactions
            sess.rollback()

    return data_bills, data_elements
