import csv
import threading
import traceback

from flask import g, redirect

from sqlalchemy import or_, select
from sqlalchemy.sql.expression import null, true

from werkzeug.exceptions import BadRequest

import chellow.e.computer
from chellow.dloads import open_file
from chellow.e.computer import SupplySource, contract_func
from chellow.models import (
    Contract,
    Era,
    MeasurementRequirement,
    Session,
    Site,
    SiteEra,
    Ssc,
    Tpr,
    User,
)
from chellow.utils import (
    c_months_u,
    csv_make_val,
    hh_max,
    hh_min,
    req_date,
    req_int,
    to_ct,
)


def _process_era(
    sess,
    caches,
    vb_func,
    forecast_date,
    bill_titles,
    contract,
    period_start,
    period_finish,
    era,
):
    chunk_start = hh_max(period_start, era.start_date)
    chunk_finish = hh_min(period_finish, era.finish_date)

    polarities = []
    if era.imp_supplier_contract == contract:
        polarities.append(True)
    if era.exp_supplier_contract == contract:
        polarities.append(False)
    for polarity in polarities:
        vals = []
        data_source = SupplySource(
            sess,
            chunk_start,
            chunk_finish,
            forecast_date,
            era,
            polarity,
            caches,
        )

        site = sess.scalars(
            select(Site)
            .join(SiteEra)
            .where(SiteEra.era == era, SiteEra.is_physical == true())
        ).one()

        if polarity:
            imp_is_substation = data_source.is_substation
            imp_llfc_code = data_source.llfc_code
            imp_llfc_description = data_source.llfc.description
            exp_is_substation = exp_llfc_code = exp_llfc_description = None
        else:
            exp_is_substation = data_source.is_substation
            exp_llfc_code = data_source.llfc_code
            exp_llfc_description = data_source.llfc.description
            imp_is_substation = imp_llfc_code = imp_llfc_description = None

        vals = {
            "mpan_core": data_source.mpan_core,
            "site_code": site.code,
            "site_name": site.name,
            "account": data_source.supplier_account,
            "from": data_source.start_date,
            "to": data_source.finish_date,
            "energisation_status": data_source.energisation_status_code,
            "gsp_group": data_source.gsp_group_code,
            "dno": data_source.dno_code,
            "era_start": era.start_date,
            "pc": data_source.pc_code,
            "meter_type": data_source.meter_type_code,
            "imp_is_substation": imp_is_substation,
            "imp_llfc_code": imp_llfc_code,
            "imp_llfc_description": imp_llfc_description,
            "exp_is_substation": exp_is_substation,
            "exp_llfc_code": exp_llfc_code,
            "exp_llfc_description": exp_llfc_description,
        }

        vb_func(data_source)
        bill = data_source.supplier_bill
        for title in bill_titles:
            if title in bill:
                vals[title] = bill[title]

        return vals


def create_csv(f, sess, start_date, finish_date, contract_id):
    caches = {}
    writer = csv.writer(f, lineterminator="\n")
    contract = Contract.get_supplier_by_id(sess, contract_id)
    forecast_date = chellow.e.computer.forecast_date()

    start_date_ct, finish_date_ct = to_ct(start_date), to_ct(finish_date)

    month_pairs = c_months_u(
        start_year=start_date_ct.year,
        start_month=start_date_ct.month,
        finish_year=finish_date_ct.year,
        finish_month=finish_date_ct.month,
    )

    bill_titles = contract_func(caches, contract, "virtual_bill_titles")()

    for tpr in (
        sess.query(Tpr)
        .join(MeasurementRequirement)
        .join(Ssc)
        .join(Era)
        .filter(
            Era.start_date <= finish_date,
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
            or_(
                Era.imp_supplier_contract == contract,
                Era.exp_supplier_contract == contract,
            ),
        )
        .order_by(Tpr.code)
        .distinct()
    ):
        for suffix in ("-kwh", "-rate", "-gbp"):
            bill_titles.append(tpr.code + suffix)
    header_titles = [
        "mpan_core",
        "site_code",
        "site_name",
        "account",
        "from",
        "to",
        "energisation_status",
        "gsp_group",
        "dno",
        "era_start",
        "pc",
        "meter_type",
        "imp_is_substation",
        "imp_llfc_code",
        "imp_llfc_description",
        "exp_is_substation",
        "exp_llfc_code",
        "exp_llfc_description",
    ]
    titles = header_titles + bill_titles
    writer.writerow(titles)
    vb_func = contract_func(caches, contract, "virtual_bill")

    for month_start, month_finish in month_pairs:
        period_start = hh_max(start_date, month_start)
        period_finish = hh_min(finish_date, month_finish)

        for era in (
            sess.query(Era)
            .filter(
                or_(
                    Era.imp_supplier_contract == contract,
                    Era.exp_supplier_contract == contract,
                ),
                Era.start_date <= period_finish,
                or_(Era.finish_date == null(), Era.finish_date >= period_start),
            )
            .order_by(Era.imp_mpan_core)
        ):
            try:
                vals = _process_era(
                    sess,
                    caches,
                    vb_func,
                    forecast_date,
                    bill_titles,
                    contract,
                    period_start,
                    period_finish,
                    era,
                )
                writer.writerow(csv_make_val(vals.get(t)) for t in titles)
            except BadRequest as e:
                raise BadRequest(f"Problem with /e/eras/{era.id}/edit {e.description}")

            sess.rollback()  # Avoid long-running transaction


def content(start_date, finish_date, contract_id, user_id):
    f = None
    try:
        with Session() as sess:
            user = User.get_by_id(sess, user_id)

            f = open_file("virtual_bills.csv", user, mode="w", newline="")

            create_csv(f, sess, start_date, finish_date, contract_id)

    except BadRequest as e:
        if f is None:
            raise
        else:
            f.write("\n" + e.description)
    except BaseException:
        if f is None:
            raise
        else:
            f.write(traceback.format_exc())
    finally:
        if f is not None:
            f.close()


def do_get(sess):
    start_date = req_date("start")
    finish_date = req_date("finish")
    contract_id = req_int("supplier_contract_id")

    threading.Thread(
        target=content, args=(start_date, finish_date, contract_id, g.user.id)
    ).start()
    return redirect("/downloads", 303)
