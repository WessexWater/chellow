import csv
import os
import sys
import threading
import traceback
from datetime import datetime as Datetime

from flask import g, request

from sqlalchemy import or_
from sqlalchemy.sql.expression import null, true

import chellow.e.tnuos
from chellow.dloads import make_names
from chellow.e.computer import SupplySource, forecast_date
from chellow.e.duos import duos_vb
from chellow.models import Era, Pc, Session, Site, SiteEra, Source, Supply, User
from chellow.utils import (
    HH,
    csv_make_val,
    ct_datetime,
    hh_format,
    reduce_bill_hhs,
    req_int,
    to_utc,
)
from chellow.views import chellow_redirect


def _make_eras(sess, nov_start, year_finish, supply_id):
    eras = (
        sess.query(Era)
        .join(Supply)
        .join(Source)
        .join(Pc)
        .filter(
            Era.start_date <= year_finish,
            or_(Era.finish_date == null(), Era.finish_date >= nov_start),
            Source.code.in_(("net", "gen-net")),
            Pc.code == "00",
        )
        .order_by(Supply.id)
    )

    if supply_id is not None:
        eras = eras.filter(Supply.id == supply_id)

    return eras


def content(year, supply_id, user_id):
    caches = {}
    f = writer = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)
            running_name, finished_name = make_names("supplies_triad.csv", user)
            f = open(running_name, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")

            march_start = to_utc(ct_datetime(year, 3, 1))
            march_finish = to_utc(ct_datetime(year, 4, 1)) - HH
            nov_start = to_utc(ct_datetime(year - 1, 11, 1))

            scalar_names = {
                "triad-actual-gsp-kw",
                "triad-actual-gbp",
                "triad-estimate-gsp-kw",
                "triad-estimate-months",
                "triad-estimate-gbp",
                "triad-all-estimates-months",
                "triad-all-estimates-gbp",
            }

            rate_names = {"triad-actual-rate", "triad-estimate-rate"}

            for i in range(1, 4):
                for p in ("triad-actual-", "triad-estimate-"):
                    act_pref = f"{p}{i}-"
                    for suf in ("msp-kw", "gsp-kw"):
                        scalar_names.add(act_pref + suf)
                    for suf in ("date", "status", "laf"):
                        rate_names.add(act_pref + suf)

            def triad_csv(supply_source):
                if supply_source is None or supply_source.mpan_core.startswith("99"):
                    return [""] * 19

                duos_vb(supply_source)
                chellow.e.tnuos.hh(supply_source)
                for hh in supply_source.hh_data:
                    bill_hh = supply_source.supplier_bill_hhs[hh["start-date"]]
                    for k in scalar_names & hh.keys():
                        bill_hh[k] = hh[k]

                    for k in rate_names & hh.keys():
                        bill_hh[k] = {hh[k]}
                bill = reduce_bill_hhs(supply_source.supplier_bill_hhs)
                values = [supply_source.mpan_core]
                for i in range(1, 4):
                    triad_prefix = "triad-actual-" + str(i)
                    for suffix in ["-date", "-msp-kw", "-status", "-laf", "-gsp-kw"]:
                        values.append(csv_make_val(bill[triad_prefix + suffix]))

                suffixes = ["gsp-kw", "rate", "gbp"]
                values += [
                    csv_make_val(bill["triad-actual-" + suf]) for suf in suffixes
                ]
                return values

            writer.writerow(
                (
                    "Site Code",
                    "Site Name",
                    "Supply Name",
                    "Source",
                    "Generator Type",
                    "Import MPAN Core",
                    "Import T1 Date",
                    "Import T1 MSP kW",
                    "Import T1 Status",
                    "Import T1 LAF",
                    "Import T1 GSP kW",
                    "Import T2 Date",
                    "Import T2 MSP kW",
                    "Import T2 Status",
                    "Import T2 LAF",
                    "Import T2 GSP kW",
                    "Import T3 Date",
                    "Import T3 MSP kW",
                    "Import T3 Status",
                    "Import T3 LAF",
                    "Import T3 GSP kW",
                    "Import GSP kW",
                    "Import Rate GBP / kW",
                    "Import GBP",
                    "Export MPAN Core",
                    "Export T1 Date",
                    "Export T1 MSP kW",
                    "Export T1 Status",
                    "Export T1 LAF",
                    "Export T1 GSP kW",
                    "Export T2 Date",
                    "Export T2 MSP kW",
                    "Export T2 Status",
                    "Export T2 LAF",
                    "Export T2 GSP kW",
                    "Export T3 Date",
                    "Export T3 MSP kW",
                    "Export T3 Status",
                    "Export T3 LAF",
                    "Export T3 GSP kW",
                    "Export GSP kW",
                    "Export Rate GBP / kW",
                    "Export GBP",
                )
            )

            fdate = forecast_date()
            eras = _make_eras(sess, nov_start, march_finish, supply_id)

            for era in eras:
                site = (
                    sess.query(Site)
                    .join(SiteEra)
                    .filter(SiteEra.is_physical == true(), SiteEra.era == era)
                    .one()
                )
                supply = era.supply

                imp_mpan_core = era.imp_mpan_core
                if imp_mpan_core is None:
                    imp_supply_source = None
                else:
                    imp_supply_source = SupplySource(
                        sess, march_start, march_finish, fdate, era, True, caches
                    )

                exp_mpan_core = era.exp_mpan_core
                if exp_mpan_core is None:
                    exp_supply_source = None
                else:
                    exp_supply_source = SupplySource(
                        sess, march_start, march_finish, fdate, era, False, caches
                    )

                gen_type = supply.generator_type
                gen_type = "" if gen_type is None else gen_type.code
                vals = []
                for value in (
                    [site.code, site.name, supply.name, supply.source.code, gen_type]
                    + triad_csv(imp_supply_source)
                    + triad_csv(exp_supply_source)
                ):
                    if isinstance(value, Datetime):
                        vals.append(hh_format(value))
                    else:
                        vals.append(str(value))
                writer.writerow(vals)

                # Avoid a long-running transaction
                sess.rollback()
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if f is not None:
            f.close()
            os.rename(running_name, finished_name)


def do_get(sess):
    year = req_int("year")
    supply_id = req_int("supply_id") if "supply_id" in request.values else None
    threading.Thread(target=content, args=(year, supply_id, g.user.id)).start()
    return chellow_redirect("/downloads", 303)
