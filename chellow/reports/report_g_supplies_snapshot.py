import csv
import sys
import threading
import traceback

from flask import g, redirect, request

from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null

from werkzeug.exceptions import BadRequest

from chellow.dloads import open_file
from chellow.e.computer import contract_func
from chellow.gas.engine import GDataSource, forecast_date
from chellow.models import GEra, GSupply, Session
from chellow.utils import csv_make_val, req_date, req_int


def content(date, g_supply_id, user):
    try:
        with Session() as sess:
            f = open_file("g_supplies_snapshot.csv", user, mode="w", newline="")
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(
                (
                    "Date",
                    "Physical Site Id",
                    "Physical Site Name",
                    "Other Site Ids",
                    "Other Site Names",
                    "MPRN",
                    "Exit Zone",
                    "Meter Serial Number",
                    "Correction Factor",
                    "Unit",
                    "Contract",
                    "Account",
                    "Supply Start",
                    "Supply Finish",
                    "reading_frequency",
                    "aq",
                    "soq",
                )
            )
            fdate = forecast_date()
            caches = {}

            g_eras = (
                sess.query(GEra, GSupply)
                .join(GSupply)
                .filter(
                    GEra.start_date <= date,
                    or_(GEra.finish_date == null(), GEra.finish_date >= date),
                )
                .order_by(GSupply.mprn)
                .options(joinedload(GEra.site_g_eras))
            )

            if g_supply_id is not None:
                g_supply = GSupply.get_by_id(sess, g_supply_id)

                g_eras = g_eras.filter(GEra.g_supply == g_supply)

            for g_era, g_supply in g_eras:
                site_codes = []
                site_names = []
                for site_g_era in g_era.site_g_eras:
                    if site_g_era.is_physical:
                        physical_site = site_g_era.site
                    else:
                        site = site_g_era.site
                        site_codes.append(site.code)
                        site_names.append(site.name)

                sup_g_eras = (
                    sess.query(GEra)
                    .filter(GEra.g_supply == g_supply)
                    .order_by(GEra.start_date)
                    .all()
                )
                g_supply_start_date = sup_g_eras[0].start_date
                g_supply_finish_date = sup_g_eras[-1].finish_date

                ds = GDataSource(sess, date, date, fdate, g_era, caches, None)
                g_supplier_contract = g_era.g_contract
                vb_function = contract_func(caches, g_supplier_contract, "virtual_bill")
                if vb_function is None:
                    raise BadRequest(
                        f"The contract {g_supplier_contract.name} doesn't have the "
                        f"virtual_bill() function."
                    )
                vb_function(ds)
                bill = ds.bill

                writer.writerow(
                    csv_make_val(value)
                    for value in [
                        date,
                        physical_site.code,
                        physical_site.name,
                        site_codes,
                        site_names,
                        g_supply.mprn,
                        g_supply.g_exit_zone.code,
                        g_era.msn,
                        g_era.correction_factor,
                        g_era.g_unit.code,
                        g_supplier_contract.name,
                        g_era.account,
                        g_supply_start_date,
                        g_supply_finish_date,
                        g_era.g_reading_frequency.code,
                        bill["aq"],
                        bill["soq"],
                    ]
                )
    except BaseException:
        msg = traceback.format_exc()
        sys.stderr.write(msg)
        writer.writerow([msg])
    finally:
        if f is not None:
            f.close()


def do_get(session):
    user = g.user
    date = req_date("date")
    if "g_supply_id" in request.values:
        g_supply_id = req_int("g_supply_id")
    else:
        g_supply_id = None

    args = (date, g_supply_id, user)
    threading.Thread(target=content, args=args).start()
    return redirect("/downloads", 303)
