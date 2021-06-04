import csv
import os
import sys
import threading
import traceback
from collections import defaultdict
from datetime import datetime as Datetime
from io import StringIO

from dateutil.relativedelta import relativedelta

from flask import flash, g, make_response, render_template, request

import odio

from sqlalchemy import or_, select, true
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

import chellow.computer
import chellow.dloads
from chellow.computer import SupplySource, contract_func, datum_range
from chellow.models import (
    Bill,
    Contract,
    Era,
    Llfc,
    MeasurementRequirement,
    Mtc,
    Pc,
    Scenario,
    Session,
    Site,
    SiteEra,
    Source,
    Ssc,
    Supply,
    Tpr,
)
from chellow.utils import (
    HH,
    PropDict,
    c_months_c,
    c_months_u,
    ct_datetime,
    hh_format,
    hh_max,
    hh_min,
    hh_range,
    make_val,
    parse_hh_start,
    req_bool,
    req_int,
    req_str,
    to_ct,
    to_utc,
    utc_datetime_now,
)
from chellow.views import chellow_redirect


CATEGORY_ORDER = {None: 0, "unmetered": 1, "nhh": 2, "amr": 3, "hh": 4}
meter_order = {"hh": 0, "amr": 1, "nhh": 2, "unmetered": 3}


def write_spreadsheet(fl, compressed, site_rows, era_rows, read_rows):
    fl.seek(0)
    fl.truncate()
    with odio.create_spreadsheet(fl, "1.2", compressed=compressed) as f:
        f.append_table("Site Level", site_rows)
        f.append_table("Era Level", era_rows)
        f.append_table("Normal Reads", read_rows)


def make_bill_row(titles, bill):
    return [bill.get(t) for t in titles]


def _make_site_deltas(
    sess, report_context, site, scenario_hh, forecast_from, supply_id
):
    site_scenario_hh = scenario_hh.get(site.code, {})

    site_deltas = {"hhs": {}}
    delts = site_deltas["supply_deltas"] = {}
    for is_import in (True, False):
        delts[is_import] = {}
        for src in ("gen", "net", "gen-net", "3rd-party", "3rd-party-reverse", "sub"):
            delts[is_import][src] = {"site": {}}

    earliest_delta = to_utc(Datetime.max)
    latest_delta = to_utc(Datetime.min)

    found_hh = False
    for typ in ("used", "generated", "parasitic", "gen_net"):
        hh_str = site_scenario_hh.get(typ, "")
        hh_data = site_scenario_hh[typ] = {}
        for row in csv.reader(StringIO(hh_str)):
            cells = [cell.strip() for cell in row]
            if len("".join(cells)) == 0:
                continue

            if len(cells) != 2:
                raise BadRequest(
                    "Can't interpret the row "
                    + str(cells)
                    + " it should be of the form 'timestamp, kWh'"
                )

            date_str, kwh_str = cells
            ts = parse_hh_start(date_str)
            earliest_delta = min(ts, earliest_delta)
            latest_delta = max(ts, latest_delta)
            try:
                hh_data[ts] = float(kwh_str)
            except ValueError as e:
                raise BadRequest(
                    "When looking at " + typ + " hh data, can't parse the "
                    "kWh at " + date_str + ": " + str(e)
                )
            found_hh = True

    if not found_hh:
        return site_deltas

    scenario_used = site_scenario_hh["used"]
    scenario_generated = site_scenario_hh["generated"]
    scenario_parasitic = site_scenario_hh["parasitic"]
    scenario_gen_net = site_scenario_hh["gen_net"]

    earliest_delta_ct = to_ct(earliest_delta)
    for month_start, month_finish in c_months_u(
        earliest_delta_ct.year, earliest_delta_ct.month, months=None
    ):
        if month_start > latest_delta:
            break
        chunk_start = hh_max(month_start, earliest_delta)
        chunk_finish = hh_min(month_finish, latest_delta)

        site_ds = chellow.computer.SiteSource(
            sess, site, chunk_start, chunk_finish, forecast_from, report_context
        )
        hh_map = dict((h["start-date"], h) for h in site_ds.hh_data)

        for era in (
            sess.query(Era)
            .join(SiteEra)
            .join(Pc)
            .filter(
                SiteEra.site == site,
                SiteEra.is_physical == true(),
                Era.imp_mpan_core != null(),
                Pc.code != "00",
                Era.start_date <= chunk_finish,
                or_(Era.finish_date == null(), Era.finish_date >= chunk_start),
            )
        ):

            if supply_id is not None and era.supply_id != supply_id:
                continue

            ss_start = hh_max(era.start_date, chunk_start)
            ss_finish = hh_min(era.finish_date, chunk_finish)

            ss = SupplySource(
                sess, ss_start, ss_finish, forecast_from, era, True, report_context
            )

            for hh in ss.hh_data:
                sdatum = hh_map[hh["start-date"]]
                sdatum["import-net-kwh"] += hh["msp-kwh"]
                sdatum["used-kwh"] += hh["msp-kwh"]

        for era in (
            sess.query(Era)
            .join(SiteEra)
            .join(Pc)
            .join(Supply)
            .join(Source)
            .filter(
                SiteEra.site == site,
                SiteEra.is_physical == true(),
                Era.imp_mpan_core != null(),
                Era.start_date <= chunk_finish,
                or_(Era.finish_date == null(), Era.finish_date >= chunk_start),
                Source.code == "gen-net",
            )
        ):

            if supply_id is not None and era.supply_id != supply_id:
                continue

            ss_start = hh_max(era.start_date, chunk_start)
            ss_finish = hh_min(era.finish_date, chunk_finish)

            ss = SupplySource(
                sess, ss_start, ss_finish, forecast_from, era, False, report_context
            )

            for hh in ss.hh_data:
                sdatum = hh_map[hh["start-date"]]
                try:
                    sdatum["gen-net-kwh"] += hh["msp-kwh"]
                except KeyError:
                    sdatum["gen-net-kwh"] = hh["msp-kwh"]

        for hh_start, hh in hh_map.items():
            if hh_start in scenario_used:
                used_delt = scenario_used[hh_start] - hh["used-kwh"]
                imp_net_delt = 0
                exp_net_delt = 0

                if used_delt < 0:
                    diff = hh["import-net-kwh"] + used_delt
                    if diff < 0:
                        imp_net_delt -= hh["import-net-kwh"]
                        exp_net_delt -= diff
                    else:
                        imp_net_delt += used_delt
                else:
                    diff = hh["export-net-kwh"] - used_delt
                    if diff < 0:
                        exp_net_delt -= hh["export-net-kwh"]
                        imp_net_delt -= diff
                    else:
                        exp_net_delt -= used_delt

                try:
                    delts[False]["net"]["site"][hh_start] += exp_net_delt
                except KeyError:
                    delts[False]["net"]["site"][hh_start] = exp_net_delt

                try:
                    delts[True]["net"]["site"][hh_start] += imp_net_delt
                except KeyError:
                    delts[True]["net"]["site"][hh_start] = imp_net_delt

                hh["import-net-kwh"] += imp_net_delt
                hh["export-net-kwh"] += exp_net_delt
                hh["used-kwh"] += used_delt
                hh["msp-kwh"] -= exp_net_delt

            if hh_start in scenario_generated:
                imp_gen_delt = scenario_generated[hh_start] - hh["import-gen-kwh"]
                imp_net_delt = 0
                exp_net_delt = 0

                if imp_gen_delt < 0:
                    diff = hh["export-net-kwh"] + imp_gen_delt
                    if diff < 0:
                        exp_net_delt -= hh["export-net-kwh"]
                        imp_net_delt -= diff
                    else:
                        exp_net_delt += imp_gen_delt
                else:
                    diff = hh["import-net-kwh"] - imp_gen_delt
                    if diff < 0:
                        imp_net_delt -= hh["import-net-kwh"]
                        exp_net_delt -= diff
                    else:
                        imp_net_delt -= imp_gen_delt

                try:
                    delts[True]["gen"]["site"][hh_start] += imp_gen_delt
                except KeyError:
                    delts[True]["gen"]["site"][hh_start] = imp_gen_delt

                try:
                    delts[False]["net"]["site"][hh_start] += exp_net_delt
                except KeyError:
                    delts[False]["net"]["site"][hh_start] = exp_net_delt

                try:
                    delts[True]["net"]["site"][hh_start] += imp_net_delt
                except KeyError:
                    delts[True]["net"]["site"][hh_start] = imp_net_delt

                hh["import-net-kwh"] += imp_net_delt
                hh["export-net-kwh"] += exp_net_delt
                hh["import-gen-kwh"] += imp_gen_delt
                hh["msp-kwh"] -= imp_net_delt

            if hh_start in scenario_parasitic:
                exp_gen_delt = scenario_parasitic[hh_start] - hh["export-gen-kwh"]
                imp_net_delt = 0
                exp_net_delt = 0

                if exp_gen_delt < 0:
                    diff = hh["import-net-kwh"] + exp_gen_delt
                    if diff < 0:
                        imp_net_delt -= hh["import-net-kwh"]
                        exp_net_delt -= diff
                    else:
                        imp_net_delt += exp_gen_delt
                else:
                    diff = hh["export-net-kwh"] - exp_gen_delt
                    if diff < 0:
                        exp_net_delt -= hh["export-net-kwh"]
                        imp_net_delt -= diff
                    else:
                        exp_net_delt -= exp_gen_delt

                try:
                    delts[False]["gen"]["site"][hh_start] += imp_gen_delt
                except KeyError:
                    delts[False]["gen"]["site"][hh_start] = exp_gen_delt

                try:
                    delts[False]["net"]["site"][hh_start] += exp_net_delt
                except KeyError:
                    delts[False]["net"]["site"][hh_start] = exp_net_delt

                try:
                    delts[True]["net"]["site"][hh_start] += imp_net_delt
                except KeyError:
                    delts[True]["net"]["site"][hh_start] = imp_net_delt

                hh["import-net-kwh"] += imp_net_delt
                hh["export-net-kwh"] += exp_net_delt
                hh["export-gen-kwh"] += exp_gen_delt
                hh["msp-kwh"] -= imp_net_delt

            if hh_start in scenario_gen_net:
                gen_net_delt = scenario_gen_net[hh_start] - hh["gen-net-kwh"]

                try:
                    delts[False]["gen-net"]["site"][hh_start] += gen_net_delt
                except KeyError:
                    delts[False]["gen-net"]["site"][hh_start] = gen_net_delt

                hh["import-gen-kwh"] += gen_net_delt
                hh["export-net-kwh"] += gen_net_delt

            site_deltas["hhs"][hh_start] = hh

    sup_deltas = site_deltas["supply_deltas"][False]["net"]["site"]
    if all(v == 0 for v in sup_deltas.values()):
        sup_deltas.clear()

    return site_deltas


def _make_calcs(
    sess,
    site,
    start_date,
    finish_date,
    supply_id,
    site_deltas,
    forecast_from,
    report_context,
    era_maps,
):
    site_gen_types = set()
    calcs = []
    for era in (
        sess.query(Era)
        .join(SiteEra)
        .join(Pc)
        .filter(
            SiteEra.site == site,
            SiteEra.is_physical == true(),
            Era.start_date <= finish_date,
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
        )
        .options(
            joinedload(Era.ssc),
            joinedload(Era.dc_contract),
            joinedload(Era.mop_contract),
            joinedload(Era.imp_supplier_contract),
            joinedload(Era.exp_supplier_contract),
            joinedload(Era.channels),
            joinedload(Era.imp_llfc).joinedload(Llfc.voltage_level),
            joinedload(Era.exp_llfc).joinedload(Llfc.voltage_level),
            joinedload(Era.cop),
            joinedload(Era.supply).joinedload(Supply.dno),
            joinedload(Era.supply).joinedload(Supply.gsp_group),
            joinedload(Era.supply).joinedload(Supply.source),
            joinedload(Era.mtc).joinedload(Mtc.meter_type),
            joinedload(Era.pc),
            joinedload(Era.site_eras),
        )
        .order_by(Pc.code)
    ):

        supply = era.supply
        if supply.generator_type is not None:
            site_gen_types.add(supply.generator_type.code)

        if supply_id is not None and supply.id != supply_id:
            continue

        ss_start = hh_max(era.start_date, start_date)
        ss_finish = hh_min(era.finish_date, finish_date)

        if era.imp_mpan_core is None:
            imp_ss = None
        else:
            sup_deltas = site_deltas["supply_deltas"][True][supply.source.code]

            imp_ss = SupplySource(
                sess,
                ss_start,
                ss_finish,
                forecast_from,
                era,
                True,
                report_context,
                era_maps=era_maps,
                deltas=sup_deltas,
            )

        if era.exp_mpan_core is None:
            exp_ss = None
            measurement_type = imp_ss.measurement_type
        else:
            sup_deltas = site_deltas["supply_deltas"][False][supply.source.code]

            exp_ss = SupplySource(
                sess,
                ss_start,
                ss_finish,
                forecast_from,
                era,
                False,
                report_context,
                era_maps=era_maps,
                deltas=sup_deltas,
            )
            measurement_type = exp_ss.measurement_type

        order = meter_order[measurement_type]
        calcs.append((order, era.imp_mpan_core, era.exp_mpan_core, imp_ss, exp_ss))

    # Check if gen deltas haven't been consumed
    extra_sss = set()
    for is_imp in (True, False):
        sup_deltas = site_deltas["supply_deltas"][is_imp]["gen"]
        if (
            len(list(t for t in sup_deltas["site"] if start_date <= t <= finish_date))
            > 0
        ):
            extra_sss.add(is_imp)

    displaced_era = chellow.computer.displaced_era(
        sess,
        report_context,
        site,
        start_date,
        finish_date,
        forecast_from,
        has_scenario_generation=len(extra_sss) > 0,
    )

    if len(extra_sss) > 0:
        if True in extra_sss:
            sup_deltas = site_deltas["supply_deltas"][True]["gen"]
            imp_ss_name = site.code + "_extra_gen_TRUE"
            imp_ss = ScenarioSource(
                sess,
                start_date,
                finish_date,
                True,
                report_context,
                sup_deltas,
                displaced_era.imp_supplier_contract,
                imp_ss_name,
            )
        else:
            imp_ss_name = imp_ss = None
        if False in extra_sss:
            exp_ss_name = site.code + "_extra_gen_FALSE"
            sup_deltas = site_deltas["supply_deltas"][False]["gen"]
            exp_ss = ScenarioSource(
                sess,
                start_date,
                finish_date,
                False,
                report_context,
                sup_deltas,
                displaced_era.imp_supplier_contract,
                imp_ss_name,
            )
        else:
            exp_ss_name = exp_ss = None

        calcs.append((0, imp_ss_name, exp_ss_name, imp_ss, exp_ss))

    # Check if exp net deltas haven't been consumed
    sup_deltas = site_deltas["supply_deltas"][False]["net"]
    if len(list(t for t in sup_deltas["site"] if start_date <= t <= finish_date)) > 0:
        ss_name = site.code + "_extra_net_export"
        ss = SupplySource(
            sess,
            start_date,
            finish_date,
            forecast_from,
            displaced_era,
            False,
            report_context,
            era_maps=era_maps,
            deltas=sup_deltas,
        )

        calcs.append((0, None, ss_name, None, ss))
    return calcs, displaced_era, site_gen_types


def _process_site(
    sess,
    report_context,
    forecast_from,
    start_date,
    finish_date,
    site,
    site_deltas,
    supply_id,
    era_maps,
    now,
    summary_titles,
    title_dict,
    era_rows,
    site_rows,
):

    calcs, displaced_era, site_gen_types = _make_calcs(
        sess,
        site,
        start_date,
        finish_date,
        supply_id,
        site_deltas,
        forecast_from,
        report_context,
        era_maps,
    )

    site_month_data = defaultdict(int)
    site_ds = chellow.computer.SiteSource(
        sess,
        site,
        start_date,
        finish_date,
        forecast_from,
        report_context,
        displaced_era,
        era_maps=era_maps,
        deltas=site_deltas,
    )

    bill_ids = set()

    if displaced_era is not None and supply_id is None:
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
            hh["msp-kwh"] for hh in site_ds.hh_data
        )

        disp_supplier_contract = displaced_era.imp_supplier_contract
        disp_vb_function = chellow.computer.contract_func(
            report_context, disp_supplier_contract, "displaced_virtual_bill"
        )
        if disp_vb_function is None:
            raise BadRequest(
                f"The supplier contract {disp_supplier_contract.name} "
                f" doesn't have the displaced_virtual_bill() function."
            )
        disp_vb_function(site_ds)
        disp_supplier_bill = site_ds.supplier_bill

        try:
            gbp = disp_supplier_bill["net-gbp"]
        except KeyError:
            disp_supplier_bill["problem"] += (
                f"For the supply {site_ds.mpan_core} the virtual bill "
                f"{disp_supplier_bill} from the contract {disp_supplier_contract.name} "
                f" does not contain the net-gbp key."
            )

        month_data["used-gbp"] = month_data["displaced-gbp"] = gbp

        out = (
            [
                now,
                None,
                disp_supplier_contract.name,
                None,
                None,
                displaced_era.meter_category,
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

    site_category = None
    site_sources = set()
    normal_reads = set()
    for i, (order, imp_mpan_core, exp_mpan_core, imp_ss, exp_ss) in enumerate(
        sorted(calcs, key=str)
    ):
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
            if imp_supplier_contract is not None:
                import_vb_function = contract_func(
                    report_context, imp_supplier_contract, "virtual_bill"
                )
                if import_vb_function is None:
                    raise BadRequest(
                        f"The supplier contract {imp_supplier_contract.name} "
                        " doesn't have the virtual_bill() function."
                    )
                import_vb_function(imp_ss)

            kwh = sum(hh["msp-kwh"] for hh in imp_ss.hh_data)
            imp_supplier_bill = imp_ss.supplier_bill

            try:
                gbp = imp_supplier_bill["net-gbp"]
            except KeyError:
                gbp = 0
                imp_supplier_bill["problem"] += (
                    f"For the supply {imp_ss.mpan_core} the virtual bill "
                    + f"{imp_supplier_bill} from the contract "
                    + f"{imp_supplier_contract.name} does not contain the "
                    + "net-gbp key."
                )

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
            if exp_supplier_contract is not None:
                export_vb_function = contract_func(
                    report_context, exp_supplier_contract, "virtual_bill"
                )
                export_vb_function(exp_ss)

            kwh = sum(hh["msp-kwh"] for hh in exp_ss.hh_data)
            exp_supplier_bill = exp_ss.supplier_bill
            try:
                gbp = exp_supplier_bill["net-gbp"]
            except KeyError:
                exp_supplier_bill["problem"] += (
                    f"For the supply {imp_ss.mpan_core} the virtual bill "
                    f"{imp_supplier_bill} from the contract "
                    f"{imp_supplier_contract.name} does not contain the net-gbp key."
                )

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
        if dc_contract is not None:
            sss.contract_func(dc_contract, "virtual_bill")(sss)
        dc_bill = sss.dc_bill
        gbp = dc_bill["net-gbp"]

        mop_contract = sss.mop_contract
        if mop_contract is not None:
            mop_bill_function = sss.contract_func(mop_contract, "virtual_bill")
            mop_bill_function(sss)
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

        era_associates = set()
        if mop_contract is not None:
            era_associates.update(
                {s.site.code for s in sss.era.site_eras if not s.is_physical}
            )

            for bill in sess.query(Bill).filter(
                Bill.supply == supply,
                Bill.start_date <= finish_date,
                Bill.finish_date >= start_date,
            ):
                if bill.id in bill_ids:
                    continue

                bill_ids.add(bill.id)
                bill_role_code = bill.batch.contract.market_role.code
                bill_start = bill.start_date
                bill_finish = bill.finish_date
                bill_duration = (bill_finish - bill_start).total_seconds() + (30 * 60)
                overlap_duration = (
                    min(bill_finish, finish_date) - max(bill_start, start_date)
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
            out += [None] + make_bill_row(title_dict["imp-supplier"], imp_supplier_bill)
            for n in imp_ss.normal_reads:
                normal_reads.add((imp_mpan_core, n))
        if exp_ss is not None:
            out += [None] + make_bill_row(title_dict["exp-supplier"], exp_supplier_bill)

        for k, v in month_data.items():
            site_month_data[k] += v
        era_rows.append([make_val(v) for v in out])

    for bill in (
        sess.query(Bill)
        .join(Supply)
        .join(Supply.eras)
        .join(SiteEra)
        .filter(
            SiteEra.site == site,
            SiteEra.is_physical == true(),
            Bill.start_date <= finish_date,
            Bill.finish_date >= start_date,
        )
    ):
        if bill.id in bill_ids:
            continue

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

        for bill in sess.query(Bill).filter(
            Bill.supply == bill.supply,
            Bill.start_date <= finish_date,
            Bill.finish_date >= start_date,
        ):
            bill_ids.add(bill.id)
            bill_role_code = bill.batch.contract.market_role.code
            bill_start = bill.start_date
            bill_finish = bill.finish_date
            bill_duration = (bill_finish - bill_start).total_seconds() + (30 * 60)
            overlap_duration = (
                min(bill_finish, finish_date) - max(bill_start, start_date)
            ).total_seconds() + (30 * 60)
            proportion = overlap_duration / bill_duration
            month_data["billed-import-net-kwh"] += proportion * float(bill.kwh)
            bill_prop_gbp = proportion * float(bill.net)
            month_data["billed-import-net-gbp"] += bill_prop_gbp
            if bill_role_code == "X":
                month_data["billed-supplier-import-net-gbp"] += bill_prop_gbp
                site_month_data["billed-supplier-import-net-gbp"] += bill_prop_gbp
            elif bill_role_code == "C":
                month_data["billed-dc-import-net-gbp"] += bill_prop_gbp
                site_month_data["billed-dc-import-net-gbp"] += bill_prop_gbp
            elif bill_role_code == "M":
                month_data["billed-mop-import-net-gbp"] += bill_prop_gbp
                site_month_data["billed-mop-import-net-gbp"] += bill_prop_gbp
            else:
                raise BadRequest("Role code not recognized.")

        era = sess.execute(
            select(Era)
            .filter(Era.supply == bill.supply)
            .order_by(Era.start_date.desc())
        ).first()[0]
        imp_supplier_contract = era.imp_supplier_contract
        exp_supplier_contract = era.exp_supplier_contract
        out = [
            now,
            era.imp_mpan_core,
            None if imp_supplier_contract is None else imp_supplier_contract.name,
            era.exp_mpan_core,
            None if exp_supplier_contract is None else exp_supplier_contract.name,
            era.meter_category,
            era.supply.source.code,
            None,
            era.supply.name,
            era.msn,
            era.pc.code,
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


def content(
    scenario_props, base_name, site_id, supply_id, user, compression, site_codes, now
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
            forecast_from = chellow.computer.forecast_date()
        else:
            forecast_from = to_utc(forecast_from)

        sites = sess.query(Site).distinct().order_by(Site.code)
        if site_id is not None:
            site = Site.get_by_id(sess, site_id)
            sites = sites.filter(Site.id == site.id)
            base_name.append("site")
            base_name.append(site.code)
        if supply_id is not None:
            supply = Supply.get_by_id(sess, supply_id)
            base_name.append("supply")
            base_name.append(str(supply.id))
            sites = sites.join(SiteEra).join(Era).filter(Era.supply == supply)
        if len(site_codes) > 0:
            base_name.append("sitecodes")
            sites = sites.filter(Site.code.in_(site_codes))

        running_name, finished_name = chellow.dloads.make_names(
            "_".join(base_name) + ".ods", user
        )

        rf = open(running_name, "wb")
        site_rows = []
        era_rows = []

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
                    f"Problem in the scenario properties. Can't find the "
                    f"'start_date' key of the contract {contract_id} in "
                    f"the 'local_rates' map."
                )

            try:
                rate_script_start = rate_script["start_date"]
            except KeyError:
                raise BadRequest(
                    f"Problem in the scenario properties. Can't find the "
                    f"'start_date' key of the contract {contract_id} in "
                    f"the 'local_rates' map."
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
                    f"For the industry rate {contract_name} the finish_date "
                    f"can't be null."
                )
            for dt in hh_range(report_context, rate_script["start_date"], rfinish):
                cont_cache[dt] = PropDict("scenario properties", rate_script["script"])

        era_maps = scenario_props.get("era_maps", {})
        by_hh = scenario_props.get("by_hh", False)

        scenario_hh = scenario_props.get("hh_data", {})

        era_header_titles = [
            "creation-date",
            "imp-mpan-core",
            "imp-supplier-contract",
            "exp-mpan-core",
            "exp-supplier-contract",
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
            if supply_id is not None:
                conts = conts.filter(Era.supply_id == supply_id)
            for cont in conts:
                title_func = chellow.computer.contract_func(
                    report_context, cont, "virtual_bill_titles"
                )
                if title_func is None:
                    raise Exception(
                        f"For the contract {cont.name} there doesn't seem to "
                        f"be a 'virtual_bill_titles' function."
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

        era_rows.append(
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

        sites = sites.all()
        deltas = {}
        normal_reads = set()
        normal_read_rows = []

        for site in sites:
            deltas[site.id] = _make_site_deltas(
                sess, report_context, site, scenario_hh, forecast_from, supply_id
            )

        for month_start, month_finish in month_pairs:
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
                            deltas[site.id],
                            supply_id,
                            era_maps,
                            now,
                            summary_titles,
                            title_dict,
                            era_rows,
                            site_rows,
                        )
                    except BadRequest as e:
                        raise BadRequest(f"Site Code {site.code}: {e.description}")

            normal_read_rows = [["mpan_core", "date", "msn", "type", "registers"]]
            for mpan_core, r in sorted(list(normal_reads)):
                row = [mpan_core, r.date, r.msn, r.type] + list(r.reads)
                normal_read_rows.append(row)

            write_spreadsheet(rf, compression, site_rows, era_rows, normal_read_rows)
    except BadRequest as e:
        msg = e.description + traceback.format_exc()
        sys.stderr.write(msg + "\n")
        site_rows.append(["Problem " + msg])
        write_spreadsheet(rf, compression, site_rows, era_rows, normal_read_rows)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + "\n")
        site_rows.append(["Problem " + msg])
        write_spreadsheet(rf, compression, site_rows, era_rows, normal_read_rows)
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

        start_year = scenario_props["scenario_start_year"]
        start_month = scenario_props["scenario_start_month"]
        start_date_ct = ct_datetime(now.year, now.month, 1)
        if start_year is None:
            scenario_props["scenario_start_year"] = start_date_ct.year
        if start_month is None:
            scenario_props["scenario_start_month"] = start_date_ct.month
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
        site_id = req_int("site_id") if "site_id" in request.values else None
        if "site_codes" in request.values:
            site_codes = req_str("site_codes").splitlines()

            # Check sites codes are valid
            for site_code in site_codes:
                Site.get_by_code(sess, site_code)

        else:
            site_codes = []

        if "supply_id" in request.values:
            supply_id = req_int("supply_id")
        else:
            supply_id = None

        if "compression" in request.values:
            compression = req_bool("compression")
        else:
            compression = True
        user = g.user

        args = (
            scenario_props,
            base_name,
            site_id,
            supply_id,
            user,
            compression,
            site_codes,
            now,
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
                "ods_monthly_duration.html",
                month_start=month_start,
                month_finish=month_finish,
            ),
            400,
        )


class ScenarioSource:
    def __init__(
        self,
        sess,
        start_date,
        finish_date,
        is_import,
        caches,
        deltas,
        supplier_contract,
        mpan_core,
    ):
        self.sess = sess
        self.supply = None
        self.mpan_core = mpan_core
        self.supply_name = mpan_core
        self.start_date = start_date
        self.is_import = is_import
        self.caches = caches
        self.deltas = deltas
        self.years_back = 0
        self.source_code = "gen"
        self.dno_code = "99"
        self.llfc_code = "510"
        self.voltage_level_code = "LV"
        self.is_substation = False
        self.gsp_group_code = "_L"
        self.supplier_bill = {"net-gbp": 0}
        self.dc_bill = {"net-gbp": 0}
        self.mop_bill = {"net-gbp": 0}
        self.supplier_contract = None
        self.dc_contract = None
        self.mop_contract = None
        self.supplier_rate_sets = defaultdict(set)
        self.is_displaced = False
        self.sc = 0
        self.pc_code = "00"
        self.mop_rate_sets = defaultdict(set)
        self.dc_rate_sets = defaultdict(set)
        self.generator_type_code = "chp"
        self.msn = ""
        self.measurement_type = "hh"
        self.hh_data = list(
            d.copy()
            for d in datum_range(
                sess, self.caches, self.years_back, start_date, finish_date
            )
        )
        if self.deltas is not None:
            site_deltas = self.deltas["site"]

            try:
                sup_deltas = self.deltas[self.mpan_core]
            except KeyError:
                sup_deltas = self.deltas[self.mpan_core] = {}

            for hh in self.hh_data:
                hh_start = hh["start-date"]
                if hh_start in sup_deltas:
                    delt = sup_deltas[hh_start]
                elif hh_start in site_deltas:
                    delt = sup_deltas[hh_start] = site_deltas[hh_start]
                    del site_deltas[hh_start]
                else:
                    continue

                hh["msp-kwh"] += delt
                hh["msp-kw"] += delt * 2
