import os
import threading
import time
import traceback
from datetime import datetime as Datetime

from dateutil.relativedelta import relativedelta

from flask import g, request

import pytz

from sqlalchemy import Float, cast, func, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.sql.expression import null, true

import chellow.computer
import chellow.dloads
from chellow.models import Bill, Channel, Era, HhDatum, Session, Site, SiteEra, Supply
from chellow.utils import HH, hh_format, hh_max, hh_min, req_int
from chellow.views.home import chellow_redirect


def content(year, month, months, supply_id, user):
    tmp_file = sess = None
    try:
        sess = Session()
        supplies = (
            sess.query(Supply)
            .join(Era)
            .distinct()
            .options(joinedload(Supply.generator_type))
        )

        if supply_id is None:
            base_name = (
                "supplies_monthly_duration_for_all_supplies_for_"
                + str(months)
                + "_to_"
                + str(year)
                + "_"
                + str(month)
                + ".csv"
            )
        else:
            supply = Supply.get_by_id(sess, supply_id)
            supplies = supplies.filter(Supply.id == supply.id)
            base_name = (
                "supplies_monthly_duration_for_"
                + str(supply.id)
                + "_"
                + str(months)
                + "_to_"
                + str(year)
                + "_"
                + str(month)
                + ".csv"
            )
        running_name, finished_name = chellow.dloads.make_names(base_name, user)

        tmp_file = open(running_name, "w")

        caches = {}

        start_date = Datetime(year, month, 1, tzinfo=pytz.utc) - relativedelta(
            months=months - 1
        )

        field_names = (
            "supply-name",
            "source-code",
            "generator-type",
            "month",
            "pc-code",
            "msn",
            "site-code",
            "site-name",
            "metering-type",
            "import-mpan-core",
            "metered-import-kwh",
            "metered-import-net-gbp",
            "metered-import-estimated-kwh",
            "billed-import-kwh",
            "billed-import-net-gbp",
            "export-mpan-core",
            "metered-export-kwh",
            "metered-export-estimated-kwh",
            "billed-export-kwh",
            "billed-export-net-gbp",
            "problem",
            "timestamp",
        )

        tmp_file.write("supply-id," + ",".join(field_names) + "\n")

        forecast_date = chellow.computer.forecast_date()

        for i in range(months):
            month_start = start_date + relativedelta(months=i)
            month_finish = month_start + relativedelta(months=1) - HH

            for supply in supplies.filter(
                Era.start_date <= month_finish,
                or_(Era.finish_date == null(), Era.finish_date >= month_start),
            ):

                generator_type = supply.generator_type
                if generator_type is None:
                    generator_type = ""
                else:
                    generator_type = generator_type.code

                source_code = supply.source.code
                eras = supply.find_eras(sess, month_start, month_finish)
                era = eras[-1]
                metering_type = era.meter_category

                site = (
                    sess.query(Site)
                    .join(SiteEra)
                    .filter(SiteEra.era == era, SiteEra.is_physical == true())
                    .one()
                )

                values = {
                    "supply-name": supply.name,
                    "source-code": source_code,
                    "generator-type": generator_type,
                    "month": hh_format(month_finish),
                    "pc-code": era.pc.code,
                    "msn": era.msn,
                    "site-code": site.code,
                    "site-name": site.name,
                    "metering-type": metering_type,
                    "problem": "",
                }

                tmp_file.write(str(supply.id) + ",")

                for is_import, pol_name in [(True, "import"), (False, "export")]:
                    if is_import:
                        mpan_core = era.imp_mpan_core
                    else:
                        mpan_core = era.exp_mpan_core

                    values[pol_name + "-mpan-core"] = mpan_core
                    kwh = 0
                    est_kwh = 0

                    if metering_type in ["hh", "amr"]:
                        est_kwh = (
                            sess.query(HhDatum.value)
                            .join(Channel)
                            .join(Era)
                            .filter(
                                HhDatum.status == "E",
                                Era.supply_id == supply.id,
                                Channel.channel_type == "ACTIVE",
                                Channel.imp_related == is_import,
                                HhDatum.start_date >= month_start,
                                HhDatum.start_date <= month_finish,
                            )
                            .first()
                        )
                        if est_kwh is None:
                            est_kwh = 0
                        else:
                            est_kwh = est_kwh[0]

                    if not (is_import and source_code in ("net", "gen-net")):
                        kwh_sum = (
                            sess.query(cast(func.sum(HhDatum.value), Float))
                            .join(Channel)
                            .join(Era)
                            .filter(
                                Era.supply_id == supply.id,
                                Channel.channel_type == "ACTIVE",
                                Channel.imp_related == is_import,
                                HhDatum.start_date >= month_start,
                                HhDatum.start_date <= month_finish,
                            )
                            .one()[0]
                        )
                        if kwh_sum is not None:
                            kwh += kwh_sum

                    values["metered-" + pol_name + "-estimated-kwh"] = est_kwh
                    values["metered-" + pol_name + "-kwh"] = kwh
                    values["metered-" + pol_name + "-net-gbp"] = 0
                    values["billed-" + pol_name + "-kwh"] = 0
                    values["billed-" + pol_name + "-net-gbp"] = 0
                    values["billed-" + pol_name + "-apportioned-kwh"] = 0
                    values["billed-" + pol_name + "-apportioned-net-gbp"] = 0
                    values["billed-" + pol_name + "-raw-kwh"] = 0
                    values["billed-" + pol_name + "-raw-net-gbp"] = 0

                for bill in sess.query(Bill).filter(
                    Bill.supply == supply,
                    Bill.start_date <= month_finish,
                    Bill.finish_date >= month_start,
                ):
                    bill_start = bill.start_date
                    bill_finish = bill.finish_date
                    bill_duration = (bill_finish - bill_start).total_seconds() + 30 * 60
                    overlap_duration = (
                        min(bill_finish, month_finish) - max(bill_start, month_start)
                    ).total_seconds() + 30 * 60
                    overlap_proportion = float(overlap_duration) / float(bill_duration)
                    values["billed-import-net-gbp"] += overlap_proportion * float(
                        bill.net
                    )
                    values["billed-import-kwh"] += overlap_proportion * float(bill.kwh)

                for era in eras:
                    chunk_start = hh_max(era.start_date, month_start)
                    chunk_finish = hh_min(era.finish_date, month_finish)

                    import_mpan_core = era.imp_mpan_core
                    if import_mpan_core is None:
                        continue

                    supplier_contract = era.imp_supplier_contract

                    if source_code in ["net", "gen-net", "3rd-party"]:
                        supply_source = chellow.computer.SupplySource(
                            sess,
                            chunk_start,
                            chunk_finish,
                            forecast_date,
                            era,
                            True,
                            caches,
                        )

                        values["metered-import-kwh"] += sum(
                            datum["msp-kwh"] for datum in supply_source.hh_data
                        )

                        import_vb_function = supply_source.contract_func(
                            supplier_contract, "virtual_bill"
                        )
                        if import_vb_function is None:
                            values["problem"] += (
                                "Can't find the "
                                "virtual_bill  function in the supplier "
                                "contract. "
                            )
                        else:
                            import_vb_function(supply_source)
                            values[
                                "metered-import-net-gbp"
                            ] += supply_source.supplier_bill["net-gbp"]

                        supply_source.contract_func(era.dc_contract, "virtual_bill")(
                            supply_source
                        )
                        values["metered-import-net-gbp"] += supply_source.dc_bill[
                            "net-gbp"
                        ]

                        mop_func = supply_source.contract_func(
                            era.mop_contract, "virtual_bill"
                        )
                        if mop_func is None:
                            values["problem"] += (
                                " MOP virtual_bill " "function can't be found."
                            )
                        else:
                            mop_func(supply_source)
                            mop_bill = supply_source.mop_bill
                            values["metered-import-net-gbp"] += mop_bill["net-gbp"]
                            if len(mop_bill["problem"]) > 0:
                                values["problem"] += (
                                    " MOP virtual bill problem: " + mop_bill["problem"]
                                )

                values["timestamp"] = int(time.time() * 1000)
                tmp_file.write(
                    ",".join('"' + str(values[name]) + '"' for name in field_names)
                    + "\n"
                )
    except BaseException:
        tmp_file.write(traceback.format_exc())
    finally:
        if sess is not None:
            sess.close()
        tmp_file.close()
        os.rename(running_name, finished_name)


def do_get(sess):
    year = req_int("end_year")
    month = req_int("end_month")
    months = req_int("months")
    supply_id = req_int("supply_id") if "supply_id" in request.values else None
    user = g.user
    threading.Thread(
        target=content, args=(year, month, months, supply_id, user)
    ).start()
    return chellow_redirect("/downloads", 303)
