import csv
import sys
import threading
import traceback
from datetime import datetime as Datetime

from flask import g, redirect

from sqlalchemy import or_, text
from sqlalchemy.sql.expression import null

from chellow.dloads import open_file
from chellow.e.computer import SiteSource, contract_func, displaced_era, forecast_date
from chellow.models import Contract, Era, Session, Site, SiteEra, Source, Supply
from chellow.utils import c_months_u, hh_format, hh_range, req_int


def to_val(v):
    if isinstance(v, Datetime):
        return hh_format(v)
    elif isinstance(v, set):
        if len(v) == 1:
            return to_val(v.pop())
        else:
            return ""
    else:
        return str(v)


def content(contract_id, end_year, end_month, months, user):
    caches = {}
    f = None
    try:
        with Session() as sess:
            f = open_file("displaced.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            titles = [
                "Site Code",
                "Site Name",
                "Associated Site Ids",
                "From",
                "To",
                "Gen Types",
                "CHP kWh",
                "LM kWh",
                "Turbine kWh",
                "PV kWh",
            ]

            month_list = list(
                c_months_u(finish_year=end_year, finish_month=end_month, months=months)
            )
            start_date, finish_date = month_list[0][0], month_list[-1][-1]

            f_date = forecast_date()

            contract = Contract.get_supplier_by_id(sess, contract_id)
            sites = (
                sess.query(Site)
                .join(SiteEra)
                .join(Era)
                .join(Supply)
                .join(Source)
                .filter(
                    or_(Era.finish_date == null(), Era.finish_date >= start_date),
                    Era.start_date <= finish_date,
                    or_(
                        Source.code.in_(("gen", "gen-grid")),
                        Era.exp_mpan_core != null(),
                    ),
                )
                .distinct()
            )
            bill_titles = contract_func(
                caches, contract, "displaced_virtual_bill_titles"
            )()

            for title in bill_titles:
                if title == "total-msp-kwh":
                    title = "total-displaced-msp-kwh"
                titles.append(title)
            writer.writerow(titles)

            for site in sites:
                for month_start, month_finish in month_list:
                    disp_era = displaced_era(
                        sess, caches, site, month_start, month_finish, f_date
                    )
                    if disp_era is None:
                        continue
                    supplier_contract = disp_era.imp_supplier_contract
                    if contract is not None and contract != supplier_contract:
                        continue

                    linked_sites = set()
                    generator_types = set()
                    for era in (
                        sess.query(Era)
                        .join(SiteEra)
                        .filter(
                            SiteEra.site == site,
                            Era.start_date <= month_finish,
                            or_(
                                Era.finish_date == null(),
                                Era.finish_date >= month_start,
                            ),
                        )
                    ):
                        for site_era in era.site_eras:
                            if site_era.site != site:
                                linked_sites.add(site_era.site.code)
                        supply = era.supply
                        if supply.generator_type is not None:
                            generator_types.add(supply.generator_type.code)

                    supply_ids = set()
                    for era in (
                        sess.query(Era)
                        .join(SiteEra)
                        .filter(
                            SiteEra.site == site,
                            SiteEra.is_physical,
                            Era.start_date <= month_finish,
                            or_(
                                Era.finish_date == null(),
                                Era.finish_date >= month_start,
                            ),
                        )
                    ):
                        supply_ids.add(era.supply.id)

                    vals = [
                        site.code,
                        site.name,
                        ", ".join(list(linked_sites)),
                        hh_format(month_start),
                        hh_format(month_finish),
                        ", ".join(list(generator_types)),
                    ]

                    total_gen_breakdown = {}

                    results = iter(
                        sess.execute(
                            text(
                                "select supply.id, hh_datum.value, "
                                "hh_datum.start_date, channel.imp_related, "
                                "source.code, generator_type.code as "
                                "gen_type_code from hh_datum, channel, source, "
                                "era, supply left outer join generator_type on "
                                "supply.generator_type_id = generator_type.id "
                                "where hh_datum.channel_id = channel.id and "
                                "channel.era_id = era.id and era.supply_id = "
                                "supply.id and supply.source_id = source.id and "
                                "channel.channel_type = 'ACTIVE' and not "
                                "(source.code = 'grid' and channel.imp_related "
                                "is true) and hh_datum.start_date >= "
                                ":month_start and hh_datum.start_date "
                                "<= :month_finish and "
                                "supply.id = any(:supply_ids) order "
                                "by hh_datum.start_date, supply.id"
                            ),
                            params={
                                "month_start": month_start,
                                "month_finish": month_finish,
                                "supply_ids": sorted(list(supply_ids)),
                            },
                        )
                    )

                    (
                        sup_id,
                        hh_val,
                        hh_start,
                        imp_related,
                        source_code,
                        gen_type_code,
                    ) = next(results, (None, None, None, None, None, None))

                    for hh_date in hh_range(caches, month_start, month_finish):
                        gen_breakdown = {}
                        exported = 0
                        while hh_start == hh_date:
                            if not imp_related and source_code in ("grid", "gen-grid"):
                                exported += hh_val
                            if (imp_related and source_code == "gen") or (
                                not imp_related and source_code == "gen-grid"
                            ):
                                gen_breakdown[gen_type_code] = (
                                    gen_breakdown.setdefault(gen_type_code, 0) + hh_val
                                )

                            if (not imp_related and source_code == "gen") or (
                                imp_related and source_code == "gen-grid"
                            ):
                                gen_breakdown[gen_type_code] = (
                                    gen_breakdown.setdefault(gen_type_code, 0) - hh_val
                                )

                            (
                                sup_id,
                                hh_val,
                                hh_start,
                                imp_related,
                                source_code,
                                gen_type_code,
                            ) = next(results, (None, None, None, None, None, None))

                        displaced = sum(gen_breakdown.values()) - exported
                        added_so_far = 0
                        for key in sorted(gen_breakdown.keys()):
                            kwh = gen_breakdown[key]
                            if displaced < 0:
                                total_gen_breakdown[key] = (
                                    total_gen_breakdown.get(key, 0) + kwh
                                )
                            else:
                                if kwh + added_so_far > displaced:
                                    total_gen_breakdown[key] = (
                                        total_gen_breakdown.get(key, 0)
                                        + displaced
                                        - added_so_far
                                    )
                                    break
                                else:
                                    total_gen_breakdown[key] = (
                                        total_gen_breakdown.get(key, 0) + kwh
                                    )
                                    added_so_far += kwh

                    for title in ["chp", "lm", "turb", "pv"]:
                        vals.append(str(total_gen_breakdown.get(title, "")))

                    site_ds = SiteSource(
                        sess,
                        site,
                        month_start,
                        month_finish,
                        f_date,
                        caches,
                        disp_era,
                    )
                    disp_func = contract_func(
                        caches, supplier_contract, "displaced_virtual_bill"
                    )
                    disp_func(site_ds)
                    bill = site_ds.supplier_bill
                    for title in bill_titles:
                        if title in bill:
                            vals.append(to_val(bill[title]))
                            del bill[title]
                        else:
                            vals.append("")

                    for k in sorted(bill.keys()):
                        vals.append(k)
                        vals.append(str(bill[k]))
                    writer.writerow(vals)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        if f is not None:
            f.write(msg)
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    end_year = req_int("finish_year")
    end_month = req_int("finish_month")
    months = req_int("months")
    contract_id = req_int("supplier_contract_id")
    args = contract_id, end_year, end_month, months, g.user
    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
