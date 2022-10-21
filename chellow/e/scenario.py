import csv
import traceback
from collections import defaultdict
from datetime import datetime as Datetime
from io import StringIO

from sqlalchemy import null, or_, true
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest

from chellow.e.computer import (
    SiteSource,
    SupplySource,
    contract_func,
    datum_range,
    displaced_era,
)
from chellow.models import Era, Llfc, MtcParticipant, Pc, SiteEra, Source, Supply
from chellow.utils import (
    c_months_u,
    hh_format,
    hh_max,
    hh_min,
    parse_hh_start,
    to_ct,
    to_utc,
)


def make_create_future_func_simple(contract_name, fnames=None):
    def create_future_func_simple(multiplier, constant):
        mult = float(multiplier)
        const = float(constant)
        if fnames is None:

            def future_func(ns):
                new_ns = {}
                for k, v in ns.items():
                    new_ns[k] = float(v) * mult + const

                return new_ns

        else:

            def future_func(ns):
                new_ns = {}
                for fname in fnames:
                    try:
                        new_ns[fname] = ns[fname] * mult + const
                    except KeyError:
                        raise BadRequest(
                            f"Can't find {fname} in rate script {ns} for contract name "
                            f"{contract_name}."
                        )

                return new_ns

        return future_func

    return create_future_func_simple


def make_create_future_func_monthly(contract_name, fnames):
    def create_future_func_monthly(multiplier, constant):
        def future_func(ns):
            new_ns = {}
            for fname in fnames:
                old_result = ns[fname]
                last_value = old_result[sorted(old_result.keys())[-1]]
                new_ns[fname] = defaultdict(
                    lambda: last_value,
                    [(k, v * multiplier + constant) for k, v in old_result.items()],
                )

            return new_ns

        return future_func

    return create_future_func_monthly


def make_site_deltas(
    sess, report_context, site, scenario_hh, forecast_from, supply_ids
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
                    f"Can't interpret the row {cells} it should be of the form "
                    f"'timestamp, kWh'"
                )

            date_str, kwh_str = cells
            ts = parse_hh_start(date_str)
            earliest_delta = min(ts, earliest_delta)
            latest_delta = max(ts, latest_delta)
            try:
                hh_data[ts] = float(kwh_str)
            except ValueError as e:
                raise BadRequest(
                    f"When looking at {typ} hh data, can't parse the kWh at {date_str} "
                    f": {e}"
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

        site_ds = SiteSource(
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

            if supply_ids is not None and era.supply_id not in supply_ids:
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

            if supply_ids is not None and era.supply_id not in supply_ids:
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


def make_calcs(
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
):
    meter_order = {"hh": 0, "amr": 1, "nhh": 2, "unmetered": 3}
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
            joinedload(Era.mtc_participant).joinedload(MtcParticipant.meter_type),
            joinedload(Era.pc),
            joinedload(Era.site_eras),
        )
        .order_by(Era.supply_id, Era.start_date)
    ):

        supply = era.supply
        if data_source_bill is not None and supply.dno.dno_code in ("88", "99"):
            continue

        if supply.generator_type is not None:
            site_gen_types.add(supply.generator_type.code)

        if supply_ids is not None and supply.id not in supply_ids:
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
                bill=data_source_bill if era.pc.code == "00" else None,
            )
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
                try:
                    import_vb_function(imp_ss)
                except (AttributeError, TypeError) as e:
                    raise BadRequest(
                        f"Problem with virtual bill of supplier contract "
                        f"{imp_supplier_contract.id} {e} {traceback.format_exc()}"
                    )
                except BadRequest as e:
                    raise BadRequest(
                        f"{e.description} Problem with virtual bill of supplier "
                        f"contract {imp_supplier_contract.id} {e}"
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
                bill=data_source_bill if era.pc.code == "00" else None,
            )
            measurement_type = exp_ss.measurement_type
            exp_supplier_contract = exp_ss.supplier_contract
            if exp_supplier_contract is not None:
                export_vb_function = contract_func(
                    report_context, exp_supplier_contract, "virtual_bill"
                )
                try:
                    export_vb_function(exp_ss)
                except (AttributeError, TypeError) as e:
                    raise BadRequest(
                        f"Problem with virtual bill of supplier contract "
                        f"{exp_supplier_contract.id} {e} {traceback.format_exc()}"
                    )
                except BadRequest as e:
                    raise BadRequest(
                        f"{e.description} Problem with virtual bill of supplier "
                        f"contract {exp_supplier_contract.id}"
                    )

        order = (
            f"{meter_order[measurement_type]}_{supply.id}_{hh_format(era.start_date)}"
        )
        calcs.append((order, era.imp_mpan_core, era.exp_mpan_core, imp_ss, exp_ss))

    start_date_ct, finish_date_ct = to_ct(start_date), to_ct(finish_date)
    for month_start, month_finish in c_months_u(
        start_year=start_date_ct.year,
        start_month=start_date_ct.month,
        finish_year=finish_date_ct.year,
        finish_month=finish_date_ct.month,
    ):
        ss_start = hh_max(month_start, start_date)
        ss_finish = hh_min(month_finish, finish_date)
        # Check if gen deltas haven't been consumed
        extra_sss = set()
        for is_imp in (True, False):
            sup_deltas = site_deltas["supply_deltas"][is_imp]["gen"]["site"]
            if len(list(t for t in sup_deltas if ss_start <= t <= ss_finish)) > 0:
                extra_sss.add(is_imp)

        disp_era = displaced_era(
            sess,
            report_context,
            site,
            ss_start,
            ss_finish,
            forecast_from,
            has_scenario_generation=len(extra_sss) > 0,
        )

        if disp_era is not None and supply_ids is None:
            site_ds = SiteSource(
                sess,
                site,
                ss_start,
                ss_finish,
                forecast_from,
                report_context,
                disp_era,
                era_maps=era_maps,
                deltas=site_deltas,
                bill=data_source_bill,
            )

            disp_supplier_contract = disp_era.imp_supplier_contract
            disp_vb_function = contract_func(
                report_context, disp_supplier_contract, "displaced_virtual_bill"
            )
            if disp_vb_function is None:
                raise BadRequest(
                    f"The supplier contract {disp_supplier_contract.name} "
                    f" doesn't have the displaced_virtual_bill() function."
                )
            disp_vb_function(site_ds)

            calcs.append(("1", "displaced", None, site_ds, None))

        if len(extra_sss) > 0:
            if True in extra_sss:
                sup_deltas = site_deltas["supply_deltas"][True]["gen"]
                imp_ss_name = site.code + "_extra_gen_TRUE"
                imp_ss = ScenarioSource(
                    sess,
                    ss_start,
                    ss_finish,
                    True,
                    report_context,
                    sup_deltas,
                    disp_era.imp_supplier_contract,
                    imp_ss_name,
                    bill=data_source_bill,
                )
            else:
                imp_ss_name = imp_ss = None
            if False in extra_sss:
                exp_ss_name = site.code + "_extra_gen_FALSE"
                sup_deltas = site_deltas["supply_deltas"][False]["gen"]
                exp_ss = ScenarioSource(
                    sess,
                    ss_start,
                    ss_finish,
                    False,
                    report_context,
                    sup_deltas,
                    disp_era.imp_supplier_contract,
                    imp_ss_name,
                    bill=data_source_bill,
                )
            else:
                exp_ss_name = exp_ss = None

            calcs.append(("0", imp_ss_name, exp_ss_name, imp_ss, exp_ss))

        # Check if exp net deltas haven't been consumed
        sup_deltas = site_deltas["supply_deltas"][False]["net"]
        if len(list(t for t in sup_deltas["site"] if ss_start <= t <= ss_finish)) > 0:
            ss_name = site.code + "_extra_net_export"
            ss = SupplySource(
                sess,
                ss_start,
                ss_finish,
                forecast_from,
                disp_era,
                False,
                report_context,
                era_maps=era_maps,
                deltas=sup_deltas,
                bill=data_source_bill,
            )

            calcs.append(("0", None, ss_name, None, ss))
    return calcs, site_gen_types


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
        bill=None,
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
        self.bill = bill
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
