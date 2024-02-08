import csv
import sys
import threading
import traceback
from io import StringIO

from flask import g, request

from sqlalchemy import or_, select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null, true

from chellow.dloads import open_file
from chellow.models import Era, RSession, Site, SiteEra, Supply, User
from chellow.utils import (
    csv_make_val,
    ct_datetime,
    hh_format,
    req_date,
    req_int,
    req_str,
    to_ct,
    to_utc,
)
from chellow.views import chellow_redirect


def _write_row(writer, titles, vals, total):
    vals["total"] = total
    writer.writerow(csv_make_val(vals[t]) for t in titles)


def _process_site(sess, zf, site, start_date, finish_date, typ):
    buf = StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    headers = [
        "site_code",
        "site_name",
        "associated_site_codes",
        "sources",
        "generator_types",
        "from",
        "to",
        "type",
        "date",
        "total",
    ]
    slot_titles = list(map(str, range(1, 51)))
    titles = headers + slot_titles
    writer.writerow(titles)
    associates = " ".join(
        s.code for s in site.find_linked_sites(sess, start_date, finish_date)
    )
    source_codes = set()
    gen_types = set()
    for supply in (
        sess.query(Supply)
        .join(Era)
        .join(SiteEra)
        .filter(
            SiteEra.is_physical == true(),
            SiteEra.site == site,
            Era.start_date <= finish_date,
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
        )
        .distinct()
        .options(joinedload(Supply.source), joinedload(Supply.generator_type))
    ):
        source_codes.add(supply.source.code)
        gen_type = supply.generator_type
        if gen_type is not None:
            gen_types.add(gen_type.code)

    vals = total = slot_count = None
    for hh in site.hh_data(sess, start_date, finish_date):
        ct_start_date = to_ct(hh["start_date"])
        if ct_start_date.hour == 0 and ct_start_date.minute == 0:
            if vals is not None:
                _write_row(writer, titles, vals, total)
            vals = {
                "site_code": site.code,
                "site_name": site.name,
                "associated_site_codes": associates,
                "sources": source_codes,
                "generator_types": gen_types,
                "from": start_date,
                "to": finish_date,
                "type": typ,
                "date": ct_start_date.strftime("%Y-%m-%d"),
            }
            for s in slot_titles:
                vals[s] = None
            total = 0
            slot_count = 0

        slot_count += 1
        val = hh[typ]
        total += val
        vals[str(slot_count)] = val
    if vals is not None:
        _write_row(writer, titles, vals, total)

    zf.writestr(
        f"{site.code}_{to_ct(finish_date).strftime('%Y%m%d%H%M')}.csv", buf.getvalue()
    )


def none_content(site_codes, typ, start_date, finish_date, user_id, file_name):
    zf = None
    try:
        with RSession() as rsess:
            user = User.get_by_id(rsess, user_id)
            sites_q = (
                select(Site)
                .join(SiteEra)
                .join(Era)
                .where(
                    SiteEra.is_physical == true(),
                    or_(Era.finish_date == null(), Era.finish_date >= start_date),
                    Era.start_date <= finish_date,
                )
                .distinct()
            )
            if site_codes is not None:
                sites_q = sites_q.where(Site.code.in_(site_codes))

            zf = open_file(file_name, user, mode="w", is_zip=True)

            for site in rsess.execute(sites_q).scalars():
                _process_site(rsess, zf, site, start_date, finish_date, typ)

                # Avoid long-running transaction
                rsess.rollback()
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        zf.write(msg)
    finally:
        if zf is not None:
            zf.close()


def site_content(site_id, start_date, finish_date, user_id, file_name):
    f = None
    try:
        with RSession() as rsess:
            user = User.get_by_id(rsess, user_id)
            f = open_file(file_name, user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            site = Site.get_by_id(rsess, site_id)
            sites = rsess.query(Site).filter(Site.id == site_id)
            start_date_str = hh_format(start_date)
            finish_date_str = hh_format(finish_date)

            for site in sites:
                writer.writerow(
                    [
                        "Site Code",
                        "Site Name",
                        "Associated Site Codes",
                        "Sources",
                        "Generator Types",
                        "From",
                        "To",
                        "Type",
                        "Date",
                    ]
                    + list(map(str, range(1, 51)))
                )
                associates = " ".join(
                    s.code
                    for s in site.find_linked_sites(rsess, start_date, finish_date)
                )
                source_codes = set()
                gen_types = set()
                for supply in (
                    rsess.query(Supply)
                    .join(Era)
                    .join(SiteEra)
                    .filter(
                        SiteEra.is_physical == true(),
                        SiteEra.site == site,
                        Era.start_date <= finish_date,
                        or_(Era.finish_date == null(), Era.finish_date >= start_date),
                    )
                    .distinct()
                    .options(
                        joinedload(Supply.source), joinedload(Supply.generator_type)
                    )
                ):
                    source_codes.add(supply.source.code)
                    gen_type = supply.generator_type
                    if gen_type is not None:
                        gen_types.add(gen_type.code)
                source_codes_str = ", ".join(sorted(source_codes))
                gen_types_str = ", ".join(sorted(gen_types))
                vals = None
                for hh in site.hh_data(rsess, start_date, finish_date):
                    hh_start_ct = to_ct(hh["start_date"])
                    if hh_start_ct.hour == 0 and hh_start_ct.minute == 0:
                        if vals is not None:
                            writer.writerow(vals)
                        vals = [
                            site.code,
                            site.name,
                            associates,
                            source_codes_str,
                            gen_types_str,
                            start_date_str,
                            finish_date_str,
                            "used",
                            hh_start_ct.strftime("%Y-%m-%d"),
                        ]
                    used_gen_kwh = hh["imp_gen"] - hh["exp_net"] - hh["exp_gen"]
                    used_3p_kwh = hh["imp_3p"] - hh["exp_3p"]
                    used_kwh = hh["imp_net"] + used_gen_kwh + used_3p_kwh
                    vals.append(str(round(used_kwh, 2)))
                if vals is not None:
                    writer.writerow(vals)
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        f.write(msg)
    finally:
        if f is not None:
            f.close()


def do_post(sess):
    start_date = req_date("start", resolution="day")
    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    finish_day = req_int("finish_day")

    finish_date_ct = ct_datetime(finish_year, finish_month, finish_day, 23, 30)
    finish_date = to_utc(finish_date_ct)

    finish_date_str = finish_date_ct.strftime("%Y%m%d%H%M")
    if "site_id" in request.values:
        site_id = req_int("site_id")
        file_name = f"sites_hh_data_{site_id}_{finish_date_str}.csv"
        args = site_id, start_date, finish_date, g.user.id, file_name
        threading.Thread(target=site_content, args=args).start()
        return chellow_redirect("/downloads", 303)
    else:
        typ = req_str("type")
        site_codes_str = req_str("site_codes")
        site_codes = site_codes_str.splitlines()
        if len(site_codes) == 0:
            site_codes = None

        file_name = f"sites_hh_data_{finish_date_str}_filter.zip"
        args = site_codes, typ, start_date, finish_date, g.user.id, file_name
        threading.Thread(target=none_content, args=args).start()
        return chellow_redirect("/downloads", 303)
