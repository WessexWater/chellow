import threading
import traceback

from flask import g, redirect, request

from odio import create_spreadsheet

from sqlalchemy import or_, select, true
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

import chellow.e.computer
from chellow.dloads import open_file
from chellow.e.computer import contract_func, forecast_date
from chellow.gas.engine import GDataSource, g_rates
from chellow.models import (
    GBill,
    GContract,
    GEra,
    GSupply,
    RSession,
    ReportRun,
    Scenario,
    Site,
    SiteGEra,
    User,
)
from chellow.utils import (
    PropDict,
    c_months_c,
    c_months_u,
    hh_format,
    hh_max,
    hh_min,
    hh_range,
    make_val,
    req_bool,
    req_int,
    req_str,
    to_utc,
    utc_datetime_now,
)


def write_spreadsheet(fl, compressed, site_rows, era_rows):
    fl.seek(0)
    fl.truncate()
    with create_spreadsheet(fl, compressed=compressed) as sheet:
        sheet.append_table("Site Level", site_rows)
        sheet.append_table("Era Level", era_rows)


def _process_era(
    report_context,
    sess,
    site,
    g_era,
    month_start,
    month_finish,
    forecast_from,
    g_era_rows,
    vb_titles,
    now,
    summary_titles,
):
    g_supply = g_era.g_supply

    ss_start = hh_max(g_era.start_date, month_start)
    ss_finish = hh_min(g_era.finish_date, month_finish)

    ss = GDataSource(
        sess,
        ss_start,
        ss_finish,
        forecast_from,
        g_era,
        report_context,
        None,
    )

    contract = g_era.g_contract
    vb_function = contract_func(report_context, contract, "virtual_bill")
    if vb_function is None:
        raise BadRequest(
            f"The contract {contract.name} doesn't have the virtual_bill() function."
        )
    try:
        vb_function(ss)
        bill = ss.bill
    except TypeError as e:
        raise BadRequest(
            f"Problem with virtual bill for g_supplier_contrat {contract.id}."
        ) from e

    summary_data = {
        "kwh": 0,
        "net_gbp": 0,
        "vat_gbp": 0,
        "gross_gbp": 0,
        "billed_kwh": 0,
        "billed_net_gbp": 0,
        "billed_vat_gbp": 0,
        "billed_gross_gbp": 0,
    }

    for key in ("kwh", "net_gbp", "vat_gbp", "gross_gbp"):
        try:
            summary_data[key] += bill[key]
        except KeyError:
            bill["problem"] += (
                f"For the supply {ss.mprn} the virtual bill {bill} "
                f"from the contract {contract.name} does not contain "
                f"the {key} key."
            )

    associated_site_codes = {
        s.site.code for s in g_era.site_g_eras if not s.is_physical
    }

    for g_bill in sess.query(GBill).filter(
        GBill.g_supply == g_supply,
        GBill.start_date <= ss_finish,
        GBill.finish_date >= ss_start,
    ):
        bill_start = g_bill.start_date
        bill_finish = g_bill.finish_date
        bill_duration = (bill_finish - bill_start).total_seconds() + (30 * 60)
        overlap_duration = (
            min(bill_finish, ss_finish) - max(bill_start, ss_start)
        ).total_seconds() + (30 * 60)
        overlap_proportion = overlap_duration / bill_duration
        summary_data["billed_kwh"] += overlap_proportion * float(g_bill.kwh)
        summary_data["billed_net_gbp"] += overlap_proportion * float(g_bill.net)
        summary_data["billed_vat_gbp"] += overlap_proportion * float(g_bill.vat)
        summary_data["billed_gross_gbp"] += overlap_proportion * float(g_bill.gross)

    g_era_row = (
        [
            make_val(v)
            for v in [
                now,
                g_supply.mprn,
                g_supply.name,
                g_supply.g_exit_zone.code,
                g_era.msn,
                g_era.g_unit.code,
                contract.name,
                site.code,
                site.name,
                associated_site_codes,
                g_era.start_date,
                month_finish,
            ]
        ]
        + [make_val(summary_data[t]) for t in summary_titles]
        + [make_val(bill.get(t)) for t in vb_titles]
    )
    g_era_rows.append(g_era_row)
    return summary_data


def content(scenario_props, user_id, compression, now, base_name):
    report_context = {}
    try:
        eng = report_context["g_engine"]
    except KeyError:
        eng = report_context["g_engine"] = {}

    try:
        rss_cache = eng["rates"]
    except KeyError:
        rss_cache = eng["rates"] = {}

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
            start_date = month_pairs[0][0]
            finish_date = month_pairs[-1][-1]

            base_name.append(
                hh_format(start_date)
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

            sites = select(Site).join(SiteGEra).distinct().order_by(Site.code)

            mprns = scenario_props.get("mprns")
            g_supply_ids = None
            if mprns is not None:
                g_supply_ids = []
                for mprn in mprns:
                    g_supply = GSupply.get_by_mprn(sess, mprn)
                    g_supply_ids.append(g_supply.id)

                if len(g_supply_ids) == 1:
                    base_name.append("g_supply")
                    base_name.append(str(g_supply.id))
                else:
                    base_name.append("mprns")

                sites = (
                    sites.join(GEra).join(GSupply).where(GSupply.id.in_(g_supply_ids))
                )

            site_codes = scenario_props.get("site_codes")
            if site_codes is not None:
                if len(site_codes) == 1:
                    base_name.append("site")
                    base_name.append(site_codes[0])
                else:
                    base_name.append("sitecodes")
                sites = sites.where(Site.code.in_(site_codes))

            for is_industry, rates_prop in (
                (True, "industry_rates"),
                (False, "supplier_rates"),
            ):

                for rate_script in scenario_props.get(rates_prop, []):
                    g_contract_id = rate_script["g_contract_id"]
                    try:
                        i_cache = rss_cache[is_industry]
                    except KeyError:
                        i_cache = rss_cache[is_industry] = {}

                    try:
                        cont_cache = i_cache[g_contract_id]
                    except KeyError:
                        cont_cache = i_cache[g_contract_id] = {}

                    try:
                        rate_script_start = rate_script["start_date"]
                    except KeyError:
                        raise BadRequest(
                            f"Problem in the scenario properties. Can't find the "
                            f"'start_date' key of the contract {g_contract_id} in the "
                            f"'{rates_prop}' map."
                        )

                    try:
                        rate_script_finish = rate_script["finish_date"]
                    except KeyError:
                        raise BadRequest(
                            f"Problem in the scenario properties. Can't find the "
                            f"'finish_date' key of the contract {g_contract_id} in the "
                            f"'{rates_prop}' map."
                        )

                    for dt in hh_range(
                        report_context, rate_script_start, rate_script_finish
                    ):
                        g_rates(sess, report_context, g_contract_id, dt, is_industry)

                    for dt in hh_range(
                        report_context, rate_script_start, rate_script_finish
                    ):
                        storage = cont_cache[dt]._storage.copy()
                        storage.update(rate_script["script"])
                        cont_cache[dt] = PropDict("scenario properties", storage)

            user = User.get_by_id(sess, user_id)
            fname = "_".join(base_name) + ".ods"
            rf = open_file(fname, user, mode="wb")
            org_rows = []
            site_rows = []
            g_era_rows = []

            org_header_titles = [
                "creation_date",
                "month",
            ]
            summary_titles = [
                "kwh",
                "net_gbp",
                "vat_gbp",
                "gross_gbp",
                "billed_kwh",
                "billed_net_gbp",
                "billed_vat_gbp",
                "billed_gross_gbp",
            ]
            org_titles = org_header_titles + summary_titles
            site_header_titles = [
                "creation_date",
                "site_code",
                "site_name",
                "associated_site_codes",
                "month",
            ]
            site_titles = site_header_titles + summary_titles
            era_header_titles = [
                "creation_date",
                "mprn",
                "supply_name",
                "exit_zone",
                "msn",
                "unit",
                "contract",
                "site_code",
                "site_name",
                "associated_site_codes",
                "era-start",
                "month",
            ]

            vb_titles = []
            conts = (
                sess.query(GContract)
                .join(GEra)
                .join(GSupply)
                .where(
                    GEra.start_date <= finish_date,
                    or_(GEra.finish_date == null(), GEra.finish_date >= start_date),
                )
                .distinct()
                .order_by(GContract.id)
            )
            if g_supply_ids is not None:
                conts = conts.where(GEra.g_supply_id.in_(g_supply_ids))
            for cont in conts:
                title_func = chellow.e.computer.contract_func(
                    report_context, cont, "virtual_bill_titles"
                )
                if title_func is None:
                    raise Exception(
                        f"For the contract {cont.name} there doesn't seem to be "
                        f"a 'virtual_bill_titles' function."
                    )
                for title in title_func():
                    if title not in vb_titles:
                        vb_titles.append(title)

            org_rows.append(org_header_titles + summary_titles)
            site_rows.append(site_header_titles + summary_titles)
            g_era_rows.append(era_header_titles + summary_titles + vb_titles)

            for month_start, month_finish in month_pairs:
                org_row = {
                    "creation_date": now,
                    "month": month_start,
                    "kwh": 0,
                    "net_gbp": 0,
                    "vat_gbp": 0,
                    "gross_gbp": 0,
                    "billed_kwh": 0,
                    "billed_net_gbp": 0,
                    "billed_vat_gbp": 0,
                    "billed_gross_gbp": 0,
                }
                for site in sess.scalars(
                    sites.where(
                        GEra.start_date <= month_finish,
                        or_(
                            GEra.finish_date == null(), GEra.finish_date >= month_start
                        ),
                    )
                ):
                    linked_sites = {
                        s.code
                        for s in site.find_linked_sites(sess, month_start, month_finish)
                    }

                    site_row = {
                        "creation_date": now,
                        "site_code": site.code,
                        "site_name": site.name,
                        "associated_site_codes": linked_sites,
                        "month": month_finish,
                        "kwh": 0,
                        "net_gbp": 0,
                        "vat_gbp": 0,
                        "gross_gbp": 0,
                        "billed_kwh": 0,
                        "billed_net_gbp": 0,
                        "billed_vat_gbp": 0,
                        "billed_gross_gbp": 0,
                    }

                    g_eras_q = (
                        select(GEra)
                        .join(SiteGEra)
                        .filter(
                            SiteGEra.site == site,
                            SiteGEra.is_physical == true(),
                            GEra.start_date <= month_finish,
                            or_(
                                GEra.finish_date == null(),
                                GEra.finish_date >= month_start,
                            ),
                        )
                        .options(
                            joinedload(GEra.g_contract),
                            joinedload(GEra.g_supply),
                            joinedload(GEra.g_supply).joinedload(GSupply.g_exit_zone),
                        )
                        .order_by(GEra.id)
                    )
                    if g_supply_ids is not None:
                        g_eras_q = g_eras_q.where(GEra.g_supply_id.in_(g_supply_ids))

                    for g_era in sess.scalars(g_eras_q):
                        try:
                            summary_data = _process_era(
                                report_context,
                                sess,
                                site,
                                g_era,
                                month_start,
                                month_finish,
                                forecast_from,
                                g_era_rows,
                                vb_titles,
                                now,
                                summary_titles,
                            )
                        except BadRequest as e:
                            raise BadRequest(
                                f"Problem with g_era {g_era.id}: {e.description}"
                            )
                        for k, v in summary_data.items():
                            org_row[k] += v
                            site_row[k] += v

                    site_rows.append([make_val(site_row[t]) for t in site_titles])
                    sess.rollback()
                org_rows.append([make_val(org_row[t]) for t in org_titles])
                write_spreadsheet(rf, compression, site_rows, g_era_rows)

        if scenario_props.get("save_report_run", False):
            report_run_id = ReportRun.w_insert(
                "g_monthly_duration", user_id, fname, {"scenario": scenario_props}
            )
            for tab, rows in (
                ("org", org_rows),
                ("site", site_rows),
                ("era", g_era_rows),
            ):
                titles = rows[0]
                for row in rows[1:]:
                    values = dict(zip(titles, row))
                    ReportRun.w_insert_row(report_run_id, tab, titles, values, {})
            ReportRun.w_update(report_run_id, "finished")

    except BaseException:
        msg = traceback.format_exc()
        print(msg)
        site_rows.append(["Problem " + msg])
        write_spreadsheet(rf, compression, site_rows, g_era_rows)
    finally:
        try:
            rf.close()
        except BaseException:
            msg = traceback.format_exc()
            ef = open_file("error.txt", user, mode="w")
            ef.write(msg + "\n")
            ef.close()


def do_get(sess):
    now = utc_datetime_now()
    base_name = []
    if "scenario_id" in request.values:
        scenario_id = req_int("scenario_id")
        scenario = Scenario.get_by_id(sess, scenario_id)
        scenario_props = scenario.props
        base_name.append(scenario.name)
    else:
        scenario_props = {}
        base_name.append("g_monthly_duration")

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

    if "g_supply_id" in request.values:
        g_supply_id = req_int("g_supply_id")
        g_supply = GSupply.get_by_id(sess, g_supply_id)
        scenario_props["mprns"] = [g_supply.mprn]

    if "compression" in request.values:
        compression = req_bool("compression")
    else:
        compression = True

    args = scenario_props, g.user.id, compression, now, base_name

    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
