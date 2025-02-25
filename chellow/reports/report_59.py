import sys
import threading
import traceback
from collections import defaultdict

from dateutil.relativedelta import relativedelta

from flask import flash, g, make_response, redirect, render_template, request

import odio

from sqlalchemy import or_, select, true
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.e.computer import contract_func, forecast_date
from chellow.e.scenario import make_calcs, make_site_deltas, scenario_fill_cache
from chellow.models import (
    Bill,
    Contract,
    Era,
    MeasurementRequirement,
    RSession,
    Scenario,
    Site,
    SiteEra,
    Source,
    Ssc,
    Supply,
    Tpr,
    User,
)
from chellow.utils import (
    HH,
    c_months_u,
    ct_datetime,
    ct_datetime_now,
    hh_format,
    hh_min,
    hh_range,
    make_val,
    parse_mpan_core,
    req_bool,
    req_hh_date,
    req_int,
    req_str,
    to_ct,
    to_utc,
    utc_datetime_now,
)


CATEGORY_ORDER = {None: 0, "unmetered": 1, "nhh": 2, "amr": 3, "hh": 4}


def write_spreadsheet(fl, compressed, site_rows, supply_rows, era_rows, read_rows):
    fl.seek(0)
    fl.truncate()
    with odio.create_spreadsheet(fl, "1.2", compressed=compressed) as f:
        f.append_table("Site Level", site_rows)
        f.append_table("Supply Level", supply_rows)
        f.append_table("Era Level", era_rows)
        f.append_table("Normal Reads", read_rows)


def make_bill_row(titles, bill):
    return [bill.get(t) for t in titles]


def _add_bills(month_data, bills, chunk_start, chunk_finish):
    for bill in bills:
        bill_role_code = bill.batch.contract.market_role.code
        bill_start = bill.start_date
        bill_finish = bill.finish_date
        bill_duration = (bill_finish - bill_start).total_seconds() + (30 * 60)
        overlap_duration = (
            min(bill_finish, chunk_finish) - max(bill_start, chunk_start)
        ).total_seconds() + (30 * 60)
        proportion = overlap_duration / bill_duration
        bill_prop_kwh = proportion * float(bill.kwh)
        bill_prop_net_gbp = proportion * float(bill.net)
        bill_prop_vat_gbp = proportion * float(bill.vat)
        bill_prop_gross_gbp = proportion * float(bill.gross)
        if bill_role_code == "X":
            role_name = "supplier"
        elif bill_role_code == "C":
            role_name = "dc"
        elif bill_role_code == "M":
            role_name = "mop"
        else:
            raise BadRequest("Role code not recognized.")

        month_data["billed-import-kwh"] += bill_prop_kwh
        month_data["billed-import-net-gbp"] += bill_prop_net_gbp
        month_data[f"billed-import-{role_name}-kwh"] += bill_prop_kwh
        month_data[f"billed-import-{role_name}-net-gbp"] += bill_prop_net_gbp
        month_data[f"billed-import-{role_name}-vat-gbp"] += bill_prop_vat_gbp
        month_data[f"billed-import-{role_name}-gross-gbp"] += bill_prop_gross_gbp


def _process_site(
    sess,
    report_context,
    forecast_from,
    start_date,
    finish_date,
    site,
    scenario_props,
    supply_ids,
    now,
    summary_titles,
    title_dict,
    era_titles,
    era_rows,
    supply_titles,
    supply_rows,
    site_rows,
    data_source_bill,
):
    scenario_hh = scenario_props.get("hh_data", {})
    era_maps = scenario_props.get("era_maps", {})

    site_deltas = make_site_deltas(
        sess, report_context, site, scenario_hh, forecast_from, supply_ids
    )

    calcs, site_gen_types = make_calcs(
        sess,
        site,
        start_date,
        finish_date,
        supply_ids,
        site_deltas,
        forecast_from,
        report_context,
        era_maps,
        data_source_bill,
    )

    site_category = None
    site_sources = set()
    normal_reads = set()
    site_data = defaultdict(int)
    supplies_data = {}
    for order, imp_mpan_core, exp_mpan_core, imp_ss, exp_ss in sorted(calcs, key=str):
        main_ss = exp_ss if imp_ss is None else imp_ss

        vals = {
            "creation-date": now,
            "start-date": main_ss.start_date,
            "finish-date": main_ss.finish_date,
            "site-code": site.code,
            "site-name": site.name,
        }
        for sname in (
            "import-grid",
            "export-grid",
            "import-gen",
            "export-gen",
            "import-3rd-party",
            "export-3rd-party",
            "msp",
            "used",
            "used-3rd-party",
        ):
            for xname in ("kwh", "net-gbp"):
                vals[f"{sname}-{xname}"] = 0
        for suf in ("kwh", "net-gbp", "vat-gbp", "gross-gbp"):
            vals[f"billed-import-{suf}"] = 0

        if imp_mpan_core == "displaced":
            try:
                supply_data = supplies_data["displaced"]
            except KeyError:
                supply_data = supplies_data[-1] = defaultdict(
                    int,
                    {
                        "creation-date": now,
                        "start-date": main_ss.start_date,
                        "finish-date": main_ss.finish_date,
                        "imp-mpan-core": "displaced",
                        "site-code": site.code,
                        "site-name": site.name,
                        "associated-site-codes": set(),
                        "source": "displaced",
                        "supply-name": "displaced",
                    },
                )

            vals["billed-import-supplier-net-gbp"] = None
            vals["billed-import-supplier-vat-gbp"] = None
            vals["billed-import-supplier-gross-gbp"] = None
            vals["billed-import-dc-net-gbp"] = None
            vals["billed-import-dc-vat-gbp"] = None
            vals["billed-import-dc-gross-gbp"] = None
            vals["billed-import-mop-net-gbp"] = None
            vals["billed-import-mop-vat-gbp"] = None
            vals["billed-import-mop-gross-gbp"] = None

            vals["used-kwh"] = vals["displaced-kwh"] = sum(
                hh["msp-kwh"] for hh in imp_ss.hh_data
            )

            disp_supplier_bill = imp_ss.supplier_bill

            gbp = disp_supplier_bill.get("net-gbp", 0)

            vals["used-net-gbp"] = vals["displaced-net-gbp"] = gbp

            vals["imp-supplier-contract"] = imp_ss.supplier_contract.name
            vals["metering-type"] = imp_ss.era.meter_category
            vals["source"] = "displaced"

            for t in title_dict["imp-supplier"]:
                try:
                    vals[t] = disp_supplier_bill[t]
                except KeyError:
                    pass

        else:
            source_code = main_ss.source_code
            supply = main_ss.supply

            try:
                supply_data = supplies_data[supply.id]
            except KeyError:
                supply_data = supplies_data[supply.id] = defaultdict(
                    int,
                    {
                        "creation-date": now,
                        "start-date": main_ss.start_date,
                        "finish-date": main_ss.finish_date,
                        "site-code": site.code,
                        "site-name": site.name,
                        "associated-site-codes": set(),
                    },
                )

            site_sources.add(source_code)

            for suf in ("net-gbp", "vat-gbp", "gross-gbp"):
                vals[f"billed-import-supplier-{suf}"] = 0
                vals[f"billed-import-dc-{suf}"] = 0
                vals[f"billed-import-mop-{suf}"] = 0

            if imp_ss is None:
                imp_bad_hhs = imp_bad_kwh = imp_supplier_contract_name = None
            else:
                imp_supplier_contract = imp_ss.supplier_contract
                imp_supplier_bill = imp_ss.supplier_bill
                if imp_supplier_contract is None:
                    imp_supplier_contract_name = None
                else:
                    imp_supplier_contract_name = imp_supplier_contract.name
                imp_bad_hhs = imp_bad_kwh = imp_md_kw = imp_md_kva = 0
                for hh in imp_ss.hh_data:
                    imp_md_kw = max(imp_md_kw, hh["msp-kw"])
                    imp_md_kva = max(imp_md_kva, hh["msp-kva"])
                    if hh["status"] != "A":
                        imp_bad_hhs += 1
                        imp_bad_kwh += hh["msp-kwh"]

                supply_data["imp-non-actual-hhs"] += imp_bad_hhs
                supply_data["imp-non-actual-kwh"] += imp_bad_kwh
                supply_data["imp-md-kw"] += imp_md_kw
                supply_data["imp-md-kva"] += imp_md_kva

                for t in title_dict["imp-supplier"]:
                    try:
                        vals[f"imp-supplier-{t}"] = imp_supplier_bill[t]
                    except KeyError:
                        pass

                for n in imp_ss.normal_reads:
                    normal_reads.add((imp_mpan_core, n))

                kwh = sum(hh["msp-kwh"] for hh in imp_ss.hh_data)

                gbp = imp_supplier_bill.get("net-gbp", 0)

                if source_code in ("grid", "gen-grid"):
                    vals["import-grid-net-gbp"] += gbp
                    vals["import-grid-kwh"] += kwh
                    vals["used-net-gbp"] += gbp
                    vals["used-kwh"] += kwh
                    if source_code == "gen-grid":
                        vals["export-gen-kwh"] += kwh
                elif source_code == "3rd-party":
                    vals["import-3rd-party-net-gbp"] += gbp
                    vals["import-3rd-party-kwh"] += kwh
                    vals["used-3rd-party-net-gbp"] += gbp
                    vals["used-3rd-party-kwh"] += kwh
                    vals["used-net-gbp"] += gbp
                    vals["used-kwh"] += kwh
                elif source_code == "3rd-party-reverse":
                    vals["export-3rd-party-net-gbp"] += gbp
                    vals["export-3rd-party-kwh"] += kwh
                    vals["used-3rd-party-net-gbp"] -= gbp
                    vals["used-3rd-party-kwh"] -= kwh
                    vals["used-net-gbp"] -= gbp
                    vals["used-kwh"] -= kwh
                elif source_code == "gen":
                    vals["import-gen-kwh"] += kwh

            if exp_ss is None:
                exp_bad_hhs = exp_bad_kwh = exp_supplier_contract_name = None
            else:
                exp_supplier_contract = exp_ss.supplier_contract
                exp_supplier_bill = exp_ss.supplier_bill
                if exp_supplier_contract is None:
                    exp_supplier_contract_name = ""
                else:
                    exp_supplier_contract_name = exp_supplier_contract.name
                exp_bad_hhs = exp_bad_kwh = exp_md_kw = exp_md_kva = 0
                for hh in exp_ss.hh_data:
                    exp_md_kw = max(exp_md_kw, hh["msp-kw"])
                    exp_md_kva = max(exp_md_kva, hh["msp-kva"])
                    if hh["status"] != "A":
                        exp_bad_hhs += 1
                        exp_bad_kwh += hh["msp-kwh"]

                supply_data["exp-non-actual-hhs"] += exp_bad_hhs
                supply_data["exp-non-actual-kwh"] += exp_bad_kwh
                supply_data["exp-md-kw"] += exp_md_kw
                supply_data["exp-md-kva"] += exp_md_kva

                for t in title_dict["exp-supplier"]:
                    try:
                        vals[f"exp-supplier-{t}"] = exp_supplier_bill[t]
                    except KeyError:
                        pass

                kwh = sum(hh["msp-kwh"] for hh in exp_ss.hh_data)
                gbp = exp_supplier_bill.get("net-gbp", 0)

                if source_code in ("net", "gen-net"):
                    vals["export-grid-net-gbp"] += gbp
                    vals["export-grid-net-kwh"] += kwh
                    if source_code == "gen-net":
                        vals["import-gen-kwh"] += kwh

                elif source_code == "3rd-party":
                    vals["export-3rd-party-net-gbp"] += gbp
                    vals["export-3rd-party-kwh"] += kwh
                    vals["used-3rd-party-net-gbp"] -= gbp
                    vals["used-3rd-party-kwh"] -= kwh
                    vals["used-net-gbp"] -= gbp
                    vals["used-kwh"] -= kwh
                elif source_code == "3rd-party-reverse":
                    vals["import-3rd-party-net-gbp"] += gbp
                    vals["import-3rd-party-kwh"] += kwh
                    vals["used-3rd-party-net-gbp"] += gbp
                    vals["used-3rd-party-kwh"] += kwh
                    vals["used-net-gbp"] += gbp
                    vals["used-kwh"] += kwh
                elif source_code == "gen":
                    vals["export-gen-kwh"] += kwh

            sss = exp_ss if imp_ss is None else imp_ss
            dc_contract = sss.dc_contract
            dc_vb_func = sss.contract_func(dc_contract, "virtual_bill")
            try:
                dc_vb_func(sss)
            except AttributeError as e:
                raise BadRequest(
                    f"Problem with virtual bill of DC contract {dc_contract.id} {e} "
                    f"{traceback.format_exc()}"
                )
            dc_bill = sss.dc_bill
            gbp = dc_bill["net-gbp"]

            mop_contract = sss.mop_contract
            mop_bill_function = sss.contract_func(mop_contract, "virtual_bill")
            try:
                mop_bill_function(sss)
            except (AttributeError, NameError) as e:
                raise BadRequest(
                    f"Problem with virtual bill of MOP contract {mop_contract.id} {e} "
                    f"{traceback.format_exc()}"
                )
            mop_bill = sss.mop_bill
            gbp += mop_bill["net-gbp"]

            if source_code in ("3rd-party", "3rd-party-reverse"):
                vals["import-3rd-party-net-gbp"] += gbp
                vals["used-3rd-party-net-gbp"] += gbp
            else:
                vals["import-grid-net-gbp"] += gbp
            vals["used-net-gbp"] += gbp

            generator_type = sss.generator_type_code
            if source_code in ("gen", "gen-grid"):
                site_gen_types.add(generator_type)

            era_category = sss.measurement_type
            if CATEGORY_ORDER[site_category] < CATEGORY_ORDER[era_category]:
                site_category = era_category

            era_associates = {
                s.site.code for s in sss.era.site_eras if not s.is_physical
            }

            for bill in sess.query(Bill).filter(
                Bill.supply == supply,
                Bill.start_date <= sss.finish_date,
                Bill.finish_date >= sss.start_date,
            ):
                bill_role_code = bill.batch.contract.market_role.code
                bill_start = bill.start_date
                bill_finish = bill.finish_date
                bill_duration = (bill_finish - bill_start).total_seconds() + (30 * 60)
                overlap_duration = (
                    min(bill_finish, sss.finish_date) - max(bill_start, sss.start_date)
                ).total_seconds() + (30 * 60)
                proportion = overlap_duration / bill_duration
                vals["billed-import-kwh"] += proportion * float(bill.kwh)
                bill_prop_net_gbp = proportion * float(bill.net)
                bill_prop_vat_gbp = proportion * float(bill.vat)
                bill_prop_gross_gbp = proportion * float(bill.gross)
                vals["billed-import-net-gbp"] += bill_prop_net_gbp
                vals["billed-import-vat-gbp"] += bill_prop_vat_gbp
                vals["billed-import-gross-gbp"] += bill_prop_gross_gbp
                if bill_role_code == "X":
                    role_name = "supplier"
                elif bill_role_code == "C":
                    role_name = "dc"
                elif bill_role_code == "M":
                    role_name = "mop"
                else:
                    raise BadRequest("Role code not recognized.")

                vals[f"billed-import-{role_name}-net-gbp"] += bill_prop_net_gbp
                vals[f"billed-import-{role_name}-vat-gbp"] += bill_prop_vat_gbp
                vals[f"billed-import-{role_name}-gross-gbp"] += bill_prop_gross_gbp

            vals["imp-mpan-core"] = imp_mpan_core
            vals["exp-mpan-core"] = exp_mpan_core
            vals["associated-site-codes"] = era_associates
            vals["era-start-date"] = sss.era.start_date
            vals["era-finish-date"] = sss.era.finish_date
            vals["imp-supplier-contract"] = imp_supplier_contract_name
            vals["imp-non-actual-hhs"] = imp_bad_hhs
            vals["imp-non-actual-kwh"] = imp_bad_kwh
            vals["exp-supplier-contract"] = exp_supplier_contract_name
            vals["exp-non-actual-hhs"] = exp_bad_hhs
            vals["exp-non-actual-kwh"] = exp_bad_kwh
            vals["metering-type"] = era_category
            vals["source"] = source_code
            vals["generator-type"] = generator_type
            vals["supply-name"] = sss.supply_name
            vals["msn"] = sss.msn
            vals["pc"] = sss.pc_code

            for t in title_dict["mop"]:
                try:
                    vals[f"mop-{t}"] = mop_bill[t]
                except KeyError:
                    pass

            for t in title_dict["dc"]:
                try:
                    vals[f"dc-{t}"] = dc_bill[t]
                except KeyError:
                    pass

            supply_data["imp-mpan-core"] = imp_mpan_core
            supply_data["exp-mpan-core"] = exp_mpan_core
            supply_data["associated-site-codes"].update(era_associates)
            supply_data["start-date"] = min(sss.start_date, supply_data["start-date"])
            supply_data["finish-date"] = max(
                sss.finish_date, supply_data["finish-date"]
            )

            supply_data["source"] = source_code
            supply_data["generator-type"] = generator_type
            supply_data["supply-name"] = sss.supply_name

        era_rows.append([make_val(vals.get(t)) for t in era_titles])

        for t in summary_titles:
            v = vals.get(t)
            if v is not None:
                site_data[t] += v

    q = select(Supply).join(Era).join(SiteEra).where(SiteEra.site == site).distinct()
    if supply_ids is not None:
        q = q.where(Supply.id.in_(supply_ids))
    for supply in sess.execute(q).scalars():
        last_era = (
            sess.execute(
                select(Era).where(Era.supply == supply).order_by(Era.start_date.desc())
            )
            .scalars()
            .first()
        )
        if last_era.finish_date is not None and last_era.start_date <= finish_date:
            site_era = sess.execute(
                select(SiteEra).where(
                    SiteEra.era == last_era,
                    SiteEra.is_physical == true(),
                    SiteEra.site == site,
                )
            ).scalar_one_or_none()
            if site_era is not None:
                chunk_start = max(start_date, last_era.finish_date + HH)
                chunk_finish = finish_date
                bills = (
                    sess.execute(
                        select(Bill).where(
                            Bill.supply == supply,
                            Bill.start_date <= chunk_finish,
                            Bill.finish_date >= chunk_start,
                        )
                    )
                    .scalars()
                    .all()
                )
                if len(bills) > 0:
                    imp_supplier_contract = last_era.imp_supplier_contract
                    imp_supplier_contract_name = (
                        None
                        if imp_supplier_contract is None
                        else imp_supplier_contract.name
                    )
                    exp_supplier_contract = last_era.exp_supplier_contract
                    exp_supplier_contract_name = (
                        None
                        if exp_supplier_contract is None
                        else exp_supplier_contract.name
                    )
                    era_associates = {
                        s.site.code for s in last_era.site_eras if not s.is_physical
                    }
                    vals = {
                        "creation-date": now,
                        "start-date": chunk_start,
                        "finish-date": chunk_finish,
                        "imp-mpan-core": last_era.imp_mpan_core,
                        "exp-mpan-core": last_era.exp_mpan_core,
                        "site-code": site.code,
                        "site-name": site.name,
                        "associated-site-codes": era_associates,
                        "era-start-date": None,
                        "era-finish-date": None,
                        "imp-supplier-contract": imp_supplier_contract_name,
                        "imp-non-actual-hhs": None,
                        "imp-non-actual-kwh": None,
                        "exp-supplier-contract": exp_supplier_contract_name,
                        "exp-non-actual-hhs": None,
                        "exp-non-actual-kwh": None,
                        "metering-type": last_era.meter_category,
                        "source": last_era.supply.source.code,
                        "generator-type": None,
                        "supply-name": last_era.supply.name,
                        "msn": last_era.msn,
                        "pc": last_era.pc.code,
                    }
                    for name in (
                        "import-grid",
                        "export-grid",
                        "import-gen",
                        "export-gen",
                        "import-3rd-party",
                        "export-3rd-party",
                        "displaced",
                        "used",
                        "used-3rd-party",
                    ):
                        for sname in ("kwh", "net-gbp"):
                            vals[f"{name}-{sname}"] = 0
                    for suf in ("kwh", "net-gbp", "vat-gbp", "gross-gbp"):
                        vals[f"billed-import-{suf}"] = 0
                        vals[f"billed-import-supplier-{suf}"] = 0
                        vals[f"billed-import-dc-{suf}"] = 0
                        vals[f"billed-import-mop-{suf}"] = 0

                    _add_bills(vals, bills, chunk_start, chunk_finish)

                    era_rows.append([make_val(vals.get(t)) for t in era_titles])
                    for t in summary_titles:
                        v = vals.get(t)
                        if v is not None:
                            site_data[t] += v
        first_era = (
            sess.execute(
                select(Era).where(Era.supply == supply).order_by(Era.start_date)
            )
            .scalars()
            .first()
        )
        if first_era.start_date > start_date:
            site_era = sess.execute(
                select(SiteEra).where(
                    SiteEra.era == first_era,
                    SiteEra.is_physical == true(),
                    SiteEra.site == site,
                )
            ).scalar_one_or_none()
            if site_era is not None:
                chunk_start = start_date
                chunk_finish = hh_min(finish_date, first_era.start_date - HH)
                bills = (
                    sess.execute(
                        select(Bill).where(
                            Bill.supply == supply,
                            Bill.start_date <= chunk_finish,
                            Bill.finish_date >= chunk_start,
                        )
                    )
                    .scalars()
                    .all()
                )
                imp_supplier_contract = first_era.imp_supplier_contract
                exp_supplier_contract = first_era.exp_supplier_contract
                if len(bills) > 0:
                    era_vals = {
                        "creation-date": now,
                        "start-date": start_date,
                        "finish-date": finish_date,
                        "imp-mpan-core": last_era.imp_mpan_core,
                        "exp-mpan-core": last_era.exp_mpan_core,
                        "site-code": site.code,
                        "site-name": site.name,
                        "associated-site-codes": None,
                        "era-start-date": None,
                        "era-finish-date": None,
                        "imp-supplier-contract": (
                            None
                            if imp_supplier_contract is None
                            else imp_supplier_contract.name
                        ),
                        "imp-non-actual-hhs": None,
                        "imp-non-actual-kwh": None,
                        "exp-supplier-contract": (
                            None
                            if exp_supplier_contract is None
                            else exp_supplier_contract.name
                        ),
                        "exp-non-actual-hhs": None,
                        "exp-non-actual-kwh": None,
                        "metering-type": last_era.meter_category,
                        "source": last_era.supply.source.code,
                        "generator-type": None,
                        "supply-name": last_era.supply.name,
                        "msn": last_era.msn,
                        "pc": last_era.pc.code,
                    }
                    for name in (
                        "import-grid",
                        "export-grid",
                        "import-gen",
                        "export-gen",
                        "import-3rd-party",
                        "export-3rd-party",
                        "displaced",
                        "used",
                        "used-3rd-party",
                    ):
                        for sname in ("kwh", "net-gbp"):
                            era_vals[f"{name}-{sname}"] = 0
                    for suf in ("kwh", "net-gbp", "vat-gbp", "gross-gbp"):
                        era_vals[f"billed-import-{suf}"] = 0
                        era_vals[f"billed-import-supplier-{suf}"] = 0
                        era_vals[f"billed-import-dc-{suf}"] = 0
                        era_vals[f"billed-import-mop-{suf}"] = 0

                    _add_bills(era_vals, bills, chunk_start, chunk_finish)

                    era_rows.append([make_val(era_vals.get(t)) for t in era_titles])
                    for t in summary_titles:
                        v = era_vals.get(t)
                        if v is not None:
                            site_data[t] += v

    for _, v in sorted(supplies_data.items()):
        row = [make_val(v.get(t)) for t in supply_titles]
        supply_rows.append(row)

    site_md_used_kw = 0
    for hh in site.hh_data(sess, start_date, finish_date, exclude_virtual=True):
        used_kw = hh["used"] * 2
        site_md_used_kw = max(used_kw, site_md_used_kw)

    site_row = [
        now,
        site.code,
        site.name,
        [s.code for s in site.find_linked_sites(sess, start_date, finish_date)],
        start_date,
        finish_date,
        site_category,
        site_sources,
        site_gen_types,
        site_md_used_kw,
    ] + [site_data[k] for k in summary_titles]

    site_rows.append([make_val(v) for v in site_row])
    return normal_reads


class Object:
    pass


def content(
    scenario_props,
    base_name,
    user_id,
    compression,
    now,
    is_bill_check,
):
    report_context = {}

    rsess = rf = None
    site_rows = []
    supply_rows = []
    era_rows = []
    normal_read_rows = []

    try:
        with RSession() as rsess:
            start_date = to_utc(
                ct_datetime(
                    scenario_props["scenario_start_year"],
                    scenario_props["scenario_start_month"],
                    scenario_props["scenario_start_day"],
                    scenario_props["scenario_start_hour"],
                    scenario_props["scenario_start_minute"],
                )
            )
            finish_date = to_utc(
                ct_datetime(
                    scenario_props["scenario_finish_year"],
                    scenario_props["scenario_finish_month"],
                    scenario_props["scenario_finish_day"],
                    scenario_props["scenario_finish_hour"],
                    scenario_props["scenario_finish_minute"],
                )
            )

            if "forecast_from" in scenario_props:
                forecast_from = scenario_props["forecast_from"]
            else:
                forecast_from = None

            if forecast_from is None:
                forecast_from = forecast_date()
            else:
                forecast_from = to_utc(forecast_from)

            site_codes = scenario_props.get("site_codes")

            sites = select(Site).distinct().order_by(Site.code)
            if site_codes is not None and len(site_codes) > 0:
                base_name.append("sitecodes")
                sites = sites.where(Site.code.in_(site_codes))

            mpan_cores = scenario_props.get("mpan_cores")
            if mpan_cores is None:
                supply_ids = None
            else:
                supply_ids = [Supply.get_by_mpan_core(rsess, m).id for m in mpan_cores]
                sites = (
                    sites.join(SiteEra).join(Era).where(Era.supply_id.in_(supply_ids))
                )

            user = User.get_by_id(rsess, user_id)
            rf = open_file("_".join(base_name) + ".ods", user, mode="wb")
            scenario_fill_cache(report_context, rsess, scenario_props)

            by_hh = scenario_props.get("by_hh", False)
            is_bill_check = scenario_props.get("is_bill_check", False)

            era_header_titles = [
                "creation-date",
                "start-date",
                "finish-date",
                "imp-mpan-core",
                "exp-mpan-core",
                "site-code",
                "site-name",
                "associated-site-codes",
                "era-start-date",
                "era-finish-date",
                "imp-supplier-contract",
                "imp-non-actual-hhs",
                "imp-non-actual-kwh",
                "exp-supplier-contract",
                "exp-non-actual-hhs",
                "exp-non-actual-kwh",
                "metering-type",
                "source",
                "generator-type",
                "supply-name",
                "msn",
                "pc",
            ]
            supply_header_titles = [
                "creation-date",
                "start-date",
                "finish-date",
                "imp-mpan-core",
                "exp-mpan-core",
                "site-code",
                "site-name",
                "associated-site-codes",
                "source",
                "generator-type",
                "supply-name",
                "imp-md-kw",
                "imp-md-kva",
                "exp-md-kw",
                "exp-md-kva",
            ]
            site_header_titles = [
                "creation-date",
                "site-code",
                "site-name",
                "associated-site-codes",
                "start-date",
                "finish-date",
                "metering-type",
                "sources",
                "generator-types",
                "md-used-kw",
            ]
            summary_titles = [
                "import-grid-kwh",
                "export-grid-kwh",
                "import-gen-kwh",
                "export-gen-kwh",
                "import-3rd-party-kwh",
                "export-3rd-party-kwh",
                "displaced-kwh",
                "used-kwh",
                "used-3rd-party-kwh",
                "import-grid-net-gbp",
                "export-grid-net-gbp",
                "import-gen-net-gbp",
                "export-gen-net-gbp",
                "import-3rd-party-net-gbp",
                "export-3rd-party-net-gbp",
                "displaced-net-gbp",
                "used-net-gbp",
                "used-3rd-party-net-gbp",
                "billed-import-kwh",
                "billed-import-net-gbp",
                "billed-import-vat-gbp",
                "billed-import-gross-gbp",
                "billed-import-supplier-net-gbp",
                "billed-import-supplier-vat-gbp",
                "billed-import-supplier-gross-gbp",
                "billed-import-dc-net-gbp",
                "billed-import-dc-vat-gbp",
                "billed-import-dc-gross-gbp",
                "billed-import-mop-net-gbp",
                "billed-import-mop-vat-gbp",
                "billed-import-mop-gross-gbp",
            ]

            title_dict = {}
            for cont_type, con_attr in (
                ("mop", Era.mop_contract),
                ("dc", Era.dc_contract),
                ("imp-supplier", Era.imp_supplier_contract),
                ("exp-supplier", Era.exp_supplier_contract),
            ):
                titles = []
                title_dict[cont_type] = titles
                conts = (
                    select(Contract)
                    .join(con_attr)
                    .join(Era.supply)
                    .join(Source)
                    .where(
                        Era.start_date <= finish_date,
                        or_(Era.finish_date == null(), Era.finish_date >= start_date),
                    )
                    .distinct()
                    .order_by(Contract.id)
                )
                if supply_ids is not None:
                    conts = conts.where(Era.supply_id.in_(supply_ids))
                for cont in rsess.scalars(conts):
                    title_func = contract_func(
                        report_context, cont, "virtual_bill_titles"
                    )
                    if title_func is None:
                        raise Exception(
                            f"For the contract {cont.name} there doesn't seem to be a "
                            f"'virtual_bill_titles' function."
                        )
                    for title in title_func():
                        if title not in titles:
                            titles.append(title)

            tpr_query = (
                rsess.query(Tpr)
                .join(MeasurementRequirement)
                .join(Ssc)
                .join(Era)
                .filter(
                    Era.start_date <= finish_date,
                    or_(Era.finish_date == null(), Era.finish_date >= start_date),
                )
                .order_by(Tpr.code)
                .distinct()
            )
            for tpr in tpr_query.filter(Era.imp_supplier_contract != null()):
                for suffix in ("-kwh", "-rate", "-gbp"):
                    title_dict["imp-supplier"].append(tpr.code + suffix)
            for tpr in tpr_query.filter(Era.exp_supplier_contract != null()):
                for suffix in ("-kwh", "-rate", "-gbp"):
                    title_dict["exp-supplier"].append(tpr.code + suffix)

            era_titles = (
                era_header_titles
                + summary_titles
                + [None]
                + ["mop-" + t for t in title_dict["mop"]]
                + [None]
                + ["dc-" + t for t in title_dict["dc"]]
                + [None]
                + ["imp-supplier-" + t for t in title_dict["imp-supplier"]]
                + [None]
                + ["exp-supplier-" + t for t in title_dict["exp-supplier"]]
            )
            site_rows.append(site_header_titles + summary_titles)
            supply_titles = supply_header_titles + summary_titles
            supply_rows.append(supply_titles)
            era_rows.append(era_titles)

            normal_reads = set()

            if is_bill_check:
                data_source_bill = Object()
                data_source_bill.start_date = start_date
                data_source_bill.finish_date = finish_date
            else:
                data_source_bill = None

            for site in rsess.scalars(sites):
                if by_hh:
                    sf = [
                        (d, d)
                        for d in hh_range(report_context, start_date, finish_date)
                    ]
                else:
                    sf = [(start_date, finish_date)]

                for start, finish in sf:
                    try:
                        normal_reads = normal_reads | _process_site(
                            rsess,
                            report_context,
                            forecast_from,
                            start,
                            finish,
                            site,
                            scenario_props,
                            supply_ids,
                            now,
                            summary_titles,
                            title_dict,
                            era_titles,
                            era_rows,
                            supply_titles,
                            supply_rows,
                            site_rows,
                            data_source_bill,
                        )
                    except BadRequest as e:
                        raise BadRequest(f"Site Code {site.code}: {e.description}")

                normal_read_rows = [["mpan_core", "date", "msn", "type", "registers"]]
                for mpan_core, r in sorted(list(normal_reads)):
                    row = [mpan_core, r.date, r.msn, r.type] + list(r.reads)
                    normal_read_rows.append(row)

                rsess.rollback()  # Evict from cache
            write_spreadsheet(
                rf, compression, site_rows, supply_rows, era_rows, normal_read_rows
            )
    except BadRequest as e:
        msg = e.description + traceback.format_exc()
        sys.stderr.write(msg + "\n")
        site_rows.append(["Problem " + msg])
        write_spreadsheet(
            rf, compression, site_rows, supply_rows, era_rows, normal_read_rows
        )
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + "\n")
        site_rows.append(["Problem " + msg])
        if rf is None:
            msg = traceback.format_exc()
            ef = open_file("error.txt", None, mode="w")
            ef.write(msg + "\n")
            ef.close()
        else:
            write_spreadsheet(
                rf, compression, site_rows, supply_rows, era_rows, normal_read_rows
            )
    finally:
        if rf is not None:
            rf.close()


def do_post(sess):
    base_name = ["duration"]
    compression = req_bool("compression")

    try:
        if "scenario_id" in request.values:
            scenario_id = req_int("scenario_id")
            scenario = Scenario.get_by_id(sess, scenario_id)
            props = scenario.props
            base_name.append(scenario.name)

        else:
            start_date = req_hh_date("start")
            finish_date = req_hh_date("finish")

            start_date_ct = to_ct(start_date)
            finish_date_ct = to_ct(finish_date)
            props = {
                "scenario_start_year": start_date_ct.year,
                "scenario_start_month": start_date_ct.month,
                "scenario_start_day": start_date_ct.day,
                "scenario_start_hour": start_date_ct.hour,
                "scenario_start_minute": start_date_ct.minute,
                "scenario_finish_year": finish_date_ct.year,
                "scenario_finish_month": finish_date_ct.month,
                "scenario_finish_day": finish_date_ct.day,
                "scenario_finish_hour": finish_date_ct.hour,
                "scenario_finish_minute": finish_date_ct.minute,
            }
            base_name.append(hh_format(start_date).replace(" ", "_").replace(":", "_"))

        if "mpan_cores" in request.values:
            mpan_cores_str = req_str("mpan_cores")
            mpan_cores_lines = mpan_cores_str.splitlines()
            if len(mpan_cores_lines) > 0:
                props["mpan_cores"] = [parse_mpan_core(m) for m in mpan_cores_lines]

        if "supply_id" in request.values:
            supply_id = req_int("supply_id")
            supply = Supply.get_by_id(sess, supply_id)
            era = supply.eras[-1]
            imp_mpan_core, exp_mpan_core = era.imp_mpan_core, era.exp_mpan_core
            props["mpan_cores"] = [
                exp_mpan_core if imp_mpan_core is None else imp_mpan_core
            ]

        if "site_codes" in request.values:
            site_codes_str = req_str("site_codes")
            site_codes_lines = site_codes_str.splitlines()
            if len(site_codes_lines) > 0:
                props["site_codes"] = [c.strip() for c in site_codes_lines]

        if "site_id" in request.values:
            site_id = req_int("site_id")
            site = Site.get_by_id(sess, site_id)
            props["site_codes"] = [site.code]

        now = utc_datetime_now()
        args = props, base_name, g.user.id, compression, now, False
        sess.rollback()
        thread = threading.Thread(target=content, args=args)
        thread.start()
        return redirect("/downloads", 303)
    except BadRequest as e:
        flash(e.description)
        if "scenario_id" in request.values:
            return make_response(
                render_template("e/scenario.html", scenario=scenario), 400
            )
        else:
            ct_last = ct_datetime_now() - relativedelta(months=1)
            months = list(
                c_months_u(start_year=ct_last.year, start_month=ct_last.month)
            )
            month_start, month_finish = months[0]
            return make_response(
                render_template(
                    "e/duration_report.html",
                    month_start=month_start,
                    month_finish=month_finish,
                ),
                400,
            )
