import os
import sys
import threading
import traceback
from collections import defaultdict
from datetime import datetime as Datetime

from dateutil.relativedelta import relativedelta

from flask import flash, g, make_response, render_template, request

import odio

from sqlalchemy import or_, select, true
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

import chellow.dloads
from chellow.e.computer import contract_func, forecast_date
from chellow.e.scenario import make_calcs, make_site_deltas
from chellow.models import (
    Bill,
    Contract,
    Era,
    MeasurementRequirement,
    Scenario,
    Session,
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
    PropDict,
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
from chellow.views import chellow_redirect


CATEGORY_ORDER = {None: 0, "unmetered": 1, "nhh": 2, "amr": 3, "hh": 4}
meter_order = {"hh": 0, "amr": 1, "nhh": 2, "unmetered": 3}


def write_spreadsheet(
    fl,
    compressed,
    site_rows,
    era_rows,
    read_rows,
    bill_check_site_rows,
    bill_check_era_rows,
    is_bill_check,
):
    fl.seek(0)
    fl.truncate()
    with odio.create_spreadsheet(fl, "1.2", compressed=compressed) as f:
        f.append_table("Site Level", site_rows)
        f.append_table("Era Level", era_rows)
        f.append_table("Normal Reads", read_rows)
        if is_bill_check:
            f.append_table("Bill Check Site", bill_check_site_rows)
            f.append_table("Bill Check Era", bill_check_era_rows)


def make_bill_row(titles, bill):
    return [bill.get(t) for t in titles]


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
    era_rows,
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
    site_month_data = defaultdict(int)
    for i, (order, imp_mpan_core, exp_mpan_core, imp_ss, exp_ss) in enumerate(
        sorted(calcs, key=str)
    ):
        if imp_mpan_core == "displaced":
            month_data = {}
            for sname in (
                "import-net",
                "export-net",
                "import-gen",
                "export-gen",
                "import-3rd-party",
                "export-3rd-party",
                "msp",
                "used",
                "used-3rd-party",
                "billed-import-net",
            ):
                for xname in ("kwh", "gbp"):
                    month_data[sname + "-" + xname] = 0
            month_data["billed-supplier-import-net-gbp"] = None
            month_data["billed-dc-import-net-gbp"] = None
            month_data["billed-mop-import-net-gbp"] = None

            month_data["used-kwh"] = month_data["displaced-kwh"] = sum(
                hh["msp-kwh"] for hh in imp_ss.hh_data
            )

            disp_supplier_bill = imp_ss.supplier_bill

            gbp = disp_supplier_bill.get("net-gbp", 0)

            month_data["used-gbp"] = month_data["displaced-gbp"] = gbp

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
                "import-net",
                "export-net",
                "import-gen",
                "export-gen",
                "import-3rd-party",
                "export-3rd-party",
                "displaced",
                "used",
                "used-3rd-party",
                "billed-import-net",
            ):
                for sname in ("kwh", "gbp"):
                    month_data[name + "-" + sname] = 0
            month_data["billed-supplier-import-net-gbp"] = 0
            month_data["billed-dc-import-net-gbp"] = 0
            month_data["billed-mop-import-net-gbp"] = 0

            if imp_ss is not None:
                imp_supplier_contract = imp_ss.supplier_contract

                kwh = sum(hh["msp-kwh"] for hh in imp_ss.hh_data)
                imp_supplier_bill = imp_ss.supplier_bill

                gbp = imp_supplier_bill.get("net-gbp", 0)

                if source_code in ("net", "gen-net"):
                    month_data["import-net-gbp"] += gbp
                    month_data["import-net-kwh"] += kwh
                    month_data["used-gbp"] += gbp
                    month_data["used-kwh"] += kwh
                    if source_code == "gen-net":
                        month_data["export-gen-kwh"] += kwh
                elif source_code == "3rd-party":
                    month_data["import-3rd-party-gbp"] += gbp
                    month_data["import-3rd-party-kwh"] += kwh
                    month_data["used-3rd-party-gbp"] += gbp
                    month_data["used-3rd-party-kwh"] += kwh
                    month_data["used-gbp"] += gbp
                    month_data["used-kwh"] += kwh
                elif source_code == "3rd-party-reverse":
                    month_data["export-3rd-party-gbp"] += gbp
                    month_data["export-3rd-party-kwh"] += kwh
                    month_data["used-3rd-party-gbp"] -= gbp
                    month_data["used-3rd-party-kwh"] -= kwh
                    month_data["used-gbp"] -= gbp
                    month_data["used-kwh"] -= kwh
                elif source_code == "gen":
                    month_data["import-gen-kwh"] += kwh

            if exp_ss is not None:
                exp_supplier_contract = exp_ss.supplier_contract

                kwh = sum(hh["msp-kwh"] for hh in exp_ss.hh_data)
                exp_supplier_bill = exp_ss.supplier_bill

                gbp = exp_supplier_bill.get("net-gbp", 0)

                if source_code in ("net", "gen-net"):
                    month_data["export-net-gbp"] += gbp
                    month_data["export-net-kwh"] += kwh
                    if source_code == "gen-net":
                        month_data["import-gen-kwh"] += kwh

                elif source_code == "3rd-party":
                    month_data["export-3rd-party-gbp"] += gbp
                    month_data["export-3rd-party-kwh"] += kwh
                    month_data["used-3rd-party-gbp"] -= gbp
                    month_data["used-3rd-party-kwh"] -= kwh
                    month_data["used-gbp"] -= gbp
                    month_data["used-kwh"] -= kwh
                elif source_code == "3rd-party-reverse":
                    month_data["import-3rd-party-gbp"] += gbp
                    month_data["import-3rd-party-kwh"] += kwh
                    month_data["used-3rd-party-gbp"] += gbp
                    month_data["used-3rd-party-kwh"] += kwh
                    month_data["used-gbp"] += gbp
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
                month_data["import-3rd-party-gbp"] += gbp
                month_data["used-3rd-party-gbp"] += gbp
            else:
                month_data["import-net-gbp"] += gbp
            month_data["used-gbp"] += gbp

            generator_type = sss.generator_type_code
            if source_code in ("gen", "gen-net"):
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
                month_data["billed-import-net-kwh"] += proportion * float(bill.kwh)
                bill_prop_gbp = proportion * float(bill.net)
                month_data["billed-import-net-gbp"] += bill_prop_gbp
                if bill_role_code == "X":
                    month_data["billed-supplier-import-net-gbp"] += bill_prop_gbp
                elif bill_role_code == "C":
                    month_data["billed-dc-import-net-gbp"] += bill_prop_gbp
                elif bill_role_code == "M":
                    month_data["billed-mop-import-net-gbp"] += bill_prop_gbp
                else:
                    raise BadRequest("Role code not recognized.")

            if imp_ss is None:
                imp_supplier_contract_name = None
                pc_code = exp_ss.pc_code
            else:
                if imp_supplier_contract is None:
                    imp_supplier_contract_name = ""
                else:
                    imp_supplier_contract_name = imp_supplier_contract.name
                pc_code = imp_ss.pc_code

            if exp_ss is None:
                exp_supplier_contract_name = None
            else:
                if exp_supplier_contract is None:
                    exp_supplier_contract_name = ""
                else:
                    exp_supplier_contract_name = exp_supplier_contract.name

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
                        "import-net",
                        "export-net",
                        "import-gen",
                        "export-gen",
                        "import-3rd-party",
                        "export-3rd-party",
                        "displaced",
                        "used",
                        "used-3rd-party",
                        "billed-import-net",
                    ):
                        for sname in ("kwh", "gbp"):
                            month_data[name + "-" + sname] = 0
                    month_data["billed-supplier-import-net-gbp"] = 0
                    month_data["billed-dc-import-net-gbp"] = 0
                    month_data["billed-mop-import-net-gbp"] = 0

                    for bill in bills:
                        bill_role_code = bill.batch.contract.market_role.code
                        bill_start = bill.start_date
                        bill_finish = bill.finish_date
                        bill_duration = (bill_finish - bill_start).total_seconds() + (
                            30 * 60
                        )
                        overlap_duration = (
                            min(bill_finish, chunk_finish)
                            - max(bill_start, chunk_start)
                        ).total_seconds() + (30 * 60)
                        proportion = overlap_duration / bill_duration
                        bill_prop_kwh = proportion * float(bill.kwh)
                        bill_prop_gbp = proportion * float(bill.net)
                        if bill_role_code == "X":
                            key = "billed-supplier-import-net-gbp"
                        elif bill_role_code == "C":
                            key = "billed-dc-import-net-gbp"
                        elif bill_role_code == "M":
                            key = "billed-mop-import-net-gbp"
                        else:
                            raise BadRequest("Role code not recognized.")

                        for data in month_data, site_month_data:
                            data["billed-import-net-kwh"] += bill_prop_kwh
                            data["billed-import-net-gbp"] += bill_prop_gbp
                            data[key] += bill_prop_gbp

                    imp_supplier_contract = last_era.imp_supplier_contract
                    exp_supplier_contract = last_era.exp_supplier_contract
                    out = [
                        now,
                        last_era.imp_mpan_core,
                        None
                        if imp_supplier_contract is None
                        else imp_supplier_contract.name,
                        last_era.exp_mpan_core,
                        None
                        if exp_supplier_contract is None
                        else exp_supplier_contract.name,
                        chunk_start,
                        last_era.meter_category,
                        last_era.supply.source.code,
                        None,
                        last_era.supply.name,
                        last_era.msn,
                        last_era.pc.code,
                        site.code,
                        site.name,
                        None,
                        finish_date,
                    ] + [month_data[t] for t in summary_titles]

                    era_rows.append([make_val(v) for v in out])
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
                        "import-net",
                        "export-net",
                        "import-gen",
                        "export-gen",
                        "import-3rd-party",
                        "export-3rd-party",
                        "displaced",
                        "used",
                        "used-3rd-party",
                        "billed-import-net",
                    ):
                        for sname in ("kwh", "gbp"):
                            month_data[name + "-" + sname] = 0
                    month_data["billed-supplier-import-net-gbp"] = 0
                    month_data["billed-dc-import-net-gbp"] = 0
                    month_data["billed-mop-import-net-gbp"] = 0

                    for bill in bills:
                        bill_role_code = bill.batch.contract.market_role.code
                        bill_start = bill.start_date
                        bill_finish = bill.finish_date
                        bill_duration = (bill_finish - bill_start).total_seconds() + (
                            30 * 60
                        )
                        overlap_duration = (
                            min(bill_finish, chunk_finish)
                            - max(bill_start, chunk_start)
                        ).total_seconds() + (30 * 60)
                        proportion = overlap_duration / bill_duration
                        bill_prop_kwh = proportion * float(bill.kwh)
                        bill_prop_gbp = proportion * float(bill.net)
                        if bill_role_code == "X":
                            key = "billed-supplier-import-net-gbp"
                        elif bill_role_code == "C":
                            key = "billed-dc-import-net-gbp"
                        elif bill_role_code == "M":
                            key = "billed-mop-import-net-gbp"
                        else:
                            raise BadRequest("Role code not recognized.")

                        for data in month_data, site_month_data:
                            data["billed-import-net-kwh"] += bill_prop_kwh
                            data["billed-import-net-gbp"] += bill_prop_gbp
                            data[key] += bill_prop_gbp

                    imp_supplier_contract = first_era.imp_supplier_contract
                    exp_supplier_contract = first_era.exp_supplier_contract
                    out = [
                        now,
                        last_era.imp_mpan_core,
                        None
                        if imp_supplier_contract is None
                        else imp_supplier_contract.name,
                        last_era.exp_mpan_core,
                        None
                        if exp_supplier_contract is None
                        else exp_supplier_contract.name,
                        None,
                        last_era.meter_category,
                        last_era.supply.source.code,
                        None,
                        last_era.supply.name,
                        last_era.msn,
                        last_era.pc.code,
                        site.code,
                        site.name,
                        None,
                        finish_date,
                    ] + [month_data[t] for t in summary_titles]

                    era_rows.append([make_val(v) for v in out])
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
    sess.rollback()
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

    try:
        comp = report_context["computer"]
    except KeyError:
        comp = report_context["computer"] = {}

    try:
        rate_cache = comp["rates"]
    except KeyError:
        rate_cache = comp["rates"] = {}

    try:
        ind_cont = report_context["contract_names"]
    except KeyError:
        ind_cont = report_context["contract_names"] = {}

    sess = None
    try:
        sess = Session()

        start_year = scenario_props["scenario_start_year"]
        start_month = scenario_props["scenario_start_month"]
        months = scenario_props["scenario_duration"]

        month_pairs = list(
            c_months_u(start_year=start_year, start_month=start_month, months=months)
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

        sites = sess.query(Site).distinct().order_by(Site.code)

        mpan_cores = scenario_props["mpan_cores"]
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

            sites = (
                sites.join(SiteEra)
                .join(Era)
                .join(Supply)
                .where(Supply.id.in_(supply_ids))
            )

        site_codes = scenario_props["site_codes"]
        if site_codes is not None:
            if len(site_codes) == 1:
                base_name.append("site")
                base_name.append(site_codes[0])
            else:
                base_name.append("sitecodes")
            sites = sites.where(Site.code.in_(site_codes))

        user = User.get_by_id(sess, user_id)
        running_name, finished_name = chellow.dloads.make_names(
            "_".join(base_name) + ".ods", user
        )

        rf = open(running_name, "wb")
        site_rows = []
        era_rows = []
        normal_read_rows = []
        bill_check_site_rows = []
        bill_check_era_rows = []

        for rate_script in scenario_props.get("local_rates", []):
            contract_id = rate_script["contract_id"]
            try:
                cont_cache = rate_cache[contract_id]
            except KeyError:
                cont_cache = rate_cache[contract_id] = {}

            try:
                rate_script_start = rate_script["start_date"]
            except KeyError:
                raise BadRequest(
                    f"Problem in the scenario properties. Can't find the 'start_date' "
                    f"key of the contract {contract_id} in the 'local_rates' map."
                )

            try:
                rate_script_start = rate_script["start_date"]
            except KeyError:
                raise BadRequest(
                    f"Problem in the scenario properties. Can't find the 'start_date' "
                    f"key of the contract {contract_id} in the 'local_rates' map."
                )

            props = PropDict("scenario properties", rate_script["script"])
            for dt in hh_range(
                report_context, rate_script_start, rate_script["finish_date"]
            ):
                cont_cache[dt] = props

        for rate_script in scenario_props.get("industry_rates", []):
            contract_name = rate_script["contract_name"]
            try:
                cont_cache = ind_cont[contract_name]
            except KeyError:
                cont_cache = ind_cont[contract_name] = {}

            rfinish = rate_script["finish_date"]
            if rfinish is None:
                raise BadRequest(
                    f"For the industry rate {contract_name} the finish_date can't be "
                    f"null."
                )
            for dt in hh_range(report_context, rate_script["start_date"], rfinish):
                cont_cache[dt] = PropDict("scenario properties", rate_script["script"])

        by_hh = scenario_props.get("by_hh", False)

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
            "site-id",
            "site-name",
            "associated-site-ids",
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
        summary_titles = [
            "import-net-kwh",
            "export-net-kwh",
            "import-gen-kwh",
            "export-gen-kwh",
            "import-3rd-party-kwh",
            "export-3rd-party-kwh",
            "displaced-kwh",
            "used-kwh",
            "used-3rd-party-kwh",
            "import-net-gbp",
            "export-net-gbp",
            "import-gen-gbp",
            "export-gen-gbp",
            "import-3rd-party-gbp",
            "export-3rd-party-gbp",
            "displaced-gbp",
            "used-gbp",
            "used-3rd-party-gbp",
            "billed-import-net-kwh",
            "billed-import-net-gbp",
            "billed-supplier-import-net-gbp",
            "billed-dc-import-net-gbp",
            "billed-mop-import-net-gbp",
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
                    or_(Era.finish_date == null(), Era.finish_date >= start_date_utc),
                )
                .distinct()
                .order_by(Contract.id)
            )
            if supply_ids is not None:
                conts = conts.where(Supply.id.in_(supply_ids))
            for cont in conts:
                title_func = contract_func(report_context, cont, "virtual_bill_titles")
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
        site_rows.append(site_header_titles + summary_titles)
        era_rows.append(era_titles)
        bill_check_site_rows.append(site_header_titles + summary_titles)
        bill_check_era_rows.append(era_titles)

        sites = sites.all()
        normal_reads = set()

        for month_start, month_finish in month_pairs:
            data_source_bill = Object()
            data_source_bill.start_date = month_start
            data_source_bill.finish_date = month_finish

            for site in sites:
                if by_hh:
                    sf = [
                        (d, d)
                        for d in hh_range(report_context, month_start, month_finish)
                    ]
                else:
                    sf = [(month_start, month_finish)]

                for start, finish in sf:
                    try:
                        normal_reads = normal_reads | _process_site(
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
                            era_rows,
                            site_rows,
                            None,
                        )
                        if is_bill_check:
                            _process_site(
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
                                bill_check_era_rows,
                                bill_check_site_rows,
                                data_source_bill,
                            )
                    except BadRequest as e:
                        raise BadRequest(f"Site Code {site.code}: {e.description}")

            normal_read_rows = [["mpan_core", "date", "msn", "type", "registers"]]
            for mpan_core, r in sorted(list(normal_reads)):
                row = [mpan_core, r.date, r.msn, r.type] + list(r.reads)
                normal_read_rows.append(row)

            write_spreadsheet(
                rf,
                compression,
                site_rows,
                era_rows,
                normal_read_rows,
                bill_check_site_rows,
                bill_check_era_rows,
                is_bill_check,
            )
    except BadRequest as e:
        msg = e.description + traceback.format_exc()
        sys.stderr.write(msg + "\n")
        site_rows.append(["Problem " + msg])
        write_spreadsheet(
            rf,
            compression,
            site_rows,
            era_rows,
            normal_read_rows,
            bill_check_site_rows,
            bill_check_era_rows,
            is_bill_check,
        )
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + "\n")
        site_rows.append(["Problem " + msg])
        write_spreadsheet(
            rf,
            compression,
            site_rows,
            era_rows,
            normal_read_rows,
            bill_check_site_rows,
            bill_check_era_rows,
            is_bill_check,
        )
    finally:
        if sess is not None:
            sess.close()
        try:
            rf.close()
            os.rename(running_name, finished_name)
        except BaseException:
            msg = traceback.format_exc()
            r_name, f_name = chellow.dloads.make_names("error.txt", user)
            ef = open(r_name, "w")
            ef.write(msg + "\n")
            ef.close()


def do_post(sess):

    base_name = []
    now = utc_datetime_now()

    if "scenario_id" in request.values:
        scenario_id = req_int("scenario_id")
        scenario = Scenario.get_by_id(sess, scenario_id)
        scenario_props = scenario.props
        base_name.append(scenario.name)

    else:
        year = req_int("finish_year")
        month = req_int("finish_month")
        months = req_int("months")
        start_date, _ = next(
            c_months_c(finish_year=year, finish_month=month, months=months)
        )
        by_hh = req_bool("by_hh")
        scenario_props = {
            "scenario_start_year": start_date.year,
            "scenario_start_month": start_date.month,
            "scenario_duration": months,
            "by_hh": by_hh,
        }
        base_name.append("monthly_duration")

    try:
        site_codes = None
        if "site_id" in request.values:
            site_id = req_int("site_id")
            site_codes = [Site.get_by_id(sess, site_id).code]

        if "site_codes" in request.values:
            site_codes_raw_str = req_str("site_codes")
            site_codes_str = site_codes_raw_str.strip()
            if len(site_codes_str) > 0:
                if site_codes is None:
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
            mpan_cores = [exp_mpan_core if imp_mpan_core is None else imp_mpan_core]
        else:
            mpan_cores = None
        scenario_props["mpan_cores"] = mpan_cores

        if "compression" in request.values:
            compression = req_bool("compression")
        else:
            compression = True

        is_bill_check = req_bool("is_bill_check")

        user = g.user

        args = (
            scenario_props,
            base_name,
            user.id,
            compression,
            now,
            is_bill_check,
        )
        threading.Thread(target=content, args=args).start()
        return chellow_redirect("/downloads", 303)
    except BadRequest as e:
        flash(e.description)
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
