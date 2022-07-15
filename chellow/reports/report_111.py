import csv
import os
import sys
import threading
import traceback
from collections import OrderedDict, defaultdict
from datetime import datetime as Datetime
from decimal import Decimal
from itertools import combinations

from dateutil.relativedelta import relativedelta

from flask import g, request

from sqlalchemy import or_
from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.sql.expression import null, true

from werkzeug.exceptions import BadRequest

from zish import ZishLocationException, loads

import chellow.dloads
from chellow.e.computer import contract_func
from chellow.models import (
    Batch,
    Bill,
    Contract,
    Era,
    Llfc,
    MarketRole,
    MtcParticipant,
    RegisterRead,
    ReportRun,
    Session,
    Site,
    SiteEra,
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
from chellow.views import chellow_redirect


def add_gap(caches, gaps, elem, start_date, finish_date, is_virtual, gbp):
    try:
        elgap = gaps[elem]
    except KeyError:
        elgap = gaps[elem] = {}

    hhs = hh_range(caches, start_date, finish_date)
    hhgbp = 0 if gbp is None else gbp / len(hhs)

    for hh_start in hhs:
        try:
            hhgap = elgap[hh_start]
        except KeyError:
            hhgap = elgap[hh_start] = {
                "has_covered": False,
                "has_virtual": False,
                "gbp": 0,
            }

        if is_virtual:
            hhgap["has_virtual"] = True
            hhgap["gbp"] = hhgbp
        else:
            hhgap["has_covered"] = True


def find_elements(bill):
    try:
        keys = [k for k in loads(bill.breakdown).keys() if k.endswith("-gbp")]
        return set(k[:-4] for k in keys)
    except ZishLocationException as e:
        raise BadRequest(
            f"Can't parse the breakdown for bill id {bill.id} attached to batch id "
            f"{bill.batch.id}: {e}"
        )


def content(
    batch_id,
    bill_id,
    contract_id,
    start_date,
    finish_date,
    user_id,
    mpan_cores,
    fname_additional,
):
    caches = {}
    tmp_file = sess = supply_id = report_run = None
    forecast_date = to_utc(Datetime.max)

    try:
        sess = Session()
        user = User.get_by_id(sess, user_id)
        running_name, finished_name = chellow.dloads.make_names(
            f"bill_check_{fname_additional}.csv", user
        )
        tmp_file = open(running_name, mode="w", newline="")
        writer = csv.writer(tmp_file, lineterminator="\n")

        report_run = ReportRun.insert(sess, "bill_check", user, fname_additional, {})

        bills = (
            sess.query(Bill)
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
            supply_ids = [
                i[0]
                for i in sess.query(Era.supply_id)
                .filter(
                    or_(
                        Era.imp_mpan_core.in_(mpan_cores),
                        Era.exp_mpan_core.in_(mpan_cores),
                    )
                )
                .distinct()
            ]
            bills = bills.join(Supply).filter(Supply.id.in_(supply_ids))

        if batch_id is not None:
            batch = Batch.get_by_id(sess, batch_id)
            bills = bills.filter(Bill.batch == batch)
            contract = batch.contract
        elif bill_id is not None:
            bill = Bill.get_by_id(sess, bill_id)
            bills = bills.filter(Bill.id == bill.id)
            contract = bill.batch.contract
        elif contract_id is not None:
            contract = Contract.get_by_id(sess, contract_id)
            bills = bills.join(Batch).filter(
                Batch.contract == contract,
                Bill.start_date <= finish_date,
                Bill.finish_date >= start_date,
            )

        vbf = contract_func(caches, contract, "virtual_bill")
        if vbf is None:
            raise BadRequest(
                f"The contract {contract.name} doesn't have a function virtual_bill."
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

        titles = [
            "batch",
            "bill-reference",
            "bill-type",
            "bill-kwh",
            "bill-net-gbp",
            "bill-vat-gbp",
            "bill-start-date",
            "bill-finish-date",
            "imp-mpan-core",
            "exp-mpan-core",
            "site-code",
            "site-name",
            "covered-from",
            "covered-to",
            "covered-bills",
            "metered-kwh",
        ]
        for t in virtual_bill_titles:
            titles.append("covered-" + t)
            titles.append("virtual-" + t)
            if t.endswith("-gbp"):
                titles.append("difference-" + t)

        writer.writerow(titles)

        bill_map = defaultdict(set, {})
        for bill in bills:
            bill_map[bill.supply.id].add(bill.id)

        for supply_id, bill_ids in bill_map.items():
            _process_supply(
                sess,
                caches,
                supply_id,
                bill_ids,
                forecast_date,
                contract,
                vbf,
                virtual_bill_titles,
                writer,
                titles,
                report_run,
            )

        report_run.update("finished")
        sess.commit()

    except BadRequest as e:
        if report_run is not None:
            report_run.update("problem")
        if supply_id is None:
            prefix = "Problem: "
        else:
            prefix = f"Problem with supply {supply_id}:"
        tmp_file.write(prefix + e.description)
    except BaseException:
        if report_run is not None:
            report_run.update("interrupted")
        if supply_id is None:
            prefix = "Problem: "
        else:
            prefix = f"Problem with supply {supply_id}:"
        msg = traceback.format_exc()
        sys.stderr.write(msg + "\n")
        tmp_file.write(prefix + msg)
    finally:
        if sess is not None:
            sess.close()
        if tmp_file is not None:
            tmp_file.close()
            os.rename(running_name, finished_name)


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

    args = (
        batch_id,
        bill_id,
        contract_id,
        start_date,
        finish_date,
        g.user.id,
        mpan_cores,
        fname_additional,
    )
    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)


def _process_supply(
    sess,
    caches,
    supply_id,
    bill_ids,
    forecast_date,
    contract,
    vbf,
    virtual_bill_titles,
    writer,
    titles,
    report_run,
):
    gaps = {}
    data_sources = {}
    market_role_code = contract.market_role.code

    while len(bill_ids) > 0:
        bill_id = list(sorted(bill_ids))[0]
        bill_ids.remove(bill_id)
        bill = (
            sess.query(Bill)
            .filter(Bill.id == bill_id)
            .options(
                joinedload(Bill.batch),
                joinedload(Bill.bill_type),
                joinedload(Bill.reads),
                joinedload(Bill.supply),
                joinedload(Bill.reads).joinedload(RegisterRead.present_type),
                joinedload(Bill.reads).joinedload(RegisterRead.previous_type),
            )
            .one()
        )
        virtual_bill = {"problem": ""}
        supply = bill.supply

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
                    f"The MSN {read_msn} of the register read {read.id} doesn't match "
                    f"the MSN of the era."
                )

            for dt, typ in [
                (read.present_date, read.present_type),
                (read.previous_date, read.previous_type),
            ]:
                key = str(dt) + "-" + read.msn
                try:
                    if typ != read_dict[key]:
                        virtual_bill[
                            "problem"
                        ] += f" Reads taken on {dt} have differing read types."
                except KeyError:
                    read_dict[key] = typ

        bill_start = bill.start_date
        bill_finish = bill.finish_date

        covered_start = bill_start
        covered_finish = bill_start
        covered_bdown = {"sum-msp-kwh": 0, "net-gbp": 0, "vat-gbp": 0}

        vb_elems = set()
        enlarged = True

        while enlarged:
            enlarged = False
            covered_elems = find_elements(bill)
            covered_bills = OrderedDict(
                (b.id, b)
                for b in sess.query(Bill)
                .join(Batch)
                .join(Contract)
                .join(MarketRole)
                .filter(
                    Bill.supply == supply,
                    Bill.start_date <= covered_finish,
                    Bill.finish_date >= covered_start,
                    MarketRole.code == market_role_code,
                )
                .order_by(Bill.start_date, Bill.issue_date)
            )
            while True:
                to_del = None
                for a, b in combinations(covered_bills.values(), 2):
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
                        to_del = (a.id, b.id)
                        break
                if to_del is None:
                    break
                else:
                    for k in to_del:
                        del covered_bills[k]
                        bill_ids.discard(k)

            for k, covered_bill in tuple(covered_bills.items()):
                elems = find_elements(covered_bill)
                if elems.isdisjoint(covered_elems):
                    if k != bill.id:
                        del covered_bills[k]
                        continue
                else:
                    covered_elems.update(elems)

                if covered_bill.start_date < covered_start:
                    covered_start = covered_bill.start_date
                    enlarged = True
                    break

                if covered_bill.finish_date > covered_finish:
                    covered_finish = covered_bill.finish_date
                    enlarged = True
                    break

        if len(covered_bills) == 0:
            continue

        primary_covered_bill = None
        for covered_bill in covered_bills.values():
            bill_ids.discard(covered_bill.id)
            covered_bdown["net-gbp"] += float(covered_bill.net)
            covered_bdown["vat-gbp"] += float(covered_bill.vat)
            covered_bdown["sum-msp-kwh"] += float(covered_bill.kwh)
            for k, v in loads(covered_bill.breakdown).items():
                if k in ("raw_lines", "raw-lines"):
                    continue

                if isinstance(v, list):
                    try:
                        covered_bdown[k].update(set(v))
                    except KeyError:
                        covered_bdown[k] = set(v)
                    except AttributeError as e:
                        raise BadRequest(
                            f"For key {k} in {[b.id for b in covered_bills.values()]} "
                            f"the value {v} can't be added to the existing value "
                            f"{covered_bdown[k]}. {e}"
                        )
                else:
                    if isinstance(v, Decimal):
                        v = float(v)
                    try:
                        covered_bdown[k] += v
                    except KeyError:
                        covered_bdown[k] = v
                    except TypeError as detail:
                        raise BadRequest(
                            f"For key {k} in {[b.id for b in covered_bills.values()]} "
                            f"the value {v} can't be added to the existing value "
                            f"{covered_bdown[k]}. {detail}"
                        )

                    if k.endswith("-gbp"):
                        elem = k[:-4]
                        covered_elems.add(elem)
                        add_gap(
                            caches,
                            gaps,
                            elem,
                            covered_bill.start_date,
                            covered_bill.finish_date,
                            False,
                            v,
                        )

            if primary_covered_bill is None or (
                (covered_bill.finish_date - covered_bill.start_date)
                > (primary_covered_bill.finish_date - primary_covered_bill.start_date)
            ):
                primary_covered_bill = covered_bill

        metered_kwh = 0
        for era in (
            sess.query(Era)
            .filter(
                Era.supply == supply,
                Era.start_date <= covered_finish,
                or_(Era.finish_date == null(), Era.finish_date >= covered_start),
            )
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
        ):

            chunk_start = hh_max(covered_start, era.start_date)
            chunk_finish = hh_min(covered_finish, era.finish_date)

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

            try:
                ds_key = (
                    chunk_start,
                    chunk_finish,
                    forecast_date,
                    era.id,
                    polarity,
                    primary_covered_bill.id,
                )
                data_source = data_sources[ds_key]
            except KeyError:
                data_source = data_sources[ds_key] = chellow.e.computer.SupplySource(
                    sess,
                    chunk_start,
                    chunk_finish,
                    forecast_date,
                    era,
                    polarity,
                    caches,
                    primary_covered_bill,
                )
                vbf(data_source)

            if data_source.measurement_type == "hh":
                metered_kwh += sum(h["msp-kwh"] for h in data_source.hh_data)
            else:
                ds = chellow.e.computer.SupplySource(
                    sess,
                    chunk_start,
                    chunk_finish,
                    forecast_date,
                    era,
                    polarity,
                    caches,
                )
                metered_kwh += sum(h["msp-kwh"] for h in ds.hh_data)

            if market_role_code == "X":
                vb = data_source.supplier_bill
                vb_hhs = data_source.supplier_bill_hhs
            elif market_role_code == "C":
                vb = data_source.dc_bill
                vb_hhs = data_source.dc_bill_hhs
            elif market_role_code == "M":
                vb = data_source.mop_bill
                vb_hhs = data_source.mop_bill_hhs
            else:
                raise BadRequest("Odd market role.")

            for k, v in vb.items():
                try:
                    if isinstance(v, set):
                        virtual_bill[k].update(v)
                    else:
                        virtual_bill[k] += v
                except KeyError:
                    virtual_bill[k] = v
                except TypeError as detail:
                    raise BadRequest(f"For key {k} and value {v}. {detail}")

            for dt, bl in vb_hhs.items():
                for k, v in bl.items():
                    if all((k.endswith("-gbp"), k != "net-gbp", v != 0)):
                        add_gap(caches, gaps, k[:-4], dt, dt, True, v)

            for k in virtual_bill.keys():
                if k.endswith("-gbp"):
                    vb_elems.add(k[:-4])

        long_map = {}
        vb_keys = set(virtual_bill.keys())
        for elem in sorted(vb_elems, key=len, reverse=True):
            els = long_map[elem] = set()
            for k in tuple(vb_keys):
                if k.startswith(elem + "-"):
                    els.add(k)
                    vb_keys.remove(k)

        for elem in vb_elems.difference(covered_elems):
            for k in long_map[elem]:
                del virtual_bill[k]

        try:
            del virtual_bill["net-gbp"]
        except KeyError:
            pass

        virtual_bill["net-gbp"] = sum(
            v for k, v in virtual_bill.items() if k.endswith("-gbp")
        )

        era = supply.find_era_at(sess, bill_finish)
        if era is None:
            imp_mpan_core = exp_mpan_core = None
            site_code = site_name = None
            virtual_bill["problem"] += "This bill finishes before or after the supply. "
        else:
            imp_mpan_core = era.imp_mpan_core
            exp_mpan_core = era.exp_mpan_core

            site = (
                sess.query(Site)
                .join(SiteEra)
                .filter(SiteEra.is_physical == true(), SiteEra.era == era)
                .one()
            )
            site_code = site.code
            site_name = site.name

        # Find bill to use for header data
        if bill.id not in covered_bills:
            for cbill in covered_bills.values():
                if bill.batch == cbill.batch:
                    bill = cbill

        values = {
            "batch": bill.batch.reference,
            "bill-reference": bill.reference,
            "bill-type": bill.bill_type.code,
            "bill-kwh": bill.kwh,
            "bill-net-gbp": bill.net,
            "bill-vat-gbp": bill.vat,
            "bill-start-date": bill_start,
            "bill-finish-date": bill_finish,
            "imp-mpan-core": imp_mpan_core,
            "exp-mpan-core": exp_mpan_core,
            "site-code": site_code,
            "site-name": site_name,
            "covered-from": covered_start,
            "covered-to": covered_finish,
            "covered-bills": sorted(covered_bills.keys()),
            "metered-kwh": metered_kwh,
        }
        for title in virtual_bill_titles:
            try:
                cov_val = covered_bdown[title]
                del covered_bdown[title]
            except KeyError:
                cov_val = None

            values[f"covered-{title}"] = cov_val

            try:
                virt_val = virtual_bill[title]
                del virtual_bill[title]
            except KeyError:
                virt_val = None

            values[f"virtual-{title}"] = virt_val

            if title.endswith("-gbp"):
                if isinstance(virt_val, (int, float, Decimal)):
                    if isinstance(cov_val, (int, float, Decimal)):
                        diff_val = float(cov_val) - float(virt_val)
                    else:
                        diff_val = 0 - float(virt_val)
                else:
                    diff_val = 0

                values[f"difference-{title}"] = diff_val

        report_run_titles = list(titles)
        for title in sorted(virtual_bill.keys()):
            virt_val = virtual_bill[title]
            virt_title = f"virtual-{title}"
            values[virt_title] = virt_val
            report_run_titles.append(virt_title)
            if title in covered_bdown:
                cov_title = f"covered-{title}"
                cov_val = covered_bdown[title]
                values[cov_title] = cov_val
                report_run_titles.append(cov_title)
                if title.endswith("-gbp"):
                    if isinstance(virt_val, (int, float, Decimal)):
                        if isinstance(cov_val, (int, float, Decimal)):
                            diff_val = float(cov_val) - float(virt_val)
                        else:
                            diff_val = 0 - float(virt_val)
                    else:
                        diff_val = 0

                    values[f"difference-{title}"] = diff_val

                    t = "difference-tpr-gbp"
                    try:
                        values[t] += diff_val
                    except KeyError:
                        values[t] = diff_val
                        report_run_titles.append(t)

        csv_row = []
        for t in titles:
            v = values[t]
            if t == "covered-bills":
                val = " | ".join(str(b) for b in v)
            else:
                val = csv_make_val(v)

            csv_row.append(val)

        for t in report_run_titles:
            if t not in titles:
                csv_row.append(t)
                csv_row.append(csv_make_val(values[t]))

        writer.writerow(csv_row)

        values["bill_id"] = bill.id
        values["batch_id"] = bill.batch.id
        values["supply_id"] = supply.id
        values["site_id"] = None if site_code is None else site.id
        report_run.insert_row(
            sess, "", report_run_titles, values, {"is_checked": False}
        )

        for bill in sess.query(Bill).filter(
            Bill.supply == supply,
            Bill.start_date <= covered_finish,
            Bill.finish_date >= covered_start,
        ):

            for k, v in loads(bill.breakdown).items():
                if k.endswith("-gbp"):
                    add_gap(
                        caches,
                        gaps,
                        k[:-4],
                        bill.start_date,
                        bill.finish_date,
                        False,
                        v,
                    )

        # Avoid long-running transactions
        sess.commit()

    clumps = []
    for element, elgap in sorted(gaps.items()):
        for start_date, hhgap in sorted(elgap.items()):
            if hhgap["has_virtual"] and not hhgap["has_covered"]:

                if len(clumps) == 0 or not all(
                    (
                        clumps[-1]["element"] == element,
                        clumps[-1]["finish_date"] + HH == start_date,
                    )
                ):
                    clumps.append(
                        {
                            "element": element,
                            "start_date": start_date,
                            "finish_date": start_date,
                            "gbp": hhgap["gbp"],
                        }
                    )
                else:
                    clumps[-1]["finish_date"] = start_date

    for i, clump in enumerate(clumps):
        vals = {}
        for title in titles:
            if title.startswith("difference-") and title.endswith("-gbp"):
                vals[title] = 0
            else:
                vals[title] = None

        vals["covered-problem"] = "_".join(
            (
                "missing",
                clump["element"],
                "supplyid",
                str(supply.id),
                "from",
                hh_format(clump["start_date"]),
            )
        )
        vals["imp-mpan-core"] = imp_mpan_core
        vals["exp-mpan-core"] = exp_mpan_core
        vals["batch"] = "missing_bill"
        vals["bill-start-date"] = hh_format(clump["start_date"])
        vals["bill-finish-date"] = hh_format(clump["finish_date"])
        vals["difference-net-gbp"] = clump["gbp"]
        writer.writerow(csv_make_val(vals[title]) for title in titles)

        vals["bill_id"] = None
        vals["batch_id"] = None
        vals["supply_id"] = supply.id
        vals["site_id"] = None if site_code is None else site.id

        report_run.insert_row(sess, "", titles, vals, {"is_checked": False})

    # Avoid long-running transactions
    sess.commit()
