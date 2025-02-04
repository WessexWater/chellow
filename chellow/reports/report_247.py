import sys
import threading
import traceback
from collections import defaultdict
from datetime import datetime as Datetime

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
    ReportRun,
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
    c_months_c,
    c_months_u,
    hh_format,
    hh_min,
    hh_range,
    make_val,
    req_bool,
    req_int,
    req_str,
    to_utc,
    utc_datetime_now,
)


CATEGORY_ORDER = {None: 0, "unmetered": 1, "nhh": 2, "amr": 3, "hh": 4}
meter_order = {"hh": 0, "amr": 1, "nhh": 2, "unmetered": 3}


def write_spreadsheet(
    fl,
    compressed,
    site_rows,
    era_rows,
    read_rows,
):
    fl.seek(0)
    fl.truncate()
    with odio.create_spreadsheet(fl, "1.2", compressed=compressed) as f:
        f.append_table("Site Level", site_rows)
        f.append_table("Era Level", era_rows)
        f.append_table("Normal Reads", read_rows)


def make_bill_row(titles, bill):
    return [bill.get(t) for t in titles]


def _add_bills(month_data, era, bills, chunk_start, chunk_finish):
    for bill in bills:
        contract = bill.batch.contract
        bill_role_code = contract.market_role.code
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
            polarity = "export" if contract == era.exp_supplier_contract else "import"
        elif bill_role_code == "C":
            role_name = "dc"
            polarity = "import"
        elif bill_role_code == "M":
            role_name = "mop"
            polarity = "import"
        else:
            raise BadRequest("Role code not recognized.")

        month_data[f"billed-{polarity}-kwh"] += bill_prop_kwh
        month_data[f"billed-{polarity}-net-gbp"] += bill_prop_net_gbp
        month_data[f"billed-{polarity}-vat-gbp"] += bill_prop_vat_gbp
        month_data[f"billed-{polarity}-gross-gbp"] += bill_prop_gross_gbp
        month_data[f"billed-{role_name}-{polarity}-net-gbp"] += bill_prop_net_gbp
        month_data[f"billed-{role_name}-{polarity}-vat-gbp"] += bill_prop_vat_gbp
        month_data[f"billed-{role_name}-{polarity}-gross-gbp"] += bill_prop_gross_gbp


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
    org_rows,
    site_rows,
    era_rows,
    normal_reads,
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
    site_month_data = defaultdict(int)
    for i, (order, imp_mpan_core, exp_mpan_core, imp_ss, exp_ss) in enumerate(
        sorted(calcs, key=str)
    ):
        if imp_mpan_core == "displaced":
            month_data = {}
            for sname in (
                "import-gen",
                "export-gen",
                "import-3rd-party",
                "export-3rd-party",
                "msp",
                "used",
                "used-3rd-party",
                "billed-export",
            ):
                for xname in ("kwh", "net-gbp"):
                    month_data[f"{sname}-{xname}"] = 0
            month_data["billed-import-kwh"] = 0
            month_data["import-grid-kwh"] = 0
            month_data["export-grid-kwh"] = 0
            for suf in ("net-gbp", "vat-gbp", "gross-gbp"):
                month_data[f"import-grid-{suf}"] = 0
                month_data[f"export-grid-{suf}"] = 0
                month_data[f"billed-import-{suf}"] = 0
                month_data[f"billed-supplier-import-{suf}"] = None
                month_data[f"billed-dc-import-{suf}"] = None
                month_data[f"billed-mop-import-{suf}"] = None
                month_data[f"billed-export-{suf}"] = 0

            month_data["used-kwh"] = month_data["displaced-kwh"] = sum(
                hh["msp-kwh"] for hh in imp_ss.hh_data
            )

            disp_supplier_bill = imp_ss.supplier_bill

            gbp = disp_supplier_bill.get("net-gbp", 0)

            month_data["used-net-gbp"] = month_data["displaced-net-gbp"] = gbp

            out = (
                [
                    now,
                    None,
                    imp_ss.supplier_contract.name,
                    None,
                    None,
                    None,
                    imp_ss.era.meter_category,
                    "displaced",
                    None,
                    None,
                    None,
                    imp_ss.pc_code,
                    imp_ss.energisation_status_code,
                    imp_ss.gsp_group_code,
                    imp_ss.dno_code,
                    imp_ss.voltage_level_code,
                    imp_ss.is_substation,
                    imp_ss.llfc_code,
                    imp_ss.llfc.description,
                    None,
                    None,
                    None,
                    None,
                    site.code,
                    site.name,
                    "",
                    finish_date,
                ]
                + [month_data[t] for t in summary_titles]
                + [None]
                + [None] * len(title_dict["mop"])
                + [None]
                + [None] * len(title_dict["dc"])
                + [None]
                + make_bill_row(title_dict["imp-supplier"], disp_supplier_bill)
            )

            era_rows.append([make_val(v) for v in out])
            for k, v in month_data.items():
                if v is not None:
                    site_month_data[k] += v
        else:
            if imp_ss is None:
                source_code = exp_ss.source_code
                supply = exp_ss.supply
            else:
                source_code = imp_ss.source_code
                supply = imp_ss.supply

            site_sources.add(source_code)
            month_data = {}
            for name in (
                "import-gen",
                "export-gen",
                "import-3rd-party",
                "export-3rd-party",
                "displaced",
                "used",
                "used-3rd-party",
                "billed-export",
            ):
                for sname in ("kwh", "net-gbp"):
                    month_data[f"{name}-{sname}"] = 0
            for polarity in ("import", "export"):
                month_data[f"billed-{polarity}-kwh"] = 0
                month_data[f"{polarity}-grid-kwh"] = 0
                for suf in ("net-gbp", "vat-gbp", "gross-gbp"):
                    month_data[f"{polarity}-grid-{suf}"] = 0
                    month_data[f"billed-{polarity}-{suf}"] = 0
                    month_data[f"billed-supplier-{polarity}-{suf}"] = 0
                    month_data[f"billed-dc-{polarity}-{suf}"] = 0
                    month_data[f"billed-mop-{polarity}-{suf}"] = 0

            if imp_ss is not None:
                imp_supplier_contract = imp_ss.supplier_contract

                kwh = sum(hh["msp-kwh"] for hh in imp_ss.hh_data)
                imp_supplier_bill = imp_ss.supplier_bill

                net_gbp = imp_supplier_bill.get("net-gbp", 0)
                vat_gbp = imp_supplier_bill.get("vat-gbp", 0)
                gross_gbp = imp_supplier_bill.get("gross-gbp", 0)

                if source_code in ("grid", "gen-grid"):
                    month_data["import-grid-net-gbp"] += net_gbp
                    month_data["import-grid-vat-gbp"] += vat_gbp
                    month_data["import-grid-gross-gbp"] += gross_gbp
                    month_data["import-grid-kwh"] += kwh
                    month_data["used-net-gbp"] += net_gbp
                    month_data["used-kwh"] += kwh
                    if source_code == "gen-grid":
                        month_data["export-gen-kwh"] += kwh
                elif source_code == "3rd-party":
                    month_data["import-3rd-party-net-gbp"] += net_gbp
                    month_data["import-3rd-party-kwh"] += kwh
                    month_data["used-3rd-party-net-gbp"] += net_gbp
                    month_data["used-3rd-party-kwh"] += kwh
                    month_data["used-net-gbp"] += net_gbp
                    month_data["used-kwh"] += kwh
                elif source_code == "3rd-party-reverse":
                    month_data["export-3rd-party-net-gbp"] += net_gbp
                    month_data["export-3rd-party-kwh"] += kwh
                    month_data["used-3rd-party-net-gbp"] -= net_gbp
                    month_data["used-3rd-party-kwh"] -= kwh
                    month_data["used-net-gbp"] -= net_gbp
                    month_data["used-kwh"] -= kwh
                elif source_code == "gen":
                    month_data["import-gen-kwh"] += kwh

            if exp_ss is not None:
                exp_supplier_contract = exp_ss.supplier_contract

                kwh = sum(hh["msp-kwh"] for hh in exp_ss.hh_data)
                exp_supplier_bill = exp_ss.supplier_bill

                net_gbp = exp_supplier_bill.get("net-gbp", 0)
                vat_gbp = exp_supplier_bill.get("vat-gbp", 0)
                gross_gbp = exp_supplier_bill.get("gross-gbp", 0)

                if source_code in ("grid", "gen-grid"):
                    month_data["export-grid-net-gbp"] += net_gbp
                    month_data["export-grid-vat-gbp"] += vat_gbp
                    month_data["export-grid-gross-gbp"] += gross_gbp
                    month_data["export-grid-kwh"] += kwh
                    if source_code == "gen-grid":
                        month_data["import-gen-kwh"] += kwh

                elif source_code == "3rd-party":
                    month_data["export-3rd-party-net-gbp"] += net_gbp
                    month_data["export-3rd-party-kwh"] += kwh
                    month_data["used-3rd-party-net-gbp"] -= net_gbp
                    month_data["used-3rd-party-kwh"] -= kwh
                    month_data["used-net-gbp"] -= net_gbp
                    month_data["used-kwh"] -= kwh
                elif source_code == "3rd-party-reverse":
                    month_data["import-3rd-party-net-gbp"] += net_gbp
                    month_data["import-3rd-party-kwh"] += kwh
                    month_data["used-3rd-party-net-gbp"] += net_gbp
                    month_data["used-3rd-party-kwh"] += kwh
                    month_data["used-net-gbp"] += net_gbp
                    month_data["used-kwh"] += kwh
                elif source_code == "gen":
                    month_data["export-gen-kwh"] += kwh

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
                month_data["import-3rd-party-net-gbp"] += gbp
                month_data["used-3rd-party-net-gbp"] += gbp
            else:
                month_data["import-grid-net-gbp"] += gbp
            month_data["used-net-gbp"] += gbp

            generator_type = sss.generator_type_code
            if source_code in ("gen", "gen-grid"):
                site_gen_types.add(generator_type)

            era_category = sss.measurement_type
            if CATEGORY_ORDER[site_category] < CATEGORY_ORDER[era_category]:
                site_category = era_category

            era_associates = {
                s.site.code for s in sss.era.site_eras if not s.is_physical
            }
            bills = sess.scalars(
                select(Bill).where(
                    Bill.supply == supply,
                    Bill.start_date <= sss.finish_date,
                    Bill.finish_date >= sss.start_date,
                )
            ).all()
            _add_bills(month_data, sss.era, bills, sss.start_date, sss.finish_date)

            if imp_ss is None:
                imp_supplier_contract_name = imp_voltage_level_code = None
                imp_is_substation = imp_llfc_code = imp_llfc_description = None
                pc_code = exp_ss.pc_code
            else:
                if imp_supplier_contract is None:
                    imp_supplier_contract_name = ""
                else:
                    imp_supplier_contract_name = imp_supplier_contract.name
                pc_code = imp_ss.pc_code
                imp_voltage_level_code = imp_ss.voltage_level_code
                imp_is_substation = imp_ss.is_substation
                imp_llfc_code = imp_ss.llfc_code
                imp_llfc_description = imp_ss.llfc.description

            if exp_ss is None:
                exp_supplier_contract_name = exp_voltage_level_code = None
                exp_is_substation = exp_llfc_code = exp_llfc_description = None
            else:
                if exp_supplier_contract is None:
                    exp_supplier_contract_name = ""
                else:
                    exp_supplier_contract_name = exp_supplier_contract.name
                exp_voltage_level_code = exp_ss.voltage_level_code
                exp_is_substation = exp_ss.is_substation
                exp_llfc_code = exp_ss.llfc_code
                exp_llfc_description = exp_ss.llfc.description

            out = (
                [
                    now,
                    imp_mpan_core,
                    imp_supplier_contract_name,
                    exp_mpan_core,
                    exp_supplier_contract_name,
                    sss.era.start_date,
                    era_category,
                    source_code,
                    generator_type,
                    sss.supply_name,
                    sss.msn,
                    pc_code,
                    sss.energisation_status_code,
                    sss.gsp_group_code,
                    sss.dno_code,
                    imp_voltage_level_code,
                    imp_is_substation,
                    imp_llfc_code,
                    imp_llfc_description,
                    exp_voltage_level_code,
                    exp_is_substation,
                    exp_llfc_code,
                    exp_llfc_description,
                    site.code,
                    site.name,
                    ",".join(sorted(list(era_associates))),
                    finish_date,
                ]
                + [month_data[t] for t in summary_titles]
                + [None]
                + make_bill_row(title_dict["mop"], mop_bill)
                + [None]
                + make_bill_row(title_dict["dc"], dc_bill)
            )
            if imp_ss is None:
                out += [None] * (len(title_dict["imp-supplier"]) + 1)
            else:
                out += [None] + make_bill_row(
                    title_dict["imp-supplier"], imp_supplier_bill
                )
                for n in imp_ss.normal_reads:
                    normal_reads.add((imp_mpan_core, n))
            if exp_ss is not None:
                out += [None] + make_bill_row(
                    title_dict["exp-supplier"], exp_supplier_bill
                )

            for k, v in month_data.items():
                site_month_data[k] += v
            era_rows.append([make_val(v) for v in out])

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
                    month_data = {}
                    for name in (
                        "import-gen",
                        "export-gen",
                        "import-3rd-party",
                        "export-3rd-party",
                        "displaced",
                        "used",
                        "used-3rd-party",
                        "billed-export",
                    ):
                        for sname in ("kwh", "net-gbp"):
                            month_data[f"{name}-{sname}"] = 0
                    month_data["billed-import-kwh"] = 0
                    month_data["import-grid-kwh"] = 0
                    month_data["export-grid-kwh"] = 0
                    for suf in ("net-gbp", "vat-gbp", "gross-gbp"):
                        month_data[f"import-grid-{suf}"] = 0
                        month_data[f"export-grid-{suf}"] = 0
                        month_data[f"billed-import-{suf}"] = 0
                        month_data[f"billed-supplier-import-{suf}"] = 0
                        month_data[f"billed-dc-import-{suf}"] = 0
                        month_data[f"billed-mop-import-{suf}"] = 0

                    _add_bills(month_data, last_era, bills, chunk_start, chunk_finish)

                    imp_supplier_contract = last_era.imp_supplier_contract
                    imp_llfc = last_era.imp_llfc
                    if imp_llfc is None:
                        imp_llfc_code = imp_voltage_level_code = None
                        imp_is_substation = imp_llfc_description = None
                    else:
                        imp_llfc_code = imp_llfc.code
                        imp_voltage_level_code = imp_llfc.voltage_level.code
                        imp_is_substation = imp_llfc.is_substation
                        imp_llfc_description = imp_llfc.description

                    exp_supplier_contract = last_era.exp_supplier_contract
                    exp_llfc = last_era.exp_llfc
                    if exp_llfc is None:
                        exp_llfc_code = exp_voltage_level_code = None
                        exp_is_substation = exp_llfc_description = None
                    else:
                        exp_llfc_code = exp_llfc.code
                        exp_voltage_level_code = exp_llfc.voltage_level.code
                        exp_is_substation = exp_llfc.is_substation
                        exp_llfc_description = exp_llfc.description
                    out = [
                        now,
                        last_era.imp_mpan_core,
                        (
                            None
                            if imp_supplier_contract is None
                            else imp_supplier_contract.name
                        ),
                        last_era.exp_mpan_core,
                        (
                            None
                            if exp_supplier_contract is None
                            else exp_supplier_contract.name
                        ),
                        chunk_start,
                        last_era.meter_category,
                        last_era.supply.source.code,
                        None,
                        last_era.supply.name,
                        last_era.msn,
                        last_era.pc.code,
                        last_era.energisation_status.code,
                        last_era.supply.gsp_group.code,
                        last_era.supply.dno.dno_code,
                        imp_voltage_level_code,
                        imp_is_substation,
                        imp_llfc_code,
                        imp_llfc_description,
                        exp_voltage_level_code,
                        exp_is_substation,
                        exp_llfc_code,
                        exp_llfc_description,
                        site.code,
                        site.name,
                        None,
                        finish_date,
                    ] + [month_data[t] for t in summary_titles]

                    era_rows.append([make_val(v) for v in out])
                    for k, v in month_data.items():
                        if v is not None:
                            site_month_data[k] += v
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
                if len(bills) > 0:
                    month_data = {}
                    for name in (
                        "import-gen",
                        "export-gen",
                        "import-3rd-party",
                        "export-3rd-party",
                        "displaced",
                        "used",
                        "used-3rd-party",
                    ):
                        for sname in ("kwh", "net-gbp"):
                            month_data[f"{name}-{sname}"] = 0
                    month_data["billed-import-kwh"] = 0
                    month_data["billed-export-kwh"] = 0
                    month_data["import-grid-kwh"] = 0
                    month_data["export-grid-kwh"] = 0
                    for suf in ("net-gbp", "vat-gbp", "gross-gbp"):
                        month_data[f"billed-import-{suf}"] = 0
                        month_data[f"billed-export-{suf}"] = 0
                        month_data[f"import-grid-{suf}"] = 0
                        month_data[f"export-grid-{suf}"] = 0
                        month_data[f"billed-supplier-import-{suf}"] = 0
                        month_data[f"billed-supplier-export-{suf}"] = 0
                        month_data[f"billed-dc-import-{suf}"] = 0
                        month_data[f"billed-mop-import-{suf}"] = 0
                    _add_bills(month_data, first_era, bills, chunk_start, chunk_finish)

                    imp_supplier_contract = first_era.imp_supplier_contract
                    imp_llfc = last_era.imp_llfc
                    if imp_llfc is None:
                        imp_llfc_code = imp_voltage_level_code = None
                        imp_is_substation = imp_llfc_description = None
                    else:
                        imp_llfc_code = imp_llfc.code
                        imp_voltage_level_code = imp_llfc.voltage_level.code
                        imp_is_substation = imp_llfc.is_substation
                        imp_llfc_description = imp_llfc.description

                    exp_llfc = last_era.exp_llfc
                    if exp_llfc is None:
                        exp_llfc_code = exp_voltage_level_code = None
                        exp_is_substation = exp_llfc_description = None
                    else:
                        exp_llfc_code = exp_llfc.code
                        exp_voltage_level_code = exp_llfc.voltage_level.code
                        exp_is_substation = exp_llfc.is_substation
                        exp_llfc_description = exp_llfc.description
                    exp_supplier_contract = first_era.exp_supplier_contract
                    out = [
                        now,
                        last_era.imp_mpan_core,
                        (
                            None
                            if imp_supplier_contract is None
                            else imp_supplier_contract.name
                        ),
                        last_era.exp_mpan_core,
                        (
                            None
                            if exp_supplier_contract is None
                            else exp_supplier_contract.name
                        ),
                        None,
                        last_era.meter_category,
                        last_era.supply.source.code,
                        None,
                        last_era.supply.name,
                        last_era.msn,
                        last_era.pc.code,
                        last_era.energisation_status.code,
                        last_era.supply.gsp_group.code,
                        last_era.supply.dno.dno_code,
                        imp_voltage_level_code,
                        imp_is_substation,
                        imp_llfc_code,
                        imp_llfc_description,
                        exp_voltage_level_code,
                        exp_is_substation,
                        exp_llfc_code,
                        exp_llfc_description,
                        site.code,
                        site.name,
                        None,
                        finish_date,
                    ] + [month_data[t] for t in summary_titles]

                    era_rows.append([make_val(v) for v in out])
                    for k, v in month_data.items():
                        if v is not None:
                            site_month_data[k] += v
    site_row = [
        now,
        site.code,
        site.name,
        ", ".join(
            s.code for s in site.find_linked_sites(sess, start_date, finish_date)
        ),
        finish_date,
        site_category,
        ", ".join(sorted(list(site_sources))),
        ", ".join(sorted(list(site_gen_types))),
    ] + [site_month_data[k] for k in summary_titles]

    site_rows.append([make_val(v) for v in site_row])
    return site_month_data


class Object:
    pass


def content(scenario_props, base_name, user_id, compression, now):
    report_context = {}

    sess = rf = None
    org_rows = []
    site_rows = []
    era_rows = []
    normal_read_rows = []
    try:
        with RSession() as sess:
            start_year = scenario_props["scenario_start_year"]
            start_month = scenario_props["scenario_start_month"]
            months = scenario_props["scenario_duration"]

            month_pairs = list(
                c_months_u(
                    start_year=start_year, start_month=start_month, months=months
                )
            )
            start_date_utc = month_pairs[0][0]
            finish_date_utc = month_pairs[-1][-1]

            base_name.append(
                hh_format(start_date_utc)
                .replace(" ", "_")
                .replace(":", "")
                .replace("-", "")
            )

            base_name.append("for")
            base_name.append(str(months))
            base_name.append("months")

            if "forecast_from" in scenario_props:
                forecast_from = scenario_props["forecast_from"]
            else:
                forecast_from = None

            if forecast_from is None:
                forecast_from = forecast_date()
            else:
                forecast_from = to_utc(forecast_from)

            base_site_set = set()

            mpan_cores = scenario_props.get("mpan_cores")
            supply_ids = None
            if mpan_cores is not None:
                supply_ids = []
                for mpan_core in mpan_cores:
                    supply = Supply.get_by_mpan_core(sess, mpan_core)
                    supply_ids.append(supply.id)

                if len(supply_ids) == 1:
                    base_name.append("supply")
                    base_name.append(str(supply.id))
                else:
                    base_name.append("mpan_cores")

                for site in sess.scalars(
                    select(Site)
                    .join(SiteEra)
                    .join(Era)
                    .join(Supply)
                    .where(Supply.id.in_(supply_ids))
                ):
                    base_site_set.add(site.id)

            site_codes = scenario_props.get("site_codes")
            if site_codes is not None:
                if len(site_codes) == 1:
                    base_name.append("site")
                    base_name.append(site_codes[0])
                else:
                    base_name.append("sitecodes")

                for site_code in site_codes:
                    site = Site.get_by_code(sess, site_code)
                    base_site_set.add(site.id)

            user = User.get_by_id(sess, user_id)

            fname = "_".join(base_name) + ".ods"
            rf = open_file(fname, user, mode="wb")

            scenario_fill_cache(report_context, sess, scenario_props)

            by_hh = scenario_props.get("by_hh", False)
            org_header_titles = [
                "creation-date",
                "month",
            ]

            site_header_titles = [
                "creation-date",
                "site-id",
                "site-name",
                "associated-site-ids",
                "month",
                "metering-type",
                "sources",
                "generator-types",
            ]
            era_header_titles = [
                "creation-date",
                "imp-mpan-core",
                "imp-supplier-contract",
                "exp-mpan-core",
                "exp-supplier-contract",
                "era-start-date",
                "metering-type",
                "source",
                "generator-type",
                "supply-name",
                "msn",
                "pc",
                "energisation-status",
                "gsp-group",
                "dno",
                "imp-voltage-level",
                "imp-is-substation",
                "imp-llfc-code",
                "imp-llfc-description",
                "exp-voltage-level",
                "exp-is-substation",
                "exp-llfc-code",
                "exp-llfc-description",
                "site-id",
                "site-name",
                "associated-site-ids",
                "month",
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
                "import-grid-vat-gbp",
                "import-grid-gross-gbp",
                "export-grid-net-gbp",
                "export-grid-vat-gbp",
                "export-grid-gross-gbp",
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
                "billed-supplier-import-net-gbp",
                "billed-supplier-import-vat-gbp",
                "billed-supplier-import-gross-gbp",
                "billed-dc-import-net-gbp",
                "billed-dc-import-vat-gbp",
                "billed-dc-import-gross-gbp",
                "billed-mop-import-net-gbp",
                "billed-mop-import-vat-gbp",
                "billed-mop-import-gross-gbp",
                "billed-export-kwh",
                "billed-export-net-gbp",
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
                    sess.query(Contract)
                    .join(con_attr)
                    .join(Era.supply)
                    .join(Source)
                    .filter(
                        Era.start_date <= finish_date_utc,
                        or_(
                            Era.finish_date == null(), Era.finish_date >= start_date_utc
                        ),
                    )
                    .distinct()
                    .order_by(Contract.id)
                )
                if supply_ids is not None:
                    conts = conts.where(Supply.id.in_(supply_ids))
                for cont in conts:
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
                sess.query(Tpr)
                .join(MeasurementRequirement)
                .join(Ssc)
                .join(Era)
                .filter(
                    Era.start_date <= finish_date_utc,
                    or_(Era.finish_date == null(), Era.finish_date >= start_date_utc),
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
            org_rows.append(org_header_titles + summary_titles)
            site_rows.append(site_header_titles + summary_titles)
            era_rows.append(era_titles)

            normal_reads = set()

            for month_start, month_finish in month_pairs:
                if scenario_props.get("is_bill_check", False):
                    data_source_bill = Object()
                    data_source_bill.start_date = month_start
                    data_source_bill.finish_date = month_finish
                else:
                    data_source_bill = None
                org_month_data = defaultdict(int)

                if len(base_site_set) > 0:
                    site_set = base_site_set
                else:
                    site_set = set()
                    for site in sess.scalars(
                        select(Site)
                        .join(SiteEra)
                        .join(Era)
                        .where(
                            Era.start_date <= month_finish,
                            or_(
                                Era.finish_date == null(),
                                Era.finish_date >= month_start,
                            ),
                        )
                    ):
                        site_set.add(site.id)
                    for site in sess.scalars(
                        select(Site)
                        .join(SiteEra)
                        .join(Era)
                        .join(Supply)
                        .join(Bill)
                        .where(
                            Bill.start_date <= month_finish,
                            Bill.finish_date >= month_start,
                        )
                    ):
                        site_set.add(site.id)

                for site in sess.scalars(
                    select(Site).where(Site.id.in_(site_set)).order_by(Site.code)
                ):
                    if by_hh:
                        sf = [
                            (d, d)
                            for d in hh_range(report_context, month_start, month_finish)
                        ]
                    else:
                        sf = [(month_start, month_finish)]

                    for start, finish in sf:
                        try:
                            site_month_data = _process_site(
                                sess,
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
                                org_rows,
                                site_rows,
                                era_rows,
                                normal_reads,
                                data_source_bill,
                            )
                            for k, v in site_month_data.items():
                                if v is not None:
                                    org_month_data[k] += v

                        except BadRequest as e:
                            raise BadRequest(f"Site Code {site.code}: {e.description}")

                    sess.rollback()  # Evict from cache

                normal_read_rows = [["mpan_core", "date", "msn", "type", "registers"]]
                for mpan_core, r in sorted(list(normal_reads)):
                    row = [mpan_core, r.date, r.msn, r.type] + list(r.reads)
                    normal_read_rows.append(row)

                org_row = [now, month_start] + [
                    org_month_data[k] for k in summary_titles
                ]
                org_rows.append([make_val(v) for v in org_row])

                write_spreadsheet(
                    rf, compression, site_rows, era_rows, normal_read_rows
                )
        if scenario_props.get("save_report_run", False):
            report_run_id = ReportRun.w_insert(
                "monthly_duration", user_id, fname, {"scenario": scenario_props}
            )
            for tab, rows in (
                ("org", org_rows),
                ("site", site_rows),
                ("era", era_rows),
            ):
                titles = rows[0]
                for row in rows[1:]:
                    values = dict(zip(titles, row))
                    ReportRun.w_insert_row(report_run_id, tab, titles, values, {})
            ReportRun.w_update(report_run_id, "finished")

    except BadRequest as e:
        msg = e.description + traceback.format_exc()
        sys.stderr.write(msg + "\n")
        site_rows.append(["Problem " + msg])
        write_spreadsheet(rf, compression, site_rows, era_rows, normal_read_rows)
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
            write_spreadsheet(rf, compression, site_rows, era_rows, normal_read_rows)
    finally:
        if rf is not None:
            rf.close()


def do_post(sess):
    base_name = []
    now = utc_datetime_now()

    if "scenario_id" in request.values:
        scenario_id = req_int("scenario_id")
        scenario = Scenario.get_by_id(sess, scenario_id)
        scenario_props = scenario.props
        base_name.append(scenario.name)
    else:
        scenario_props = {}
        base_name.append("monthly_duration")

    if "finish_year" in request.values:
        year = req_int("finish_year")
        month = req_int("finish_month")
        months = req_int("months")
        start_date, _ = next(
            c_months_c(finish_year=year, finish_month=month, months=months)
        )
        scenario_props["scenario_start_year"] = start_date.year
        scenario_props["scenario_start_month"] = start_date.month
        scenario_props["scenario_duration"] = months

    scenario_props["by_hh"] = req_bool("by_hh")

    try:
        if "site_id" in request.values:
            site_id = req_int("site_id")
            scenario_props["site_codes"] = [Site.get_by_id(sess, site_id).code]

        if "site_codes" in request.values:
            site_codes_raw_str = req_str("site_codes")
            site_codes_str = site_codes_raw_str.strip()
            if len(site_codes_str) > 0:
                site_codes = []

                for site_code in site_codes_str.splitlines():
                    Site.get_by_code(sess, site_code)  # Check valid
                    site_codes.append(site_code)

                scenario_props["site_codes"] = site_codes

        if "supply_id" in request.values:
            supply_id = req_int("supply_id")
            supply = Supply.get_by_id(sess, supply_id)
            era = supply.eras[-1]
            imp_mpan_core, exp_mpan_core = era.imp_mpan_core, era.exp_mpan_core
            scenario_props["mpan_cores"] = [
                exp_mpan_core if imp_mpan_core is None else imp_mpan_core
            ]

        if "compression" in request.values:
            compression = req_bool("compression")
        else:
            compression = True

        user = g.user

        args = (scenario_props, base_name, user.id, compression, now)
        threading.Thread(target=content, args=args).start()
        return redirect("/downloads", 303)
    except BadRequest as e:
        flash(e.description)
        if "scenario_id" in request.values:
            return make_response(
                render_template("e/scenario.html", scenario=scenario), 400
            )
        else:
            now = Datetime.utcnow()
            month_start = Datetime(now.year, now.month, 1) - relativedelta(months=1)
            month_finish = Datetime(now.year, now.month, 1) - HH
            return make_response(
                render_template(
                    "e/ods_monthly_duration.html",
                    month_start=month_start,
                    month_finish=month_finish,
                ),
                400,
            )
