import csv
from collections import defaultdict
from datetime import datetime as Datetime
from io import StringIO

from sqlalchemy import null, or_, true

from werkzeug.exceptions import BadRequest

from chellow.e.computer import SiteSource, SupplySource
from chellow.models import Era, Pc, SiteEra, Source, Supply
from chellow.utils import (
    c_months_u,
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


def make_site_deltas(sess, report_context, site, scenario_hh, forecast_from, supply_id):
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
