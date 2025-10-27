import csv
from collections import defaultdict
from datetime import datetime as Datetime
from decimal import Decimal
from importlib import import_module
from io import BytesIO, StringIO


from dateutil.relativedelta import relativedelta

from flask import (
    Blueprint,
    flash,
    g,
    make_response,
    redirect,
    render_template as rtemplate,
    request,
)

from sqlalchemy import false, func, null, select, text, true
from sqlalchemy.orm import aliased, joinedload


from werkzeug.exceptions import BadRequest

from zish import dumps, loads

import chellow.gas.bill_import
import chellow.gas.dn_rate_parser
from chellow.models import (
    BillType,
    Contract,
    GBatch,
    GBill,
    GContract,
    GDn,
    GEra,
    GExitZone,
    GLdz,
    GRateScript,
    GReadType,
    GReadingFrequency,
    GRegisterRead,
    GSupply,
    GUnit,
    Report,
    Site,
    SiteGEra,
)
from chellow.utils import (
    HH,
    csv_make_val,
    req_checkbox,
    req_date,
    req_decimal,
    req_file,
    req_int,
    req_str,
    req_zish,
    utc_datetime,
    utc_datetime_now,
)
from chellow.views import hx_redirect as chx_redirect


def chellow_redirect(path, code=None):
    return redirect(f"/g{path}", code)


def hx_redirect(path, code=None):
    return chx_redirect(f"/g{path}", code)


gas = Blueprint("g", __name__, template_folder="templates", url_prefix="/g")


def render_template(tname, **kwargs):
    return rtemplate(f"g/{tname}", **kwargs)


@gas.route("/supplies")
def supplies_get():
    if "search_pattern" in request.values:
        pattern = req_str("search_pattern")
        pattern = pattern.strip()
        reduced_pattern = pattern.replace(" ", "")
        if "max_results" in request.values:
            max_results = req_int("max_results")
        else:
            max_results = 50

        g_eras = (
            g.sess.query(GEra)
            .from_statement(
                text(
                    "select e1.* from g_era as e1 "
                    "inner join (select e2.g_supply_id, max(e2.start_date) "
                    "as max_start_date from g_era as e2 "
                    "join g_supply on (e2.g_supply_id = g_supply.id) "
                    "where replace(lower(g_supply.mprn), ' ', '') "
                    "like lower(:reducedPattern) "
                    "or lower(e2.account) like lower(:pattern) "
                    "or lower(e2.msn) like lower(:pattern) "
                    "group by e2.g_supply_id) as sq "
                    "on e1.g_supply_id = sq.g_supply_id "
                    "and e1.start_date = sq.max_start_date limit :max_results"
                )
            )
            .params(
                pattern="%" + pattern + "%",
                reducedPattern="%" + reduced_pattern + "%",
                max_results=max_results,
            )
            .all()
        )
        if len(g_eras) == 1:
            return chellow_redirect(f"/supplies/{g_eras[0].g_supply.id}")
        else:
            return render_template(
                "supplies.html", g_eras=g_eras, max_results=max_results
            )
    else:
        return render_template("supplies.html")


@gas.route("/supplies/<int:g_supply_id>")
def supply_get(g_supply_id):
    debug = ""
    try:
        g_era_bundles = []
        g_supply = GSupply.get_by_id(g.sess, g_supply_id)
        g_eras = g.sess.scalars(
            select(GEra)
            .where(GEra.g_supply == g_supply)
            .order_by(GEra.start_date.desc())
        ).all()
        for g_era in g_eras:
            physical_site = (
                g.sess.query(Site)
                .join(SiteGEra)
                .filter(SiteGEra.is_physical == true(), SiteGEra.g_era == g_era)
                .one()
            )
            other_sites = (
                g.sess.query(Site)
                .join(SiteGEra)
                .filter(SiteGEra.is_physical != true(), SiteGEra.g_era == g_era)
                .all()
            )
            g_bill_dicts = []
            g_era_bundle = {
                "g_era": g_era,
                "physical_site": physical_site,
                "other_sites": other_sites,
                "g_bill_dicts": g_bill_dicts,
            }
            g_era_bundles.append(g_era_bundle)

            g_era_bundle["shared_accounts"] = (
                g.sess.query(GSupply)
                .distinct()
                .join(GEra)
                .filter(
                    GSupply.id != g_supply.id,
                    GEra.account == g_era.account,
                    GEra.g_contract == g_era.g_contract,
                )
                .all()
            )

            g_bills = (
                select(GBill)
                .where(GBill.g_supply == g_supply)
                .order_by(
                    GBill.start_date.desc(),
                    GBill.issue_date.desc(),
                    GBill.reference.desc(),
                )
            )
            if g_era != g_eras[0]:
                g_bills = g_bills.where(GBill.start_date < g_era.finish_date)
            if g_era != g_eras[-1]:
                g_bills = g_bills.where(GBill.start_date >= g_era.start_date)

            for g_bill in g.sess.scalars(g_bills):
                g_reads = (
                    g.sess.query(GRegisterRead)
                    .filter(GRegisterRead.g_bill == g_bill)
                    .order_by(GRegisterRead.pres_date.desc())
                    .options(
                        joinedload(GRegisterRead.prev_type),
                        joinedload(GRegisterRead.pres_type),
                    )
                    .all()
                )
                g_bill_dicts.append({"g_bill": g_bill, "g_reads": g_reads})

            b_dicts = list(reversed(g_bill_dicts))
            for i, b_dict in enumerate(b_dicts):
                if i < (len(b_dicts) - 1):
                    g_bill = b_dict["g_bill"]
                    next_b_dict = b_dicts[i + 1]
                    next_g_bill = next_b_dict["g_bill"]
                    if (
                        g_bill.start_date,
                        g_bill.finish_date,
                        g_bill.kwh,
                        g_bill.net,
                    ) == (
                        next_g_bill.start_date,
                        next_g_bill.finish_date,
                        -1 * next_g_bill.kwh,
                        -1 * next_g_bill.net,
                    ) and "collapsible" not in b_dict:
                        b_dict["collapsible"] = True
                        next_b_dict["first_collapsible"] = True
                        next_b_dict["collapsible"] = True
                        b_dict["collapse_id"] = next_b_dict["collapse_id"] = g_bill.id

        RELATIVE_YEAR = relativedelta(years=1)

        now = utc_datetime_now()
        triad_year = (now - RELATIVE_YEAR).year if now.month < 3 else now.year
        this_month_start = Datetime(now.year, now.month, 1)
        last_month_start = this_month_start - relativedelta(months=1)
        last_month_finish = this_month_start - relativedelta(minutes=30)

        batch_reports = []
        config_contract = Contract.get_non_core_by_name(g.sess, "configuration")
        properties = config_contract.make_properties()
        if "g_supply_reports" in properties:
            for report_id in properties["g_supply_reports"]:
                batch_reports.append(Report.get_by_id(g.sess, report_id))

        note = truncated_line = None
        g_supply_note = (
            {"notes": []} if len(g_supply.note.strip()) == 0 else loads(g_supply.note)
        )

        notes = g_supply_note["notes"]
        if len(notes) > 0:
            note = notes[-1]
            lines = note["body"].splitlines()
            if len(lines) > 0:
                line0 = lines[0]
                if len(lines) > 1 or len(line0) > 50:
                    truncated_line = line0[:50]
        return render_template(
            "supply.html",
            triad_year=triad_year,
            now=now,
            last_month_start=last_month_start,
            last_month_finish=last_month_finish,
            g_era_bundles=g_era_bundles,
            g_supply=g_supply,
            system_properties=properties,
            truncated_line=truncated_line,
            note=note,
            this_month_start=this_month_start,
            batch_reports=batch_reports,
            debug=debug,
        )

    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return render_template("supply.html")


@gas.route("/supplies/<int:g_supply_id>/edit")
def supply_edit_get(g_supply_id):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)
    g_eras = (
        g.sess.query(GEra)
        .filter(GEra.g_supply == g_supply)
        .order_by(GEra.start_date.desc())
    )
    g_exit_zones = g.sess.query(GExitZone).order_by(GExitZone.code).all()
    return render_template(
        "supply_edit.html",
        g_supply=g_supply,
        g_eras=g_eras,
        g_exit_zones=g_exit_zones,
    )


@gas.route("/supplies/<int:g_supply_id>/edit", methods=["DELETE"])
def supply_edit_delete(g_supply_id):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)
    try:
        g_supply.delete(g.sess)
        g.sess.commit()
        return hx_redirect("/supplies")
    except BadRequest as e:
        flash(e.description)
        g_eras = g.sess.scalars(
            select(GEra)
            .where(GEra.g_supply == g_supply)
            .order_by(GEra.start_date.desc())
        )
        g_exit_zones = g.sess.query(GExitZone).order_by(GExitZone.code).all()
        return make_response(
            render_template(
                "supply_edit.html",
                g_supply=g_supply,
                g_eras=g_eras,
                g_exit_zones=g_exit_zones,
            ),
            400,
        )


@gas.route("/supplies/<int:g_supply_id>/edit", methods=["POST"])
def supply_edit_post(g_supply_id):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)
    try:
        if "insert_g_era" in request.values:
            start_date = req_date("start")
            g_supply.insert_g_era_at(g.sess, start_date)
            g.sess.commit()
            return chellow_redirect(f"/supplies/{g_supply.id}", 303)
        else:
            mprn = req_str("mprn")
            name = req_str("name")
            g_exit_zone_id = req_int("g_exit_zone_id")
            g_exit_zone = GExitZone.get_by_id(g.sess, g_exit_zone_id)
            g_supply.update(mprn, name, g_exit_zone)
            g.sess.commit()
            return chellow_redirect(f"/supplies/{g_supply.id}", 303)
    except BadRequest as e:
        flash(e.description)
        g_eras = (
            g.sess.query(GEra)
            .filter(GEra.g_supply == g_supply)
            .order_by(GEra.start_date.desc())
        )
        g_exit_zones = g.sess.query(GExitZone).order_by(GExitZone.code).all()
        return make_response(
            render_template(
                "supply_edit.html",
                g_supply=g_supply,
                g_eras=g_eras,
                g_exit_zones=g_exit_zones,
            ),
            400,
        )


@gas.route("/batches")
def batches_get():
    g_contract_id = req_int("g_contract_id")
    g_contract = GContract.get_by_id(g.sess, g_contract_id)
    g_batches = g.sess.execute(
        select(
            GBatch,
            func.count(GBill.id),
            func.coalesce(func.sum(GBill.net), 0),
            func.coalesce(func.sum(GBill.vat), 0),
            func.coalesce(func.sum(GBill.gross), 0),
            func.coalesce(func.sum(GBill.kwh), 0),
        )
        .join(GBill, isouter=True)
        .where(GBatch.g_contract == g_contract)
        .group_by(GBatch.id)
        .order_by(GBatch.reference.desc())
    )
    return render_template("batches.html", g_contract=g_contract, g_batches=g_batches)


@gas.route("/supplier_contracts/<int:g_contract_id>/add_batch")
def batch_add_get(g_contract_id):
    g_contract = GContract.get_by_id(g.sess, g_contract_id)
    g_batches = g.sess.execute(
        select(GBatch)
        .where(GBatch.g_contract == g_contract)
        .order_by(GBatch.reference.desc())
    ).scalars()
    return render_template("batch_add.html", g_contract=g_contract, g_batches=g_batches)


@gas.route("/supplier_contracts/<int:g_contract_id>/add_batch", methods=["POST"])
def batch_add_post(g_contract_id):
    try:
        g_contract = GContract.get_by_id(g.sess, g_contract_id)
        reference = req_str("reference")
        description = req_str("description")

        g_batch = g_contract.insert_g_batch(g.sess, reference, description)
        g.sess.commit()
        return chellow_redirect(f"/batches/{g_batch.id}", 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        g_batches = g.sess.execute(
            select(GBatch)
            .where(GBatch.g_contract == g_contract)
            .order_by(GBatch.reference.desc())
        )
        return make_response(
            render_template(
                "batch_add.html", g_contract=g_contract, g_batches=g_batches
            ),
            400,
        )


@gas.route("/batches/<int:g_batch_id>")
def batch_get(g_batch_id):
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)

    num_bills = sum_net_gbp = sum_vat_gbp = sum_gross_gbp = sum_kwh = 0
    vat_breakdown = {}
    max_reads = 0

    g_bills = (
        g.sess.execute(
            select(GBill)
            .where(GBill.g_batch == g_batch)
            .order_by(GBill.reference, GBill.start_date)
        )
        .scalars()
        .all()
    )

    for g_bill in g_bills:
        num_bills += 1
        sum_net_gbp += g_bill.net
        sum_vat_gbp += g_bill.vat
        sum_gross_gbp += g_bill.gross
        sum_kwh += g_bill.kwh
        max_reads = max(len(g_bill.g_reads), max_reads)

        if g_bill.vat != 0:
            bd = g_bill.make_breakdown()

            if "vat_rate" in bd:
                vat_tuple = tuple([str(v * 100) for v in sorted(bd["vat_rate"])])
                vat_percentage = vat_tuple[0] if len(vat_tuple) == 1 else vat_tuple
                try:
                    vbd = vat_breakdown[vat_percentage]
                except KeyError:
                    vbd = vat_breakdown[vat_percentage] = defaultdict(int)

                vbd["vat"] += g_bill.vat
                vbd["net"] += g_bill.net

            if "vat" in bd:
                for vat_percentage, vat_bd in bd["vat"].items():
                    try:
                        vbd = vat_breakdown[vat_percentage]
                    except KeyError:
                        vbd = vat_breakdown[vat_percentage] = defaultdict(int)

                    vbd["vat"] += vat_bd.get("vat", Decimal("0"))
                    vbd["net"] += vat_bd.get("net", Decimal("0"))

    config_contract = Contract.get_non_core_by_name(g.sess, "configuration")
    properties = config_contract.make_properties()

    if "g_batch_reports" in properties:
        g_batch_reports = []
        for report_id in properties["g_batch_reports"]:
            g_batch_reports.append(Report.get_by_id(g.sess, report_id))
    else:
        g_batch_reports = None

    return render_template(
        "batch.html",
        g_batch_reports=g_batch_reports,
        g_batch=g_batch,
        g_bills=g_bills,
        max_reads=max_reads,
        num_bills=num_bills,
        sum_net_gbp=sum_net_gbp,
        sum_vat_gbp=sum_vat_gbp,
        sum_gross_gbp=sum_gross_gbp,
        sum_kwh=sum_kwh,
        vat_breakdown=vat_breakdown,
    )


@gas.route("/batches/<int:g_batch_id>/edit")
def batch_edit_get(g_batch_id):
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)
    return render_template("batch_edit.html", g_batch=g_batch)


@gas.route("/batches/<int:g_batch_id>/edit", methods=["POST"])
def batch_edit_post(g_batch_id):
    try:
        g_batch = GBatch.get_by_id(g.sess, g_batch_id)
        if "update" in request.values:
            reference = req_str("reference")
            description = req_str("description")
            g_batch.update(g.sess, reference, description)
            g.sess.commit()
            return chellow_redirect(f"/batches/{g_batch.id}", 303)
        elif "delete_bills" in request.values:
            g.sess.query(GBill).filter(GBill.g_batch == g_batch).delete(False)
            g.sess.commit()
            return hx_redirect(f"/batches/{g_batch.id}")
    except BadRequest as e:
        flash(e.description)
        return make_response(render_template("batch_edit.html", g_batch=g_batch), 400)


@gas.route("/batches/<int:g_batch_id>/edit", methods=["DELETE"])
def batch_edit_delete(g_batch_id):
    try:
        g_batch = GBatch.get_by_id(g.sess, g_batch_id)
        g_contract = g_batch.g_contract
        g_batch.delete(g.sess)
        g.sess.commit()
        return hx_redirect(f"/batches?g_contract_id={g_contract.id}")
    except BadRequest as e:
        flash(e.description)
        return make_response(render_template("batch_edit.html", g_batch=g_batch), 400)


@gas.route("/bills/<int:g_bill_id>")
def bill_get(g_bill_id):
    g_bill = GBill.get_by_id(g.sess, g_bill_id)
    g_reads = (
        g.sess.query(GRegisterRead)
        .filter(GRegisterRead.g_bill == g_bill)
        .order_by(GRegisterRead.pres_date.desc())
    )
    fields = {"g_bill": g_bill, "g_reads": g_reads}
    try:
        breakdown = g_bill.make_breakdown()

        raw_lines = g_bill.raw_lines

        rows = set()
        columns = set()
        grid = defaultdict(dict)

        for k, v in tuple(breakdown.items()):
            if k.endswith("_gbp"):
                columns.add("gbp")
                row_name = k[:-4]
                rows.add(row_name)
                grid[row_name]["gbp"] = v
                del breakdown[k]

        for k, v in tuple(breakdown.items()):
            for row_name in sorted(list(rows), key=len, reverse=True):
                if k.startswith(row_name + "_"):
                    col_name = k[len(row_name) + 1 :]
                    columns.add(col_name)
                    grid[row_name][col_name] = csv_make_val(v)
                    del breakdown[k]
                    break

        for k, v in breakdown.items():
            pair = k.split("_")
            row_name = "_".join(pair[:-1])
            column_name = pair[-1]
            rows.add(row_name)
            columns.add(column_name)
            grid[row_name][column_name] = csv_make_val(v)

        column_list = sorted(list(columns))
        for rate_name in [col for col in column_list if col.endswith("rate")]:
            column_list.remove(rate_name)
            column_list.append(rate_name)

        if "gbp" in column_list:
            column_list.remove("gbp")
            column_list.append("gbp")

        row_list = sorted(list(rows))
        fields.update(
            {
                "raw_lines": raw_lines,
                "row_list": row_list,
                "column_list": column_list,
                "grid": grid,
            }
        )
    except SyntaxError:
        pass

    return render_template("bill.html", **fields)


@gas.route("/bill_imports")
def bill_imports_get():
    g_batch_id = req_int("g_batch_id")
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)
    importer_ids = sorted(
        chellow.gas.bill_import.get_bill_importer_ids(g_batch.id), reverse=True
    )
    parser_names = chellow.gas.bill_import.find_parser_names()
    g_contract_props = g_batch.g_contract.make_properties()

    return render_template(
        "bill_imports.html",
        importer_ids=importer_ids,
        g_batch=g_batch,
        parser_names=parser_names,
        default_bill_parser_name=g_contract_props.get("default_bill_parser", ""),
    )


@gas.route("/bill_imports", methods=["POST"])
def bill_imports_post():
    try:
        g_batch_id = req_int("g_batch_id")
        g_batch = GBatch.get_by_id(g.sess, g_batch_id)
        file_item = req_file("import_file")
        file_bytes = file_item.stream.read()
        parser_name = req_str("parser_name")
        imp_id = chellow.gas.bill_import.start_bill_importer(
            g.sess, g_batch.id, file_item.filename, file_bytes, parser_name
        )
        return chellow_redirect(f"/bill_imports/{imp_id}", 303)
    except BadRequest as e:
        flash(e.description)
        importer_ids = sorted(
            chellow.gas.bill_import.get_bill_importer_ids(g_batch.id), reverse=True
        )
        g_contract_props = g_batch.g_contract.make_properties()
        return make_response(
            render_template(
                "bill_imports.html",
                importer_ids=importer_ids,
                g_batch=g_batch,
                parser_names=chellow.gas.bill_import.find_parser_names(),
                default_bill_parser_name=g_contract_props.get(
                    "default_bill_parser", ""
                ),
            ),
            400,
        )


@gas.route("/bill_imports/<int:imp_id>")
def bill_import_get(imp_id):
    importer = chellow.gas.bill_import.get_bill_importer(imp_id)
    g_batch = GBatch.get_by_id(g.sess, importer.g_batch_id)
    fields = {"g_batch": g_batch}
    if importer is not None:
        imp_fields = importer.make_fields()
        if "successful_bills" in imp_fields and len(imp_fields["successful_bills"]) > 0:
            fields["successful_max_registers"] = max(
                len(bill["reads"]) for bill in imp_fields["successful_bills"]
            )
        fields.update(imp_fields)
        fields["status"] = importer.status()
    return render_template("bill_import.html", **fields)


@gas.route("/batches/<int:g_batch_id>/add_bill")
def bill_add_get(g_batch_id):
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)
    g_bills = (
        g.sess.query(GBill).filter(GBill.g_batch == g_batch).order_by(GBill.start_date)
    )
    bill_types = g.sess.query(BillType).order_by(BillType.code).all()
    return render_template(
        "bill_add.html", g_batch=g_batch, g_bills=g_bills, bill_types=bill_types
    )


@gas.route("/batches/<int:g_batch_id>/add_bill", methods=["POST"])
def bill_add_post(g_batch_id):
    try:
        g_batch = GBatch.get_by_id(g.sess, g_batch_id)
        bill_type_id = req_int("bill_type_id")
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        mprn = req_str("mprn")
        g_supply = GSupply.get_by_mprn(g.sess, mprn)
        account = req_str("account")
        reference = req_str("reference")
        issue_date = req_date("issue")
        start_date = req_date("start")
        finish_date = req_date("finish")
        kwh = req_decimal("kwh")
        net = req_decimal("net")
        vat = req_decimal("vat")
        gross = req_decimal("gross")
        breakdown = req_zish("breakdown")
        g_bill = g_batch.insert_g_bill(
            g.sess,
            g_supply,
            bill_type,
            reference,
            account,
            issue_date,
            start_date,
            finish_date,
            kwh,
            net,
            vat,
            gross,
            "",
            breakdown,
        )
        g.sess.commit()
        return chellow_redirect(f"/bills/{g_bill.id}", 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        g_bills = (
            g.sess.query(GBill)
            .filter(GBill.g_batch == g_batch)
            .order_by(GBill.start_date)
        )
        bill_types = g.sess.query(BillType).order_by(BillType.code).all()
        return make_response(
            render_template(
                "bill_add.html",
                g_batch=g_batch,
                g_bills=g_bills,
                bill_types=bill_types,
            ),
            400,
        )


@gas.route("/supplies/<int:g_supply_id>/notes")
def supply_notes_get(g_supply_id):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)

    if len(g_supply.note.strip()) > 0:
        g_supply_note = loads(g_supply.note)
    else:
        g_supply_note = {"notes": []}

    return render_template(
        "supply_notes.html", g_supply=g_supply, g_supply_note=g_supply_note
    )


@gas.route("/supplies/<int:g_supply_id>/notes/add")
def supply_note_add_get(g_supply_id):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)
    return render_template("supply_note_add.html", g_supply=g_supply)


@gas.route("/supplies/<int:g_supply_id>/notes/add", methods=["POST"])
def supply_note_add_post(g_supply_id):
    try:
        g_supply = GSupply.get_by_id(g.sess, g_supply_id)
        body = req_str("body")
        if len(g_supply.note.strip()) == 0:
            note_dict = {"notes": []}
        else:
            note_dict = loads(g_supply.note)

        note_dict["notes"].append({"body": body, "timestamp": utc_datetime_now()})
        g_supply.note = dumps(note_dict)
        g.sess.commit()
        return chellow_redirect(f"/supplies/{g_supply_id}", 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template("supply_note_add.html", g_supply=g_supply), 400
        )


@gas.route("/supplies/<int:g_supply_id>/notes/<int:index>/edit")
def supply_note_edit_get(g_supply_id, index):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)
    g_supply_note = loads(g_supply.note)
    note = g_supply_note["notes"][index]
    note["index"] = index
    return render_template("supply_note_edit.html", g_supply=g_supply, note=note)


@gas.route("/supplies/<int:g_supply_id>/notes/<int:index>/edit", methods=["DELETE"])
def supply_note_edit_delete(g_supply_id, index):
    try:
        g_supply = GSupply.get_by_id(g.sess, g_supply_id)
        g_supply_note = loads(g_supply.note)
        del g_supply_note["notes"][index]
        g_supply.note = dumps(g_supply_note)
        g.sess.commit()
        return hx_redirect(f"/supplies/{g_supply_id}/notes")
    except BadRequest as e:
        flash(e.description)
        g_supply_note = loads(g_supply.note)
        note = g_supply_note["notes"][index]
        note["index"] = index
        return render_template("supply_note_edit.html", g_supply=g_supply, note=note)


@gas.route("/supplies/<int:g_supply_id>/notes/<int:index>/edit", methods=["POST"])
def supply_note_edit_post(g_supply_id, index):
    try:
        g_supply = GSupply.get_by_id(g.sess, g_supply_id)
        g_supply_note = loads(g_supply.note)
        body = req_str("body")
        note = g_supply_note["notes"][index]
        note["body"] = body
        g_supply.note = dumps(g_supply_note)
        g.sess.commit()
        return hx_redirect(f"/supplies/{g_supply_id}/notes/{index}")
    except BadRequest as e:
        flash(e.description)
        g_supply_note = loads(g_supply.note)
        note = g_supply_note["notes"][index]
        note["index"] = index
        return render_template("supply_note_edit.html", g_supply=g_supply, note=note)


@gas.route("/eras/<int:g_era_id>/edit")
def era_edit_get(g_era_id):
    g_era = GEra.get_by_id(g.sess, g_era_id)
    supplier_g_contracts = g.sess.scalars(
        select(GContract)
        .where(GContract.is_industry == false())
        .order_by(GContract.name)
    )
    site_g_eras = (
        g.sess.query(SiteGEra)
        .join(Site)
        .filter(SiteGEra.g_era == g_era)
        .order_by(Site.code)
        .all()
    )
    g_units = g.sess.query(GUnit).order_by(GUnit.code).all()
    g_reading_frequencies = (
        g.sess.query(GReadingFrequency).order_by(GReadingFrequency.code).all()
    )
    return render_template(
        "era_edit.html",
        g_era=g_era,
        supplier_g_contracts=supplier_g_contracts,
        site_g_eras=site_g_eras,
        g_units=g_units,
        g_reading_frequencies=g_reading_frequencies,
    )


@gas.route("/eras/<int:g_era_id>/edit", methods=["POST"])
def era_edit_post(g_era_id):
    try:
        g_era = GEra.get_by_id(g.sess, g_era_id)

        if "delete" in request.values:
            g_supply = g_era.g_supply
            g_supply.delete_g_era(g.sess, g_era)
            g.sess.commit()
            return chellow_redirect(f"/supplies/{g_supply.id}", 303)

        elif "attach" in request.values:
            site_code = req_str("site_code")
            site = Site.get_by_code(g.sess, site_code)
            g_era.attach_site(g.sess, site)
            g.sess.commit()
            return chellow_redirect(f"/supplies/{g_era.g_supply.id}", 303)

        elif "detach" in request.values:
            site_id = req_int("site_id")
            site = Site.get_by_id(g.sess, site_id)
            g_era.detach_site(g.sess, site)
            g.sess.commit()
            return chellow_redirect(f"/supplies/{g_era.g_supply.id}", 303)

        elif "locate" in request.values:
            site_id = req_int("site_id")
            site = Site.get_by_id(g.sess, site_id)
            g_era.set_physical_location(g.sess, site)
            g.sess.commit()
            return chellow_redirect(f"/supplies/{g_era.g_supply.id}", 303)

        else:
            start_date = req_date("start")
            is_ended = req_checkbox("is_ended")
            finish_date = req_date("finish") if is_ended else None
            msn = req_str("msn")
            correction_factor = req_decimal("correction_factor")
            g_contract_id = req_int("g_contract_id")
            g_contract = GContract.get_by_id(g.sess, g_contract_id)
            account = req_str("account")
            g_unit_id = req_int("g_unit_id")
            g_unit = GUnit.get_by_id(g.sess, g_unit_id)
            g_reading_frequency_id = req_int("g_reading_frequency_id")
            g_reading_frequency = GReadingFrequency.get_by_id(
                g.sess, g_reading_frequency_id
            )
            aq = req_decimal("aq")
            soq = req_decimal("soq")
            g_era.g_supply.update_g_era(
                g.sess,
                g_era,
                start_date,
                finish_date,
                msn,
                correction_factor,
                g_unit,
                g_contract,
                account,
                g_reading_frequency,
                aq,
                soq,
            )
            g.sess.commit()
            return chellow_redirect(f"/supplies/{g_era.g_supply.id}", 303)

    except BadRequest as e:
        flash(e.description)
        supplier_g_contracts = g.sess.query(GContract).order_by(GContract.name)
        site_g_eras = (
            g.sess.query(SiteGEra)
            .join(Site)
            .filter(SiteGEra.g_era == g_era)
            .order_by(Site.code)
            .all()
        )
        g_units = g.sess.query(GUnit).order_by(GUnit.code).all()
        g_reading_frequencies = (
            g.sess.query(GReadingFrequency).order_by(GReadingFrequency.code).all()
        )
        return make_response(
            render_template(
                "era_edit.html",
                g_era=g_era,
                supplier_g_contracts=supplier_g_contracts,
                site_g_eras=site_g_eras,
                g_units=g_units,
                g_reading_frequencies=g_reading_frequencies,
            ),
            400,
        )


@gas.route("/bills/<int:g_bill_id>/edit")
def bill_edit_get(g_bill_id):
    g_bill = GBill.get_by_id(g.sess, g_bill_id)
    bill_types = g.sess.query(BillType).order_by(BillType.code).all()
    return render_template("bill_edit.html", g_bill=g_bill, bill_types=bill_types)


@gas.route("/bills/<int:g_bill_id>/edit", methods=["POST"])
def bill_edit_post(g_bill_id):
    try:
        g_bill = GBill.get_by_id(g.sess, g_bill_id)
        if "delete" in request.values:
            g_batch = g_bill.g_batch
            g_bill.delete(g.sess)
            g.sess.commit()
            return chellow_redirect(f"/batches/{g_batch.id}", 303)

        else:
            account = req_str("account")
            reference = req_str("reference")
            issue_date = req_date("issue")
            start_date = req_date("start")
            finish_date = req_date("finish")
            kwh = req_decimal("kwh")
            net_gbp = req_decimal("net_gbp")
            vat_gbp = req_decimal("vat_gbp")
            gross_gbp = req_decimal("gross_gbp")
            type_id = req_int("bill_type_id")
            raw_lines = req_str("raw_lines")
            breakdown = req_zish("breakdown")
            bill_type = BillType.get_by_id(g.sess, type_id)

            g_bill.update(
                bill_type,
                reference,
                account,
                issue_date,
                start_date,
                finish_date,
                kwh,
                net_gbp,
                vat_gbp,
                gross_gbp,
                raw_lines,
                breakdown,
            )
            g.sess.commit()
            return chellow_redirect(f"/bills/{g_bill.id}", 303)

    except BadRequest as e:
        flash(e.description)
        g_bill = GBill.get_by_id(g.sess, g_bill_id)
        bill_types = g.sess.query(BillType).order_by(BillType.code).all()
        return make_response(
            render_template("bill_edit.html", g_bill=g_bill, bill_types=bill_types),
            400,
        )


@gas.route("/bills/<int:g_bill_id>/add_read")
def read_add_get(g_bill_id):
    g_read_types = g.sess.query(GReadType).order_by(GReadType.code)
    g_bill = GBill.get_by_id(g.sess, g_bill_id)
    g_units = g.sess.query(GUnit).order_by(GUnit.code)
    return render_template(
        "read_add.html", g_bill=g_bill, g_read_types=g_read_types, g_units=g_units
    )


@gas.route("/bills/<int:g_bill_id>/add_read", methods=["POST"])
def g_read_add_post(g_bill_id):
    try:
        g_bill = GBill.get_by_id(g.sess, g_bill_id)
        msn = req_str("msn")
        g_unit_id = req_int("g_unit_id")
        g_unit = GUnit.get_by_id(g.sess, g_unit_id)
        correction_factor = req_decimal("correction_factor")
        calorific_value = req_decimal("calorific_value")
        prev_date = req_date("prev_date")
        prev_value = req_decimal("prev_value")
        prev_type_id = req_int("prev_type_id")
        prev_type = GReadType.get_by_id(g.sess, prev_type_id)
        pres_date = req_date("pres_date")
        pres_value = req_decimal("pres_value")
        pres_type_id = req_int("pres_type_id")
        pres_type = GReadType.get_by_id(g.sess, pres_type_id)

        g_bill.insert_g_read(
            g.sess,
            msn,
            g_unit,
            correction_factor,
            calorific_value,
            prev_value,
            prev_date,
            prev_type,
            pres_value,
            pres_date,
            pres_type,
        )
        g.sess.commit()
        return chellow_redirect(f"/bills/{g_bill.id}", 303)
    except BadRequest as e:
        flash(e.description)
        g_read_types = g.sess.query(GReadType).order_by(GReadType.code)
        return render_template(
            "read_add.html", g_bill=g_bill, g_read_types=g_read_types
        )


@gas.route("/reads/<int:g_read_id>/edit")
def read_edit_get(g_read_id):
    g_read_types = g.sess.query(GReadType).order_by(GReadType.code).all()
    g_read = GRegisterRead.get_by_id(g.sess, g_read_id)
    g_units = g.sess.query(GUnit).order_by(GUnit.code)
    return render_template(
        "read_edit.html", g_read=g_read, g_read_types=g_read_types, g_units=g_units
    )


@gas.route("/reads/<int:g_read_id>/edit", methods=["POST"])
def read_edit_post(g_read_id):
    try:
        g_read = GRegisterRead.get_by_id(g.sess, g_read_id)
        if "update" in request.values:
            msn = req_str("msn")
            prev_date = req_date("prev_date")
            prev_value = req_decimal("prev_value")
            prev_type_id = req_int("prev_type_id")
            prev_type = GReadType.get_by_id(g.sess, prev_type_id)
            pres_date = req_date("pres_date")
            pres_value = req_decimal("pres_value")
            pres_type_id = req_int("pres_type_id")
            pres_type = GReadType.get_by_id(g.sess, pres_type_id)
            g_unit_id = req_int("g_unit_id")
            g_unit = GUnit.get_by_id(g.sess, g_unit_id)
            correction_factor = req_decimal("correction_factor")
            calorific_value = req_decimal("calorific_value")

            g_read.update(
                msn,
                g_unit,
                correction_factor,
                calorific_value,
                prev_value,
                prev_date,
                prev_type,
                pres_value,
                pres_date,
                pres_type,
            )

            g.sess.commit()
            return chellow_redirect(f"/bills/{g_read.g_bill.id}", 303)

        elif "delete" in request.values:
            g_bill = g_read.g_bill
            g_read.delete(g.sess)
            g.sess.commit()
            return chellow_redirect(f"/bills/{g_bill.id}", 303)

    except BadRequest as e:
        flash(e.description)
        g_read_types = g.sess.query(GReadType).order_by(GReadType.code).all()
        g_units = g.sess.query(GUnit).order_by(GUnit.code)
        return make_response(
            render_template(
                "read_edit.html",
                g_read=g_read,
                g_read_types=g_read_types,
                g_units=g_units,
            ),
            400,
        )


@gas.route("/units")
def units_get():
    g_units = g.sess.query(GUnit).order_by(GUnit.code)
    return render_template("units.html", g_units=g_units)


@gas.route("/units/<int:g_unit_id>")
def unit_get(g_unit_id):
    g_unit = GUnit.get_by_id(g.sess, g_unit_id)
    return render_template("unit.html", g_unit=g_unit)


@gas.route("/read_types/<int:g_read_type_id>")
def read_type_get(g_read_type_id):
    g_read_type = GReadType.get_by_id(g.sess, g_read_type_id)
    return render_template("read_type.html", g_read_type=g_read_type)


@gas.route("/read_types")
def read_types_get():
    g_read_types = g.sess.query(GReadType).order_by(GReadType.code)
    return render_template("read_types.html", g_read_types=g_read_types)


@gas.route("/reports")
def reports_get():
    now = utc_datetime_now()
    now_day = utc_datetime(now.year, now.month, now.day)
    month_start = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = Datetime(now.year, now.month, 1) - HH
    return render_template(
        "reports.html",
        month_start=month_start,
        month_finish=month_finish,
        now_day=now_day,
    )


@gas.route("/dns")
def dns_get():
    g_dns = g.sess.query(GDn).order_by(GDn.code)
    return render_template("dns.html", g_dns=g_dns)


@gas.route("/dns/<int:g_dn_id>")
def dn_get(g_dn_id):
    g_dn = GDn.get_by_id(g.sess, g_dn_id)
    g_ldzs = g.sess.query(GLdz).filter(GLdz.g_dn == g_dn).order_by(GLdz.code).all()
    return render_template("dn.html", g_dn=g_dn, g_ldzs=g_ldzs)


@gas.route("/industry_contracts")
def industry_contracts_get():
    contracts = g.sess.execute(
        select(GContract)
        .where(GContract.is_industry == true())
        .order_by(GContract.name)
    ).scalars()
    return render_template("industry_contracts.html", contracts=contracts)


@gas.route("/industry_contracts/<int:contract_id>")
def industry_contract_get(contract_id):
    contract = GContract.get_industry_by_id(g.sess, contract_id)
    rate_scripts = g.sess.execute(
        select(GRateScript)
        .where(GRateScript.g_contract == contract)
        .order_by(GRateScript.start_date.desc())
    ).scalars()

    try:
        import_module(f"chellow.gas.{contract.name}").get_importer()
        has_auto_importer = True
    except AttributeError:
        has_auto_importer = False
    except ImportError:
        has_auto_importer = False

    return render_template(
        "industry_contract.html",
        contract=contract,
        rate_scripts=rate_scripts,
        has_auto_importer=has_auto_importer,
    )


@gas.route("/industry_contracts/add")
def industry_contract_add_get():
    contracts = g.sess.execute(
        select(GContract)
        .where(GContract.is_industry == true())
        .order_by(GContract.name)
    )
    return render_template("industry_contract_add.html", contracts=contracts)


@gas.route("/industry_contracts/add", methods=["POST"])
def industry_contract_add_post():
    try:
        name = req_str("name")
        start_date = req_date("start")
        charge_script = req_str("charge_script")
        properties = req_zish("properties")

        contract = GContract.insert(
            g.sess, True, name, charge_script, properties, start_date, None, {}
        )
        g.sess.commit()
        return chellow_redirect(f"/industry_contracts/{contract.id}", 303)

    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        contracts = g.sess.query(GContract).order_by(GContract.name)
        return make_response(
            render_template("industry_contract_add.html", contracts=contracts), 400
        )


@gas.route("/industry_contracts/<int:g_contract_id>/edit")
def industry_contract_edit_get(g_contract_id):
    g_contract = GContract.get_industry_by_id(g.sess, g_contract_id)
    return render_template("industry_contract_edit.html", g_contract=g_contract)


@gas.route("/industry_contracts/<int:g_contract_id>/edit", methods=["DELETE"])
def industry_contract_edit_delete(g_contract_id):
    try:
        g_contract = GContract.get_industry_by_id(g.sess, g_contract_id)
        g_contract.delete(g.sess)
        g.sess.commit()
        return hx_redirect("/industry_contracts")
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return make_response(
            render_template("industry_contract_edit.html", g_contract=g_contract), 400
        )


@gas.route("/industry_contracts/<int:g_contract_id>/edit", methods=["PATCH"])
def industry_contract_edit_patch(g_contract_id):
    try:
        g_contract = GContract.get_industry_by_id(g.sess, g_contract_id)
        if "state" in request.values:
            state = req_zish("state")
            g_contract.update_state(state)
        else:
            name = req_str("name")
            charge_script = req_str("charge_script")
            properties = req_zish("properties")
            g_contract.update(name, charge_script, properties)

        g.sess.commit()
        return hx_redirect(f"/industry_contracts/{g_contract.id}", 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return make_response(
            render_template("industry_contract_edit.html", g_contract=g_contract), 400
        )


@gas.route("/industry_contracts/<int:contract_id>/auto_importer")
def industry_auto_importer_get(contract_id):
    contract = GContract.get_industry_by_id(g.sess, contract_id)
    importer = import_module(f"chellow.gas.{contract.name}").get_importer()
    return render_template(
        "industry_auto_importer.html", importer=importer, contract=contract
    )


@gas.route("/industry_contracts/<int:contract_id>/auto_importer", methods=["POST"])
def industry_auto_importer_post(contract_id):
    try:
        contract = GContract.get_industry_by_id(g.sess, contract_id)
        importer = import_module(f"chellow.gas.{contract.name}").get_importer()
        importer.go()
        return chellow_redirect(f"/industry_contracts/{contract.id}/auto_importer", 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template(
                "industry_auto_importer.html", importer=importer, contract=contract
            ),
            400,
        )


@gas.route("/industry_contracts/<int:g_contract_id>/add_rate_script")
def industry_rate_script_add_get(g_contract_id):
    now = utc_datetime_now()
    initial_date = utc_datetime(now.year, now.month)
    g_contract = GContract.get_industry_by_id(g.sess, g_contract_id)
    return render_template(
        "industry_rate_script_add.html",
        g_contract=g_contract,
        initial_date=initial_date,
    )


@gas.route("/industry_contracts/<int:g_contract_id>/add_rate_script", methods=["POST"])
def industry_rate_script_add_post(g_contract_id):
    try:
        g_contract = GContract.get_by_id(g.sess, g_contract_id)
        start_date = req_date("start")
        g_rate_script = g_contract.insert_g_rate_script(g.sess, start_date, {})
        g.sess.commit()
        return chellow_redirect(f"/industry_rate_scripts/{g_rate_script.id}", 303)
    except BadRequest as e:
        flash(e.description)
        now = utc_datetime_now()
        initial_date = utc_datetime(now.year, now.month)
        return make_response(
            render_template(
                "industry_rate_script_add.html",
                g_contract=g_contract,
                initial_date=initial_date,
            ),
            400,
        )


@gas.route("/industry_rate_scripts/<int:g_rate_script_id>/edit")
def industry_rate_script_edit_get(g_rate_script_id):
    g_rate_script = GRateScript.get_by_id(g.sess, g_rate_script_id)
    return render_template(
        "industry_rate_script_edit.html", g_rate_script=g_rate_script
    )


@gas.route("/industry_rate_scripts/<int:g_rate_script_id>/edit", methods=["POST"])
def industry_rate_script_edit_post(g_rate_script_id):
    try:
        g_rate_script = GRateScript.get_by_id(g.sess, g_rate_script_id)
        g_contract = g_rate_script.g_contract
        if "delete" in request.values:
            g_contract.delete_g_rate_script(g.sess, g_rate_script)
            g.sess.commit()
            return chellow_redirect(f"/industry_contracts/{g_contract.id}", 303)
        elif "import" in request.form:
            file_item = req_file("dn_file")

            rates = chellow.gas.dn_rate_parser.find_rates(
                file_item.filename, BytesIO(file_item.read())
            )
            g_contract.update_g_rate_script(
                g.sess,
                g_rate_script,
                g_rate_script.start_date,
                g_rate_script.finish_date,
                rates,
            )
            g.sess.commit()
            return chellow_redirect(f"/industry_rate_scripts/{g_rate_script.id}", 303)
        else:
            script = req_zish("script")
            start_date = req_date("start")
            has_finished = req_checkbox("has_finished")
            finish_date = req_date("finish") if has_finished else None
            g_contract.update_g_rate_script(
                g.sess, g_rate_script, start_date, finish_date, script
            )
            g.sess.commit()
            return chellow_redirect(f"/industry_rate_scripts/{g_rate_script.id}", 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return make_response(
            render_template(
                "industry_rate_script_edit.html", g_rate_script=g_rate_script
            ),
            400,
        )


@gas.route("/industry_rate_scripts/<int:g_rate_script_id>")
def industry_rate_script_get(g_rate_script_id):
    g_rate_script = GRateScript.get_by_id(g.sess, g_rate_script_id)
    g_contract = g_rate_script.g_contract
    next_g_rate_script = (
        g.sess.execute(
            select(GRateScript)
            .where(
                GRateScript.g_contract == g_contract,
                GRateScript.start_date > g_rate_script.start_date,
            )
            .order_by(GRateScript.start_date)
        )
        .scalars()
        .first()
    )
    previous_g_rate_script = (
        g.sess.execute(
            select(GRateScript)
            .where(
                GRateScript.g_contract == g_contract,
                GRateScript.start_date < g_rate_script.start_date,
            )
            .order_by(GRateScript.start_date.desc())
        )
        .scalars()
        .first()
    )
    return render_template(
        "industry_rate_script.html",
        g_rate_script=g_rate_script,
        previous_g_rate_script=previous_g_rate_script,
        next_g_rate_script=next_g_rate_script,
    )


@gas.route("/ldzs/<int:g_ldz_id>")
def ldz_get(g_ldz_id):
    g_ldz = GLdz.get_by_id(g.sess, g_ldz_id)
    g_exit_zones = (
        g.sess.query(GExitZone)
        .filter(GExitZone.g_ldz == g_ldz)
        .order_by(GExitZone.code)
        .all()
    )
    return render_template("ldz.html", g_ldz=g_ldz, g_exit_zones=g_exit_zones)


@gas.route("/reading_frequencies/<int:g_reading_frequency_id>")
def reading_frequency_get(g_reading_frequency_id):
    g_reading_frequency = GReadingFrequency.get_by_id(g.sess, g_reading_frequency_id)
    return render_template(
        "reading_frequency.html", g_reading_frequency=g_reading_frequency
    )


@gas.route("/reading_frequencies")
def reading_frequencies_get():
    g_reading_frequencies = g.sess.query(GReadingFrequency).order_by(
        GReadingFrequency.code
    )
    return render_template(
        "reading_frequencies.html", g_reading_frequencies=g_reading_frequencies
    )


@gas.route("/exit_zones/<int:g_exit_zone_id>")
def exit_zone_get(g_exit_zone_id):
    g_exit_zone = GExitZone.get_by_id(g.sess, g_exit_zone_id)
    return render_template("exit_zone.html", g_exit_zone=g_exit_zone)


@gas.route("/batches/<int:g_batch_id>/csv")
def batch_csv_get(g_batch_id):
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)
    rows = []
    max_reads = 0
    for g_bill in g.sess.scalars(
        select(GBill)
        .where(GBill.g_batch == g_batch)
        .order_by(GBill.reference, GBill.start_date)
        .options(
            joinedload(GBill.bill_type),
            joinedload(GBill.g_reads).joinedload(GRegisterRead.g_unit),
            joinedload(GBill.g_reads).joinedload(GRegisterRead.pres_type),
            joinedload(GBill.g_reads).joinedload(GRegisterRead.prev_type),
        )
    ).unique():
        row = [
            g_batch.g_contract.name,
            g_batch.reference,
            g_bill.reference,
            g_bill.account,
            g_bill.issue_date,
            g_bill.start_date,
            g_bill.finish_date,
            g_bill.kwh,
            g_bill.net,
            g_bill.vat,
            g_bill.gross,
            g_bill.bill_type.code,
            g_bill.breakdown,
        ]
        g_reads = g_bill.g_reads
        max_reads = max(max_reads, len(g_reads))
        for g_read in g_reads:
            row.extend(
                [
                    g_read.msn,
                    g_read.g_unit.code,
                    g_read.correction_factor,
                    g_read.calorific_value,
                    g_read.prev_date,
                    g_read.prev_value,
                    g_read.prev_type.code,
                    g_read.pres_date,
                    g_read.pres_value,
                    g_read.pres_type.code,
                ]
            )
        rows.append(row)

    si = StringIO()
    cw = csv.writer(si)
    read_titles = [
        "msn",
        "unit",
        "correction_factor",
        "calorific_value",
        "prev_date",
        "prev_value",
        "prev_type",
        "pres_date",
        "pres_value",
        "pres_type",
    ]
    titles = [
        "Contract",
        "Batch Reference",
        "Bill Reference",
        "Account",
        "Issued",
        "From",
        "To",
        "kWh",
        "Net",
        "VAT",
        "Gross",
        "Type",
        "breakdown",
    ]
    for i in range(max_reads):
        for rt in read_titles:
            titles.append(f"{i}_{rt}")
    cw.writerow(titles)
    for row in rows:
        cw.writerow(csv_make_val(v) for v in row)
    disp = f'attachment; filename="g_batch_{g_batch.id}.csv"'
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = disp
    output.headers["Content-type"] = "text/csv"
    return output


@gas.route("/supplier_contracts")
def supplier_contracts_get():
    GRateScriptAliasFinish = aliased(GRateScript)

    current_contracts = g.sess.scalars(
        select(GContract)
        .join(
            GRateScriptAliasFinish,
            GContract.finish_g_rate_script_id == GRateScriptAliasFinish.id,
        )
        .where(
            GContract.is_industry == false(),
            GRateScriptAliasFinish.finish_date == null(),
        )
        .order_by(GContract.name)
    )
    ended_contracts = g.sess.scalars(
        select(GContract)
        .join(
            GRateScriptAliasFinish,
            GContract.finish_g_rate_script_id == GRateScriptAliasFinish.id,
        )
        .where(
            GContract.is_industry == false(),
            GRateScriptAliasFinish.finish_date != null(),
        )
        .order_by(GContract.name)
    )

    return render_template(
        "supplier_contracts.html",
        current_contracts=current_contracts,
        ended_contracts=ended_contracts,
    )


@gas.route("/supplier_contracts/<int:contract_id>")
def supplier_contract_get(contract_id):
    contract = GContract.get_supplier_by_id(g.sess, contract_id)
    rate_scripts = g.sess.execute(
        select(GRateScript)
        .where(GRateScript.g_contract == contract)
        .order_by(GRateScript.start_date.desc())
    ).scalars()

    now = Datetime.utcnow() - relativedelta(months=1)
    month_start = Datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH

    return render_template(
        "supplier_contract.html",
        contract=contract,
        month_start=month_start,
        month_finish=month_finish,
        rate_scripts=rate_scripts,
    )


@gas.route("/supplier_contracts/add")
def supplier_contract_add_get():
    contracts = g.sess.execute(
        select(GContract)
        .where(GContract.is_industry == false())
        .order_by(GContract.name)
    )
    return render_template("supplier_contract_add.html", contracts=contracts)


@gas.route("/supplier_contracts/add", methods=["POST"])
def supplier_contract_add_post():
    try:
        name = req_str("name")
        start_date = req_date("start")
        charge_script = req_str("charge_script")
        properties = req_zish("properties")

        contract = GContract.insert_supplier(
            g.sess, name, charge_script, properties, start_date, None, {}
        )
        g.sess.commit()
        return chellow_redirect(f"/supplier_contracts/{contract.id}", 303)

    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        contracts = g.sess.query(GContract).order_by(GContract.name)
        return make_response(
            render_template("supplier_contract_add.html", contracts=contracts), 400
        )


@gas.route("/supplier_contracts/<int:g_contract_id>/edit")
def supplier_contract_edit_get(g_contract_id):
    g_contract = GContract.get_supplier_by_id(g.sess, g_contract_id)
    return render_template("supplier_contract_edit.html", g_contract=g_contract)


@gas.route("/supplier_contracts/<int:g_contract_id>/edit", methods=["POST"])
def supplier_contract_edit_post(g_contract_id):
    try:
        g_contract = GContract.get_by_id(g.sess, g_contract_id)
        name = req_str("name")
        charge_script = req_str("charge_script")
        properties = req_zish("properties")
        g_contract.update(name, charge_script, properties)
        g.sess.commit()
        return chellow_redirect(f"/supplier_contracts/{g_contract.id}", 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return make_response(
            render_template("supplier_contract_edit.html", g_contract=g_contract), 400
        )


@gas.route("/supplier_contracts/<int:g_contract_id>/edit", methods=["DELETE"])
def supplier_contract_edit_delete(g_contract_id):
    try:
        g_contract = GContract.get_by_id(g.sess, g_contract_id)
        g_contract.delete(g.sess)
        g.sess.commit()
        return hx_redirect("/supplier_contracts", 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return make_response(
            render_template("supplier_contract_edit.html", g_contract=g_contract), 400
        )


@gas.route("/supplier_contracts/<int:g_contract_id>/add_rate_script")
def supplier_rate_script_add_get(g_contract_id):
    now = utc_datetime_now()
    initial_date = utc_datetime(now.year, now.month)
    g_contract = GContract.get_by_id(g.sess, g_contract_id)
    return render_template(
        "supplier_rate_script_add.html",
        g_contract=g_contract,
        initial_date=initial_date,
    )


@gas.route("/supplier_contracts/<int:g_contract_id>/add_rate_script", methods=["POST"])
def supplier_rate_script_add_post(g_contract_id):
    try:
        g_contract = GContract.get_by_id(g.sess, g_contract_id)
        start_date = req_date("start")
        g_rate_script = g_contract.insert_g_rate_script(g.sess, start_date, {})
        g.sess.commit()
        return chellow_redirect(f"/supplier_rate_scripts/{g_rate_script.id}", 303)
    except BadRequest as e:
        flash(e.description)
        now = utc_datetime_now()
        initial_date = utc_datetime(now.year, now.month)
        return make_response(
            render_template(
                "supplier_rate_script_add.html",
                g_contract=g_contract,
                initial_date=initial_date,
            ),
            400,
        )


@gas.route("/supplier_rate_scripts/<int:g_rate_script_id>/edit")
def supplier_rate_script_edit_get(g_rate_script_id):
    g_rate_script = GRateScript.get_by_id(g.sess, g_rate_script_id)
    return render_template(
        "supplier_rate_script_edit.html", g_rate_script=g_rate_script
    )


@gas.route("/supplier_rate_scripts/<int:g_rate_script_id>/edit", methods=["POST"])
def supplier_rate_script_edit_post(g_rate_script_id):
    try:
        g_rate_script = GRateScript.get_by_id(g.sess, g_rate_script_id)
        g_contract = g_rate_script.g_contract
        if "delete" in request.values:
            g_contract.delete_g_rate_script(g.sess, g_rate_script)
            g.sess.commit()
            return chellow_redirect(f"/supplier_contracts/{g_contract.id}", 303)
        else:
            script = req_zish("script")
            start_date = req_date("start")
            has_finished = req_checkbox("has_finished")
            finish_date = req_date("finish") if has_finished else None
            g_contract.update_g_rate_script(
                g.sess, g_rate_script, start_date, finish_date, script
            )
            g.sess.commit()
            return chellow_redirect(f"/supplier_rate_scripts/{g_rate_script.id}", 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return make_response(
            render_template(
                "supplier_rate_script_edit.html", g_rate_script=g_rate_script
            ),
            400,
        )


@gas.route("/supplier_rate_scripts/<int:g_rate_script_id>")
def supplier_rate_script_get(g_rate_script_id):
    g_rate_script = GRateScript.get_by_id(g.sess, g_rate_script_id)
    g_contract = g_rate_script.g_contract
    next_g_rate_script = (
        g.sess.execute(
            select(GRateScript)
            .where(
                GRateScript.g_contract == g_contract,
                GRateScript.start_date > g_rate_script.start_date,
            )
            .order_by(GRateScript.start_date)
        )
        .scalars()
        .first()
    )
    previous_g_rate_script = (
        g.sess.execute(
            select(GRateScript)
            .where(
                GRateScript.g_contract == g_contract,
                GRateScript.start_date < g_rate_script.start_date,
            )
            .order_by(GRateScript.start_date.desc())
        )
        .scalars()
        .first()
    )
    return render_template(
        "supplier_rate_script.html",
        g_rate_script=g_rate_script,
        next_g_rate_script=next_g_rate_script,
        previous_g_rate_script=previous_g_rate_script,
    )
