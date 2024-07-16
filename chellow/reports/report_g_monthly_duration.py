import sys
import threading
import traceback

from flask import g, request

import odio

from sqlalchemy import or_, select, true
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

import chellow.e.computer
from chellow.dloads import open_file
from chellow.e.computer import contract_func
from chellow.gas.engine import GDataSource
from chellow.models import (
    GBill,
    GContract,
    GEra,
    GSupply,
    Session,
    Site,
    SiteGEra,
)
from chellow.utils import (
    c_months_u,
    ct_datetime_now,
    hh_format,
    hh_max,
    hh_min,
    make_val,
    req_bool,
    req_int,
)
from chellow.views import chellow_redirect


CATEGORY_ORDER = {None: 0, "unmetered": 1, "nhh": 2, "amr": 3, "hh": 4}
meter_order = {"hh": 0, "amr": 1, "nhh": 2, "unmetered": 3}


def write_spreadsheet(fl, compressed, site_rows, era_rows):
    fl.seek(0)
    fl.truncate()
    with odio.create_spreadsheet(fl, "1.2", compressed=compressed) as f:
        f.append_table("Site Level", site_rows)
        f.append_table("Era Level", era_rows)


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

    try:
        gbp = bill["net_gbp"]
    except KeyError:
        gbp = 0
        bill["problem"] += (
            f"For the supply {ss.mprn} the virtual bill {bill} "
            f"from the contract {contract.name} does not contain "
            f"the net_gbp key."
        )
    try:
        kwh = bill["kwh"]
    except KeyError:
        kwh = 0
        bill["problem"] += (
            f"For the supply {ss.mprn} the virtual bill "
            f"{bill} from the contract {contract.name} does not "
            f"contain the 'kwh' key."
        )

    billed_kwh = billed_net_gbp = billed_vat_gbp = billed_gross_gbp = 0

    g_era_associates = {s.site.code for s in g_era.site_g_eras if not s.is_physical}

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
        billed_kwh += overlap_proportion * float(g_bill.kwh)
        billed_net_gbp += overlap_proportion * float(g_bill.net)
        billed_vat_gbp += overlap_proportion * float(g_bill.vat)
        billed_gross_gbp += overlap_proportion * float(g_bill.gross)

    associated_site_ids = ",".join(sorted(g_era_associates))
    g_era_rows.append(
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
                associated_site_ids,
                g_era.start_date,
                month_finish,
                kwh,
                gbp,
                billed_kwh,
                billed_net_gbp,
                billed_vat_gbp,
                billed_gross_gbp,
            ]
        ]
        + [make_val(bill.get(t)) for t in vb_titles]
    )
    return kwh, gbp, billed_kwh, billed_net_gbp, billed_vat_gbp, billed_gross_gbp


def content(
    site_id, g_supply_id, user, compression, finish_year, finish_month, months, now=None
):
    if now is None:
        now = ct_datetime_now()
    report_context = {}
    month_list = list(
        c_months_u(finish_year=finish_year, finish_month=finish_month, months=months)
    )
    start_date, finish_date = month_list[0][0], month_list[-1][-1]

    try:
        with Session() as sess:
            base_name = [
                "g_monthly_duration",
                hh_format(start_date)
                .replace(" ", "_")
                .replace(":", "")
                .replace("-", ""),
                "for",
                str(months),
                "months",
            ]

            forecast_from = chellow.e.computer.forecast_date()

            sites = (
                sess.query(Site)
                .join(SiteGEra)
                .join(GEra)
                .filter(SiteGEra.is_physical == true())
                .distinct()
                .order_by(Site.code)
            )
            if site_id is not None:
                site = Site.get_by_id(sess, site_id)
                sites = sites.filter(Site.id == site.id)
                base_name.append("site")
                base_name.append(site.code)
            if g_supply_id is not None:
                g_supply = GSupply.get_by_id(sess, g_supply_id)
                base_name.append("g_supply")
                base_name.append(str(g_supply.id))
                sites = sites.filter(GEra.g_supply == g_supply)

            rf = open_file("_".join(base_name) + ".ods", user, mode="wb")
            site_rows = []
            g_era_rows = []

            era_header_titles = [
                "creation_date",
                "mprn",
                "supply_name",
                "exit_zone",
                "msn",
                "unit",
                "contract",
                "site_id",
                "site_name",
                "associated_site_ids",
                "era-start",
                "month",
            ]
            site_header_titles = [
                "creation_date",
                "site_id",
                "site_name",
                "associated_site_ids",
                "month",
            ]
            summary_titles = [
                "kwh",
                "gbp",
                "billed_kwh",
                "billed_net_gbp",
                "billed_vat_gbp",
                "billed_gross_gbp",
            ]

            vb_titles = []
            conts = (
                sess.query(GContract)
                .join(GEra)
                .join(GSupply)
                .filter(
                    GEra.start_date <= finish_date,
                    or_(GEra.finish_date == null(), GEra.finish_date >= start_date),
                )
                .distinct()
                .order_by(GContract.id)
            )
            if g_supply_id is not None:
                conts = conts.filter(GEra.g_supply_id == g_supply_id)
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

            g_era_rows.append(era_header_titles + summary_titles + vb_titles)
            site_rows.append(site_header_titles + summary_titles)

            for month_start, month_finish in month_list:
                for site in sites.filter(
                    GEra.start_date <= month_finish,
                    or_(GEra.finish_date == null(), GEra.finish_date >= month_start),
                ):
                    site_kwh = site_gbp = site_billed_kwh = site_billed_net_gbp = 0
                    site_billed_vat_gbp = site_billed_gross_gbp = 0

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
                    if g_supply_id is not None:
                        g_eras_q = g_eras_q.where(GEra.g_supply_id == g_supply_id)

                    for g_era in sess.scalars(g_eras_q):
                        try:
                            (
                                kwh,
                                gbp,
                                billed_kwh,
                                billed_net_gbp,
                                billed_vat_gbp,
                                billed_gross_gbp,
                            ) = _process_era(
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
                            )
                            site_kwh += kwh
                            site_gbp += gbp
                            site_billed_kwh += billed_kwh
                            site_billed_net_gbp += billed_net_gbp
                            site_billed_vat_gbp += billed_vat_gbp
                            site_billed_gross_gbp += billed_gross_gbp
                        except BadRequest as e:
                            raise BadRequest(
                                f"Problem with g_era {g_era.id}: {e.description}"
                            )

                    linked_sites = ", ".join(
                        s.code
                        for s in site.find_linked_sites(sess, month_start, month_finish)
                    )

                    site_rows.append(
                        [
                            make_val(v)
                            for v in [
                                now,
                                site.code,
                                site.name,
                                linked_sites,
                                month_finish,
                                site_kwh,
                                site_gbp,
                                site_billed_kwh,
                                site_billed_net_gbp,
                                site_billed_vat_gbp,
                                site_billed_gross_gbp,
                            ]
                        ]
                    )
                    sess.rollback()
                write_spreadsheet(rf, compression, site_rows, g_era_rows)

    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg + "\n")
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
    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    months = req_int("months")

    site_id = req_int("site_id") if "site_id" in request.values else None

    if "g_supply_id" in request.values:
        g_supply_id = req_int("g_supply_id")
    else:
        g_supply_id = None

    if "compression" in request.values:
        compression = req_bool("compression")
    else:
        compression = True

    user = g.user
    args = (site_id, g_supply_id, user, compression, finish_year, finish_month, months)

    threading.Thread(target=content, args=args).start()
    return chellow_redirect("/downloads", 303)
