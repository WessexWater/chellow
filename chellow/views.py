import csv
import gc
import importlib
import json
import math
import os
import platform
import sys
import traceback
import types
from collections import OrderedDict
from datetime import datetime as Datetime
from importlib import import_module
from io import DEFAULT_BUFFER_SIZE, StringIO
from itertools import chain, islice
from operator import itemgetter
from random import choice
from xml.dom import Node

from dateutil.relativedelta import relativedelta

from flask import (
    Blueprint,
    Response,
    current_app,
    flash,
    g,
    make_response,
    redirect,
    render_template,
    request,
)

import psutil

from pympler import muppy, summary

from sqlalchemy import (
    Float,
    cast,
    false,
    func,
    not_,
    null,
    or_,
    select,
    text,
    true,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy.orm.attributes import flag_modified

from werkzeug.exceptions import BadRequest

import chellow.bank_holidays
import chellow.dloads
import chellow.e.bill_importer
import chellow.e.bsuos
import chellow.e.computer
import chellow.e.hh_importer
import chellow.e.laf_import
import chellow.e.mdd_importer
import chellow.e.rcrc
import chellow.e.system_price
import chellow.e.tlms
import chellow.edi_lib
import chellow.general_import
import chellow.rate_server
from chellow.models import (
    BillType,
    Channel,
    Comm,
    Contract,
    Cop,
    EnergisationStatus,
    Era,
    GContract,
    GEra,
    GExitZone,
    GReadingFrequency,
    GUnit,
    GeneratorType,
    GspGroup,
    HhDatum,
    MarketRole,
    Participant,
    Party,
    Pc,
    RateScript,
    Report,
    ReportRun,
    ReportRunRow,
    Scenario,
    Site,
    SiteEra,
    SiteGEra,
    Snag,
    Source,
    Ssc,
    Supply,
    User,
    UserRole,
)
from chellow.utils import (
    HH,
    c_months_u,
    csv_make_val,
    ct_datetime_now,
    hh_range,
    parse_mpan_core,
    req_bool,
    req_date,
    req_decimal,
    req_hh_date,
    req_int,
    req_str,
    req_zish,
    send_response,
    to_ct,
    utc_datetime,
    utc_datetime_now,
)

home = Blueprint("", __name__, template_folder="templates")


def chellow_redirect(path, code=None):
    location = chellow.utils.url_root + path
    if code is None:
        return redirect(location)
    else:
        return redirect(location, code)


@home.route("/configuration", methods=["GET"])
def configuration():
    config = Contract.get_non_core_by_name(g.sess, "configuration")
    return chellow_redirect(f"/non_core_contracts/{config.id}")


@home.route("/health")
def health():
    return Response("healthy\n", mimetype="text/plain")


@home.route("/local_reports/<int:report_id>/output")
def local_report_output_get(report_id):
    report = g.sess.query(Report).get(report_id)
    try:
        ns = {"report_id": report_id, "template": report.template}
        exec(report.script, ns)
        return ns["do_get"]()
    except BaseException:
        return Response(traceback.format_exc(), status=500)


@home.route("/local_reports/<int:report_id>/output", methods=["GET", "POST"])
def local_report_output_post(report_id):
    report = g.sess.query(Report).get(report_id)
    try:
        ns = {"report_id": report_id, "template": report.template}
        exec(report.script, ns)
        return ns["do_post"]()
    except BaseException:
        return Response(traceback.format_exc(), status=500)


@home.route("/local_reports", methods=["GET"])
def local_reports_get():
    reports = g.sess.query(Report).order_by(Report.id, Report.name).all()
    return render_template("local_reports.html", reports=reports)


@home.route("/local_reports", methods=["POST"])
def local_reports_post():
    name = req_str("name")
    report = Report(name, "", "")
    g.sess.add(report)
    try:
        g.sess.commit()
    except IntegrityError as e:
        if "duplicate key value violates unique constraint" in str(e):
            return Response("There's already a report with that name.", status=400)
        else:
            raise
    return chellow_redirect(f"/local_reports/{report.id}", 303)


@home.route("/local_reports/<int:report_id>")
def local_report_get(report_id):
    report = Report.get_by_id(g.sess, report_id)
    return render_template("local_report.html", report=report)


@home.route("/local_reports/<int:report_id>", methods=["POST"])
def local_report_post(report_id):
    report = Report.get_by_id(g.sess, report_id)
    if "delete" in request.values:
        g.sess.delete(report)
        return chellow_redirect("/local_reports", 303)

    else:
        name = req_str("name")
        script = req_str("script")
        template = req_str("template")
        report.update(name, script, template)
        try:
            g.sess.commit()
        except BadRequest as e:
            if "duplicate key value violates unique constraint" in str(e):
                return Response("There's already a report with that name.", status=400)
            else:
                raise
        return chellow_redirect(f"/local_reports/{report.id}", 303)


@home.route("/system")
def system_get():
    traces = []
    for thread_id, stack in sys._current_frames().items():
        traces.append(f"\n# ThreadID: {thread_id}")
        for filename, lineno, name, line in traceback.extract_stack(stack):
            traces.append(f'File: "{filename}", line {lineno}, in {name}')
            if line:
                traces.append(f"  {line.strip()}")
    pg_stats = g.sess.execute("select * from pg_stat_activity").fetchall()

    pg_indexes = g.sess.execute(
        """
        select
            t.relname as table_name,
            i.relname as index_name,
            array_to_string(array_agg(a.attname), ', ') as column_names
        from
            pg_class t,
            pg_class i,
            pg_index ix,
            pg_attribute a
        where
            t.oid = ix.indrelid
            and i.oid = ix.indexrelid
            and a.attrelid = t.oid
            and a.attnum = ANY(ix.indkey)
            and t.relkind = 'r'
        group by
            t.relname,
            i.relname
        order by
            t.relname,
            i.relname;
        """
    ).fetchall()

    if hasattr(chellow, "versions"):
        version_number = chellow.versions["version"]
        version_hash = chellow.versions["full-revisionid"]
    else:
        version_number = None
        version_hash = None

    return render_template(
        "system.html",
        traces="\n".join(traces),
        version_number=version_number,
        version_hash=version_hash,
        pg_stats=pg_stats,
        request=request,
        virtual_memory=psutil.virtual_memory(),
        swap_memory=psutil.swap_memory(),
        python_version=platform.python_version(),
        pg_indexes=pg_indexes,
    )


def get_objects():
    return dict((id(obj), obj) for obj in gc.get_objects())


def obj_val(obj):
    if isinstance(obj, (int, float)):
        return repr(obj)
    elif isinstance(obj, str):
        return repr(obj[:100])
    elif isinstance(obj, list):
        ls = []
        for o in obj[:10]:
            if isinstance(o, (int, float)):
                desc = repr(o)
            elif isinstance(o, str):
                desc = repr(o[:100])
            elif isinstance(o, (list, dict)):
                desc = "length: " + str(len(o))
            else:
                desc = ""
            ls.append("(" + ", ".join([str(type(o)), desc]) + ")")
        return "length: " + str(len(obj)) + " [" + ", ".join(ls)
    elif isinstance(obj, tuple):
        ls = []
        for o in obj[:10]:
            if isinstance(o, (int, float)):
                desc = repr(o)
            elif isinstance(o, str):
                desc = repr(o[:100])
            elif isinstance(o, (list, dict)):
                desc = "length: " + str(len(o))
            else:
                desc = ""
            ls.append("(" + ", ".join([str(type(o)), desc]) + ")")
        return "length: " + str(len(obj)) + " (" + ", ".join(ls)
    elif isinstance(obj, dict):
        ls = []
        for k, v in islice(obj.items(), 10):
            if isinstance(v, (int, float)):
                desc = repr(v)
            elif isinstance(v, str):
                desc = repr(v[:100])
            elif isinstance(v, (list, dict)):
                desc = "length: " + str(len(v))
            else:
                desc = str(type(v))
            ls.append(str(k) + ": " + desc)
        return "length: " + str(len(obj)) + " {" + ", ".join(ls)
    elif isinstance(obj, types.CodeType):
        return obj.co_filename
    elif isinstance(obj, types.FunctionType):
        return obj.__name__
    elif isinstance(obj, types.FrameType):
        return obj.f_code.co_filename + " " + str(obj.f_lineno)
    elif isinstance(obj, types.MethodType):
        return obj.__name__
    elif isinstance(obj, types.ModuleType):
        return obj.__name__
    elif isinstance(obj, Node):
        parent_node = obj.parentNode
        if parent_node is None:
            id_str = "None"
        else:
            id_str = str(id(parent_node))
        return "parent: " + id_str
    else:
        return ""


def get_path(node):
    path = [node]
    parent = node["parent"]
    while parent is not None:
        path.append(parent)
        parent = parent["parent"]
    return path


def add_obj(objects, path, leaves):
    if len(leaves) > 10:
        return

    added = False
    path_ids = set(id(o) for o in path)
    for ref in gc.get_referrers(path[-1]):
        ref_id = id(ref)
        if ref_id not in path_ids and ref_id in objects:
            add_obj(objects, path + [ref], leaves)
            added = True
    if not added:
        leaves.append(path)


@home.route("/system/chains")
def chains_get():
    unreachable = gc.collect()
    objects = get_objects()
    obj = choice(tuple(objects.values()))
    leaves = []
    root_path = [obj]
    add_obj(objects, root_path, leaves)
    paths = []
    for leaf in leaves:
        path_tuples = [(id(o), type(o), obj_val(o)) for o in leaf]
        paths.append(path_tuples)
    return render_template("chain.html", paths=paths, unreachable=unreachable)


@home.route("/system/object_summary")
def object_summary_get():
    sumry = summary.summarize(muppy.get_objects())
    sumry_text = "\n".join(summary.format_(sumry, sort="size", order="descending"))
    return render_template("object_summary.html", summary=sumry_text)


@home.route("/")
def home_get():
    config = Contract.get_non_core_by_name(g.sess, "configuration")
    now = utc_datetime_now()
    month_start = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = Datetime(now.year, now.month, 1) - HH

    return render_template(
        "home.html",
        properties=config.make_properties(),
        month_start=month_start,
        month_finish=month_finish,
    )


@home.route("/local_reports_home")
def local_reports_home():
    config = Contract.get_non_core_by_name(g.sess, "configuration")
    properties = config.make_properties()
    report_id = properties["local_reports_id"]
    return local_report_output_get(report_id)


@home.errorhandler(500)
def error_500(error):
    return traceback.format_exc(), 500


@home.errorhandler(RuntimeError)
def error_runtime(error):
    return "called rtime handler " + str(error), 500


@home.route("/bill_types")
def bill_types_get():
    bill_types = g.sess.query(BillType).order_by(BillType.code)
    return render_template("bill_types.html", bill_types=bill_types)


@home.route("/users", methods=["GET"])
def users_get():
    users = g.sess.query(User).order_by(User.email_address).all()
    parties = (
        g.sess.query(Party)
        .join(MarketRole)
        .join(Participant)
        .order_by(MarketRole.code, Participant.code)
        .all()
    )

    config_contract = Contract.get_non_core_by_name(g.sess, "configuration")
    props = config_contract.make_properties()
    ad_props = props.get("ad_authentication", {})
    ad_auth_on = ad_props.get("on", False)
    return render_template(
        "users.html", users=users, parties=parties, ad_auth_on=ad_auth_on
    )


@home.route("/users", methods=["POST"])
def users_post():
    email_address = req_str("email_address")

    config_contract = Contract.get_non_core_by_name(g.sess, "configuration")
    props = config_contract.make_properties()
    ad_props = props.get("ad_authentication", {})
    ad_auth_on = ad_props.get("on", False)

    if ad_auth_on:
        password = ""
    else:
        password = req_str("password")
    user_role_code = req_str("user_role_code")
    role = UserRole.get_by_code(g.sess, user_role_code)
    try:
        party = None
        if role.code == "party-viewer":
            party_id = req_int("party_id")
            party = g.sess.query(Party).get(party_id)
        user = User.insert(g.sess, email_address, password, role, party)
        g.sess.commit()
        return chellow_redirect("/users/" + str(user.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        users = g.sess.query(User).order_by(User.email_address).all()
        parties = (
            g.sess.query(Party)
            .join(MarketRole)
            .join(Participant)
            .order_by(MarketRole.code, Participant.code)
            .all()
        )
        return make_response(
            render_template(
                "users.html", users=users, parties=parties, ad_auth_on=ad_auth_on
            ),
            400,
        )


@home.route("/users/<int:user_id>", methods=["POST"])
def user_post(user_id):
    try:
        user = User.get_by_id(g.sess, user_id)
        if "current_password" in request.values:
            current_password = req_str("current_password")
            new_password = req_str("new_password")
            confirm_new_password = req_str("confirm_new_password")
            if not user.password_matches(current_password):
                raise BadRequest("The current password is incorrect.")
            if new_password != confirm_new_password:
                raise BadRequest("The new passwords aren't the same.")
            if len(new_password) < 6:
                raise BadRequest("The password must be at least 6 characters long.")
            user.set_password(new_password)
            g.sess.commit()
            return chellow_redirect("/users/" + str(user.id), 303)
        elif "delete" in request.values:
            g.sess.delete(user)
            g.sess.commit()
            return chellow_redirect("/users", 303)
        else:
            email_address = req_str("email_address")
            user_role_code = req_str("user_role_code")
            user_role = UserRole.get_by_code(g.sess, user_role_code)
            party = None
            if user_role.code == "party-viewer":
                party_id = req_int("party_id")
                party = Party.get_by_id(g.sess, party_id)
            user.update(email_address, user_role, party)
            g.sess.commit()
            return chellow_redirect("/users/" + str(user.id), 303)
    except BadRequest as e:
        flash(e.description)
        parties = (
            g.sess.query(Party)
            .join(MarketRole)
            .join(Participant)
            .order_by(MarketRole.code, Participant.code)
        )
        config_contract = Contract.get_non_core_by_name(g.sess, "configuration")
        props = config_contract.make_properties()
        ad_props = props.get("ad_authentication", {})
        ad_auth_on = ad_props.get("on", False)
        return make_response(
            render_template(
                "user.html", parties=parties, user=user, ad_auth_on=ad_auth_on
            ),
            400,
        )


@home.route("/users/<int:user_id>")
def user_get(user_id):
    parties = (
        g.sess.query(Party)
        .join(MarketRole)
        .join(Participant)
        .order_by(MarketRole.code, Participant.code)
    )
    user = User.get_by_id(g.sess, user_id)
    config_contract = Contract.get_non_core_by_name(g.sess, "configuration")
    props = config_contract.make_properties()
    ad_props = props.get("ad_authentication", {})
    ad_auth_on = ad_props.get("on", False)
    return render_template(
        "user.html", parties=parties, user=user, ad_auth_on=ad_auth_on
    )


@home.route("/general_imports")
def general_imports_get():
    return render_template(
        "general_imports.html",
        process_ids=sorted(chellow.general_import.get_process_ids(), reverse=True),
    )


@home.route("/general_imports", methods=["POST"])
def general_imports_post():
    try:
        file_item = request.files["import_file"]
        file_name = file_item.filename
        if not file_name.endswith(".csv"):
            raise BadRequest("The file name should have the extension '.csv'.")
        f = StringIO(
            str(file_item.stream.read(), encoding="utf-8-sig", errors="ignore")
        )
        f.seek(0)
        proc_id = chellow.general_import.start_process(f)
        return chellow_redirect("/general_imports/" + str(proc_id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template(
            "general_imports.html",
            process_ids=sorted(chellow.general_import.get_process_ids(), reverse=True),
        )


@home.route("/general_imports/<int:import_id>")
def general_import_get(import_id):
    try:
        proc = chellow.general_import.get_process(import_id)
        fields = proc.get_fields()
        fields["is_alive"] = proc.is_alive()
        fields["process_id"] = import_id
        return render_template("general_import.html", **fields)
    except BadRequest as e:
        flash(e.description)
        return render_template("general_import.html", process_id=import_id)


@home.route("/edi_viewer")
def edi_viewer_get():
    return render_template("edi_viewer.html")


@home.route("/edi_viewer", methods=["POST"])
def edi_viewer_post():
    segments = []
    try:
        file_item = request.files["edi_file"]
        file_name = file_item.filename
        f = StringIO(
            str(file_item.stream.read(), encoding="utf-8-sig", errors="ignore")
        )
        f.seek(0)
        parser = chellow.edi_lib.EdiParser(f)
        for segment_name in parser:
            elements = parser.elements

            if segment_name == "CCD":
                segment_name = segment_name + elements[1][0]
                try:
                    seg = chellow.edi_lib.SEGMENTS[segment_name]
                except KeyError:
                    raise BadRequest(
                        "The segment name " + segment_name + " is not recognized."
                    )
            else:
                try:
                    seg = chellow.edi_lib.SEGMENTS[segment_name]
                except KeyError:
                    raise BadRequest(
                        "The segment name " + segment_name + " is not recognized."
                    )

            titles_element = []
            titles_component = []
            values = []
            elems = seg["elements"]
            if len(elements) > len(elems):
                raise BadRequest(
                    "There are more elements than recognized for the "
                    "segment " + segment_name + "."
                )
            for element, elem in zip(elements, elems):
                comps = elem["components"]
                colspan = len(comps)
                titles_element.append(
                    {
                        "value": elem["description"],
                        "colspan": str(colspan),
                        "rowspan": "2" if colspan == 1 else "1",
                    }
                )
                if len(element) > len(comps):
                    raise BadRequest(
                        "There are more components than recognized for the "
                        "segment " + segment_name + " and element " + str(element) + "."
                    )

                for i, (title, typ) in enumerate(comps):
                    if colspan > 1:
                        titles_component.append(title)
                    try:
                        component = element[i]

                        if typ == "X":
                            value = component
                        elif typ == "date":
                            d = component
                            if len(d) > 0:
                                value = "-".join((d[:2], d[2:4], d[4:]))
                            else:
                                value = d
                        elif typ == "time":
                            t = component
                            if len(t) > 0:
                                value = ":".join((t[:2], t[2:4], t[4:]))
                            else:
                                value = t
                        else:
                            raise BadRequest("Didn't recognize the type " + typ + ".")
                    except IndexError:
                        value = ""

                    values.append(value)

            segments.append(
                {
                    "name": segment_name,
                    "description": seg["description"],
                    "titles_element": titles_element,
                    "titles_component": titles_component,
                    "vals": values,
                    "raw_line": parser.line,
                }
            )

        return render_template(
            "edi_viewer.html", segments=segments, file_name=file_name
        )
    except BadRequest as e:
        flash(e.description)
        return render_template(
            "edi_viewer.html", segments=segments, file_name=file_name
        )


@home.route("/sites/<int:site_id>/edit")
def site_edit_get(site_id):
    try:
        site = Site.get_by_id(g.sess, site_id)
        sources = g.sess.query(Source).order_by(Source.code)
        generator_types = g.sess.query(GeneratorType).order_by(GeneratorType.code)
        gsp_groups = g.sess.query(GspGroup).order_by(GspGroup.code)
        eras = (
            g.sess.query(Era)
            .join(SiteEra)
            .filter(SiteEra.site == site)
            .order_by(Era.start_date.desc())
        )
        mop_contracts = (
            g.sess.query(Contract)
            .join(MarketRole)
            .filter(MarketRole.code == "M")
            .order_by(Contract.name)
        )
        dc_contracts = (
            g.sess.query(Contract)
            .join(MarketRole)
            .filter(MarketRole.code.in_(("C", "D")))
            .order_by(Contract.name)
        )
        supplier_contracts = (
            g.sess.query(Contract)
            .join(MarketRole)
            .filter(MarketRole.code == "X")
            .order_by(Contract.name)
        )
        pcs = g.sess.query(Pc).order_by(Pc.code)
        cops = g.sess.query(Cop).order_by(Cop.code)
        comms = g.sess.execute(select(Comm).order_by(Comm.code)).scalars()
        energisation_statuses = g.sess.query(EnergisationStatus).order_by(
            EnergisationStatus.code
        )
        default_energisation_status = EnergisationStatus.get_by_code(g.sess, "E")
        g_contracts = g.sess.execute(
            select(GContract)
            .where(GContract.is_industry == false())
            .order_by(GContract.name)
        ).scalars()
        g_units = g.sess.query(GUnit).order_by(GUnit.code)
        g_exit_zones = g.sess.query(GExitZone).order_by(GExitZone.code)
        g_reading_frequencies = g.sess.query(GReadingFrequency).order_by(
            GReadingFrequency.code
        )
        return render_template(
            "site_edit.html",
            site=site,
            sources=sources,
            generator_types=generator_types,
            gsp_groups=gsp_groups,
            eras=eras,
            energisation_statuses=energisation_statuses,
            default_energisation_status=default_energisation_status,
            mop_contracts=mop_contracts,
            dc_contracts=dc_contracts,
            supplier_contracts=supplier_contracts,
            pcs=pcs,
            cops=cops,
            comms=comms,
            g_contracts=g_contracts,
            g_units=g_units,
            g_exit_zones=g_exit_zones,
            g_reading_frequencies=g_reading_frequencies,
        )
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return render_template(
            "site_edit.html",
            site=site,
            sources=sources,
            generator_types=generator_types,
            gsp_groups=gsp_groups,
            eras=eras,
            mop_contracts=mop_contracts,
            dc_contracts=dc_contracts,
            supplier_contracts=supplier_contracts,
            pcs=pcs,
            cops=cops,
            comms=comms,
            g_contracts=g_contracts,
            g_units=g_units,
            g_exit_zones=g_exit_zones,
            g_reading_frequencies=g_reading_frequencies,
        )


@home.route("/sites/<int:site_id>/edit", methods=["POST"])
def site_edit_post(site_id):
    try:
        site = Site.get_by_id(g.sess, site_id)
        if "delete" in request.form:
            site.delete(g.sess)
            g.sess.commit()
            flash("Site deleted successfully.")
            return chellow_redirect("/sites", 303)

        elif "update" in request.form:
            code = req_str("code")
            name = req_str("site_name")
            site.update(code, name)
            g.sess.commit()
            flash("Site updated successfully.")
            return chellow_redirect(f"/sites/{site.id}", 303)

        elif "insert_electricity" in request.form:
            start_date = req_date("start")
            name = req_str("name")
            source_id = req_int("source_id")
            source = Source.get_by_id(g.sess, source_id)
            gsp_group_id = req_int("gsp_group_id")
            gsp_group = GspGroup.get_by_id(g.sess, gsp_group_id)
            mop_contract_id = req_int("mop_contract_id")
            mop_contract = Contract.get_mop_by_id(g.sess, mop_contract_id)
            mop_account = req_str("mop_account")
            dc_contract_id = req_int("dc_contract_id")
            dc_contract = Contract.get_dc_by_id(g.sess, dc_contract_id)
            dc_account = req_str("dc_account")
            msn = req_str("msn")
            pc_id = req_int("pc_id")
            pc = Pc.get_by_id(g.sess, pc_id)
            mtc_code = req_str("mtc_code")
            cop_id = req_int("cop_id")
            cop = Cop.get_by_id(g.sess, cop_id)
            comm_id = req_int("comm_id")
            comm = Comm.get_by_id(g.sess, comm_id)
            ssc_code = req_str("ssc_code")
            if len(ssc_code) > 0:
                ssc = Ssc.get_by_code(g.sess, ssc_code, start_date)
            else:
                ssc = None
            energisation_status_id = req_int("energisation_status_id")
            energisation_status = EnergisationStatus.get_by_id(
                g.sess, energisation_status_id
            )
            properties = req_zish("properties")
            if "generator_type_id" in request.form:
                generator_type_id = req_int("generator_type_id")
                generator_type = GeneratorType.get_by_id(g.sess, generator_type_id)
            else:
                generator_type = None

            if "imp_mpan_core" in request.form:
                imp_mpan_core_raw = req_str("imp_mpan_core")
                if len(imp_mpan_core_raw) == 0:
                    imp_mpan_core = None
                else:
                    imp_mpan_core = parse_mpan_core(imp_mpan_core_raw)
            else:
                imp_mpan_core = None

            if imp_mpan_core is None:
                imp_supplier_contract = None
                imp_supplier_account = None
                imp_sc = None
                imp_llfc_code = None
            else:
                imp_supplier_contract_id = req_int("imp_supplier_contract_id")
                imp_supplier_contract = Contract.get_supplier_by_id(
                    g.sess, imp_supplier_contract_id
                )
                imp_supplier_account = req_str("imp_supplier_account")
                imp_sc = req_int("imp_sc")
                imp_llfc_code = req_str("imp_llfc_code")

            if "exp_mpan_core" in request.form:
                exp_mpan_core_raw = req_str("exp_mpan_core")
                if len(exp_mpan_core_raw) == 0:
                    exp_mpan_core = None
                else:
                    exp_mpan_core = parse_mpan_core(exp_mpan_core_raw)
            else:
                exp_mpan_core = None

            if exp_mpan_core is None:
                exp_supplier_contract = None
                exp_supplier_account = None
                exp_sc = None
                exp_llfc_code = None
            else:
                exp_supplier_contract_id = req_int("exp_supplier_contract_id")
                exp_supplier_contract = Contract.get_supplier_by_id(
                    g.sess, exp_supplier_contract_id
                )
                exp_supplier_account = req_str("exp_supplier_account")
                exp_sc = req_int("exp_sc")
                exp_llfc_code = req_str("exp_llfc_code")

            supply = site.insert_e_supply(
                g.sess,
                source,
                generator_type,
                name,
                start_date,
                None,
                gsp_group,
                mop_contract,
                mop_account,
                dc_contract,
                dc_account,
                msn,
                pc,
                mtc_code,
                cop,
                comm,
                ssc,
                energisation_status,
                properties,
                imp_mpan_core,
                imp_llfc_code,
                imp_supplier_contract,
                imp_supplier_account,
                imp_sc,
                exp_mpan_core,
                exp_llfc_code,
                exp_supplier_contract,
                exp_supplier_account,
                exp_sc,
            )
            g.sess.commit()
            return chellow_redirect(f"/e/supplies/{supply.id}", 303)

        elif "insert_gas" in request.form:
            name = req_str("name")
            msn = req_str("msn")
            mprn = req_str("mprn")
            correction_factor = req_decimal("correction_factor")
            g_unit_id = req_int("g_unit_id")
            g_unit = GUnit.get_by_id(g.sess, g_unit_id)
            g_exit_zone_id = req_int("g_exit_zone_id")
            g_exit_zone = GExitZone.get_by_id(g.sess, g_exit_zone_id)
            g_contract_id = req_int("g_contract_id")
            g_contract = GContract.get_by_id(g.sess, g_contract_id)
            account = req_str("account")
            g_reading_frequency_id = req_int("g_reading_frequency_id")
            g_reading_frequency = GReadingFrequency.get_by_id(
                g.sess, g_reading_frequency_id
            )
            start_date = req_date("start")
            g_supply = site.insert_g_supply(
                g.sess,
                mprn,
                name,
                g_exit_zone,
                start_date,
                None,
                msn,
                correction_factor,
                g_unit,
                g_contract,
                account,
                g_reading_frequency,
            )
            g.sess.commit()
            return chellow_redirect(f"/g/supplies/{g_supply.id}", 303)
        else:
            raise BadRequest(
                "The request must contain one of the following parameter names: "
                "delete, update, insert_electricity, insert_gas."
            )

    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        sources = g.sess.query(Source).order_by(Source.code)
        generator_types = g.sess.query(GeneratorType).order_by(GeneratorType.code)
        gsp_groups = g.sess.query(GspGroup).order_by(GspGroup.code)
        energisation_statuses = g.sess.query(EnergisationStatus).order_by(
            EnergisationStatus.code
        )
        default_energisation_status = EnergisationStatus.get_by_code(g.sess, "E")
        eras = (
            g.sess.query(Era)
            .join(SiteEra)
            .filter(SiteEra.site == site)
            .order_by(Era.start_date.desc())
        )
        mop_contracts = (
            g.sess.query(Contract)
            .join(MarketRole)
            .filter(MarketRole.code == "M")
            .order_by(Contract.name)
        )
        dc_contracts = (
            g.sess.query(Contract)
            .join(MarketRole)
            .filter(MarketRole.code.in_(("C", "D")))
            .order_by(Contract.name)
        )
        supplier_contracts = (
            g.sess.query(Contract)
            .join(MarketRole)
            .filter(MarketRole.code == "X")
            .order_by(Contract.name)
        )
        pcs = g.sess.query(Pc).order_by(Pc.code)
        cops = g.sess.query(Cop).order_by(Cop.code)
        comms = g.sess.execute(select(Comm).order_by(Comm.code)).scalars()
        g_contracts = g.sess.query(GContract).order_by(GContract.name)
        g_units = g.sess.query(GUnit).order_by(GUnit.code)
        g_exit_zones = g.sess.query(GExitZone).order_by(GExitZone.code)
        g_reading_frequencies = g.sess.query(GReadingFrequency).order_by(
            GReadingFrequency.code
        )
        return make_response(
            render_template(
                "site_edit.html",
                site=site,
                sources=sources,
                generator_types=generator_types,
                gsp_groups=gsp_groups,
                energisation_statuses=energisation_statuses,
                default_energisation_status=default_energisation_status,
                eras=eras,
                mop_contracts=mop_contracts,
                dc_contracts=dc_contracts,
                supplier_contracts=supplier_contracts,
                pcs=pcs,
                cops=cops,
                comms=comms,
                g_contracts=g_contracts,
                g_units=g_units,
                g_exit_zones=g_exit_zones,
                g_reading_frequencies=g_reading_frequencies,
            ),
            400,
        )


@home.route("/sites/add", methods=["POST"])
def site_add_post():
    try:
        code = req_str("code")
        name = req_str("name")
        site = Site.insert(g.sess, code, name)
        g.sess.commit()
        return chellow_redirect("/sites/" + str(site.id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template("site_add.html")


@home.route("/sites/add")
def site_add_get():
    return render_template("site_add.html")


@home.route("/sites")
def sites_get():
    LIMIT = 50
    if "pattern" in request.values:
        pattern = req_str("pattern")
        sites = (
            g.sess.query(Site)
            .from_statement(
                text(
                    "select * from site "
                    "where lower(code || ' ' || name) like '%' || lower(:pattern) "
                    "|| '%' order by code limit :lim"
                )
            )
            .params(pattern=pattern.strip(), lim=LIMIT)
            .all()
        )

        if len(sites) == 1:
            return chellow_redirect(f"/sites/{sites[0].id}")
        else:
            return render_template("sites.html", sites=sites, limit=LIMIT)
    else:
        return render_template("sites.html")


@home.route("/supplies")
def supplies_get():
    if "search_pattern" in request.args:
        pattern = req_str("search_pattern")
        pattern = pattern.strip()
        reduced_pattern = pattern.replace(" ", "")
        if "max_results" in request.args:
            max_results = req_int("max_results")
        else:
            max_results = 50
        e_eras = (
            g.sess.query(Era)
            .from_statement(
                text(
                    "select e1.* from era as e1 "
                    "inner join (select e2.supply_id, max(e2.start_date) "
                    "as max_start_date from era as e2 "
                    "where replace(lower(e2.imp_mpan_core), ' ', '') "
                    "like lower(:reduced_pattern) "
                    "or lower(e2.imp_supplier_account) like lower(:pattern) "
                    "or replace(lower(e2.exp_mpan_core), ' ', '') "
                    "like lower(:reduced_pattern) "
                    "or lower(e2.exp_supplier_account) like lower(:pattern) "
                    "or lower(e2.dc_account) like lower(:pattern) "
                    "or lower(e2.mop_account) like lower(:pattern) "
                    "or lower(e2.msn) like lower(:pattern) "
                    "group by e2.supply_id) as sq "
                    "on e1.supply_id = sq.supply_id "
                    "and e1.start_date = sq.max_start_date limit :max_results"
                )
            )
            .params(
                pattern="%" + pattern + "%",
                reduced_pattern="%" + reduced_pattern + "%",
                max_results=max_results,
            )
            .all()
        )

        g_eras = (
            g.sess.query(GEra)
            .from_statement(
                text(
                    """
select e1.* from g_era as e1 inner join
  (select e2.g_supply_id, max(e2.start_date) as max_start_date
  from g_era as e2 join g_supply on e2.g_supply_id = g_supply.id
  where
    lower(g_supply.mprn) like lower(:pattern)
    or lower(e2.account) like lower(:pattern)
    or lower(e2.msn) like lower(:pattern)
  group by e2.g_supply_id) as sq
on e1.g_supply_id = sq.g_supply_id and e1.start_date = sq.max_start_date
limit :max_results"""
                )
            )
            .params(pattern="%" + pattern + "%", max_results=max_results)
            .all()
        )

        if len(e_eras) == 1 and len(g_eras) == 0:
            return chellow_redirect(f"/e/supplies/{e_eras[0].supply.id}", 307)
        elif len(e_eras) == 0 and len(g_eras) == 1:
            return chellow_redirect(f"/g/supplies/{g_eras[0].g_supply.id}", 307)
        else:
            return render_template(
                "supplies.html", e_eras=e_eras, g_eras=g_eras, max_results=max_results
            )
    else:
        return render_template("supplies.html")


@home.route("/reports/<report_id>")
def report_get(report_id):
    report_module = importlib.import_module(f"chellow.reports.report_{report_id}")
    return report_module.do_get(g.sess)


@home.route("/reports/<report_id>", methods=["POST"])
def report_post(report_id):
    report_module = importlib.import_module(f"chellow.reports.report_{report_id}")
    return report_module.do_post(g.sess)


@home.route("/sites/<int:site_id>/hh_data")
def site_hh_data_get(site_id):
    caches = {}
    site = Site.get_by_id(g.sess, site_id)

    year = req_int("year")
    month = req_int("month")
    start_date, finish_date = next(
        c_months_u(start_year=year, start_month=month, months=1)
    )

    supplies = (
        g.sess.query(Supply)
        .join(Era)
        .join(SiteEra)
        .join(Source)
        .filter(
            SiteEra.site == site,
            SiteEra.is_physical == true(),
            Era.start_date <= finish_date,
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
            Source.code != "sub",
        )
        .order_by(Supply.id)
        .distinct()
        .options(joinedload(Supply.source), joinedload(Supply.generator_type))
        .all()
    )

    data = iter(
        g.sess.query(HhDatum)
        .join(Channel)
        .join(Era)
        .filter(
            Channel.channel_type == "ACTIVE",
            Era.supply_id.in_([s.id for s in supplies]),
            HhDatum.start_date >= start_date,
            HhDatum.start_date <= finish_date,
        )
        .order_by(HhDatum.start_date, Era.supply_id)
        .options(
            joinedload(HhDatum.channel)
            .joinedload(Channel.era)
            .joinedload(Era.supply)
            .joinedload(Supply.source)
        )
    )
    datum = next(data, None)

    hh_data = []
    for hh_date in hh_range(caches, start_date, finish_date):
        sups = []
        hh_dict = {
            "start_date": hh_date,
            "supplies": sups,
            "export_kwh": 0,
            "import_kwh": 0,
            "parasitic_kwh": 0,
            "generated_kwh": 0,
            "third_party_import_kwh": 0,
            "third_party_export_kwh": 0,
        }
        hh_data.append(hh_dict)
        for supply in supplies:
            sup_hh = {}
            sups.append(sup_hh)
            while (
                datum is not None
                and datum.start_date == hh_date
                and datum.channel.era.supply_id == supply.id
            ):
                channel = datum.channel
                imp_related = channel.imp_related
                hh_float_value = float(datum.value)
                source_code = channel.era.supply.source.code

                prefix = "import_" if imp_related else "export_"
                sup_hh[prefix + "kwh"] = datum.value
                sup_hh[prefix + "status"] = datum.status

                if not imp_related and source_code in ("net", "gen-net"):
                    hh_dict["export_kwh"] += hh_float_value
                if imp_related and source_code in ("net", "gen-net"):
                    hh_dict["import_kwh"] += hh_float_value
                if (imp_related and source_code == "gen") or (
                    not imp_related and source_code == "gen-net"
                ):
                    hh_dict["generated_kwh"] += hh_float_value
                if (not imp_related and source_code == "gen") or (
                    imp_related and source_code == "gen-net"
                ):
                    hh_dict["parasitic_kwh"] += hh_float_value
                if (imp_related and source_code == "3rd-party") or (
                    not imp_related and source_code == "3rd-party-reverse"
                ):
                    hh_dict["third_party_import_kwh"] += hh_float_value
                if (not imp_related and source_code == "3rd-party") or (
                    imp_related and source_code == "3rd-party-reverse"
                ):
                    hh_dict["third_party_export_kwh"] += hh_float_value
                datum = next(data, None)

        hh_dict["displaced_kwh"] = (
            hh_dict["generated_kwh"] - hh_dict["export_kwh"] - hh_dict["parasitic_kwh"]
        )
        hh_dict["used_kwh"] = sum(
            (
                hh_dict["import_kwh"],
                hh_dict["displaced_kwh"],
                hh_dict["third_party_import_kwh"] - hh_dict["third_party_export_kwh"],
            )
        )

    return render_template(
        "site_hh_data.html", site=site, supplies=supplies, hh_data=hh_data
    )


@home.route("/sites/<int:site_id>")
def site_get(site_id):
    configuration_contract = Contract.get_non_core_by_name(g.sess, "configuration")
    site = Site.get_by_id(g.sess, site_id)

    eras = (
        g.sess.query(Era)
        .join(SiteEra)
        .filter(SiteEra.site == site)
        .order_by(Era.supply_id, Era.start_date.desc())
        .all()
    )

    groups = []
    for idx, era in enumerate(eras):
        if idx == 0 or eras[idx - 1].supply_id != era.supply_id:
            if era.pc.code == "00":
                meter_cat = "HH"
            elif len(era.channels) > 0:
                meter_cat = "AMR"
            elif era.mtc_participant.meter_type.code in ["UM", "PH"]:
                meter_cat = "Unmetered"
            else:
                meter_cat = "NHH"

            groups.append(
                {
                    "last_era": era,
                    "is_ongoing": era.finish_date is None,
                    "meter_category": meter_cat,
                }
            )

        if era == eras[-1] or era.supply_id != eras[idx + 1]:
            groups[-1]["first_era"] = era

    groups = sorted(groups, key=itemgetter("is_ongoing"), reverse=True)

    g_eras = (
        g.sess.query(GEra)
        .join(SiteGEra)
        .filter(SiteGEra.site == site)
        .order_by(GEra.g_supply_id, GEra.start_date.desc())
        .all()
    )

    g_groups = []
    for idx, g_era in enumerate(g_eras):
        if idx == 0 or g_eras[idx - 1].g_supply_id != g_era.g_supply_id:
            g_groups.append(
                {"last_g_era": g_era, "is_ongoing": g_era.finish_date is None}
            )

        if g_era == g_eras[-1] or g_era.g_supply_id != g_eras[idx + 1]:
            g_groups[-1]["first_g_era"] = g_era

    g_groups = sorted(g_groups, key=itemgetter("is_ongoing"), reverse=True)

    now = utc_datetime_now()
    month_start = Datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH
    last_month_start = month_start - relativedelta(months=1)
    last_month_finish = month_start - HH

    properties = configuration_contract.make_properties()
    other_sites = site.find_linked_sites(g.sess, now, now)
    scenarios = g.sess.query(Scenario).order_by(Scenario.name).all()
    return render_template(
        "site.html",
        site=site,
        groups=groups,
        properties=properties,
        other_sites=other_sites,
        month_start=month_start,
        month_finish=month_finish,
        last_month_start=last_month_start,
        last_month_finish=last_month_finish,
        scenarios=scenarios,
        g_groups=g_groups,
    )


@home.route("/downloads")
def downloads_get():
    files = []
    download_path = chellow.dloads.download_path

    for fl in sorted(os.listdir(download_path), reverse=True):
        statinfo = os.stat(os.path.join(download_path, fl))
        files.append(
            {
                "name": fl,
                "last_modified": Datetime.utcfromtimestamp(statinfo.st_mtime),
                "size": statinfo.st_size,
            }
        )

    return render_template("downloads.html", files=files)


@home.route("/downloads", methods=["POST"])
def downloads_post():
    chellow.dloads.reset()
    return chellow_redirect("/downloads", 303)


@home.route("/downloads/<fname>")
def download_get(fname):
    head, name = os.path.split(os.path.normcase(os.path.normpath(fname)))

    download_path = os.path.join(current_app.instance_path, "downloads")

    full_name = os.path.join(download_path, name)

    def content():
        try:
            with open(full_name, "rb") as fl:
                while True:
                    data = fl.read(DEFAULT_BUFFER_SIZE)
                    if len(data) == 0:
                        break
                    yield data
        except BaseException:
            yield traceback.format_exc()

    return send_response(content, file_name=name)


@home.route("/downloads/<fname>", methods=["POST"])
def download_post(fname):
    head, name = os.path.split(os.path.normcase(os.path.normpath(fname)))

    download_path = os.path.join(current_app.instance_path, "downloads")
    full_name = os.path.join(download_path, name)
    os.remove(full_name)
    return chellow_redirect("/downloads", 303)


@home.route("/report_runs")
def report_runs_get():
    runs = g.sess.query(ReportRun).order_by(ReportRun.date_created.desc())

    return render_template("report_runs.html", runs=runs)


@home.route("/report_runs/<int:run_id>")
def report_run_get(run_id):
    run = g.sess.query(ReportRun).filter(ReportRun.id == run_id).one()
    if run.name == "bill_check":
        row = (
            g.sess.query(ReportRunRow)
            .filter(ReportRunRow.report_run == run)
            .order_by(ReportRunRow.id)
            .first()
        )
        elements = []
        summary = {}
        if row is None:
            pass

        else:
            titles = row.data["titles"]
            diff_titles = [
                t for t in titles if t.startswith("difference-") and t.endswith("-gbp")
            ]
            diff_selects = [
                func.sum(ReportRunRow.data["values"][t].as_float()) for t in diff_titles
            ]
            sum_diffs = (
                g.sess.query(*diff_selects).filter(ReportRunRow.report_run == run).one()
            )

            for t, sum_diff in zip(diff_titles, sum_diffs):
                elem = t[11:-4]
                if elem == "net":
                    summary["sum_difference"] = sum_diff
                else:
                    elements.append((elem, sum_diff))

            elements.sort(key=lambda x: abs(x[1]), reverse=True)
            elements.insert(0, ("net", summary["sum_difference"]))

        if "element" in request.values:
            element = req_str("element")
        else:
            element = "net"

        hide_checked = req_bool("hide_checked")

        order_by = f"difference-{element}-gbp"
        q = g.sess.query(ReportRunRow).filter(ReportRunRow.report_run == run)
        if hide_checked:
            q = q.filter(
                ReportRunRow.data["properties"]["is_checked"].as_boolean() == false()
            )

        rows = (
            q.order_by(
                func.abs(ReportRunRow.data["values"][order_by].as_float()).desc()
            )
            .limit(200)
            .all()
        )
        return render_template(
            "report_run_bill_check.html",
            run=run,
            rows=rows,
            summary=summary,
            elements=elements,
            element=element,
            hide_checked=hide_checked,
        )

    elif run.name == "asset_comparison":
        rows = (
            g.sess.execute(
                select(ReportRunRow)
                .filter(ReportRunRow.report_run == run)
                .order_by(ReportRunRow.data["values"]["asset_status"])
            )
            .scalars()
            .all()
        )
        return render_template(
            "report_run_asset_comparison.html",
            run=run,
            rows=rows,
        )

    elif run.name == "ecoes_comparison":
        rows = (
            g.sess.execute(
                select(ReportRunRow)
                .filter(ReportRunRow.report_run == run)
                .order_by(
                    ReportRunRow.data["values"]["chellow_supplier_contract_name"],
                    ReportRunRow.data["values"]["problem"],
                )
            )
            .scalars()
            .all()
        )
        return render_template(
            "report_run_ecoes_comparison.html",
            run=run,
            rows=rows,
        )

    elif run.name == "supply_contacts":
        rows = (
            g.sess.execute(
                select(ReportRunRow)
                .filter(ReportRunRow.report_run == run)
                .order_by(
                    ReportRunRow.data["values"]["site_code"],
                )
            )
            .scalars()
            .all()
        )
        return render_template(
            "report_run_supply_contacts.html",
            run=run,
            rows=rows,
        )

    else:
        order_by = "row.id"
        ob = ReportRunRow.id
        summary = {}

        rows = (
            g.sess.query(ReportRunRow)
            .filter(ReportRunRow.report_run == run)
            .order_by(ob)
            .limit(200)
            .all()
        )

        return render_template(
            "report_run_asset_comparison.html",
            run=run,
            rows=rows,
            order_by=order_by,
            summary=summary,
        )


@home.route("/report_runs/<int:run_id>", methods=["POST"])
def report_run_post(run_id):
    run = g.sess.query(ReportRun).filter(ReportRun.id == run_id).one()
    run.delete(g.sess)
    g.sess.commit()
    return chellow_redirect("/report_runs", 303)


@home.route("/report_runs/<int:run_id>/spreadsheet")
def report_run_spreadsheet_get(run_id):
    run = g.sess.query(ReportRun).filter(ReportRun.id == run_id).one()

    si = StringIO()
    cw = csv.writer(si)

    first_row = (
        g.sess.execute(
            select(ReportRunRow)
            .where(ReportRunRow.report_run == run)
            .order_by(ReportRunRow.id)
        )
        .scalars()
        .first()
    )

    if first_row is not None:
        titles = first_row.data["titles"]
        cw.writerow(titles)

    for row in g.sess.execute(
        select(ReportRunRow)
        .where(ReportRunRow.report_run == run)
        .order_by(ReportRunRow.id)
    ).scalars():
        cw.writerow([csv_make_val(row.data["values"].get(t)) for t in titles])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = f'attachment; filename="{run.title}"'
    output.headers["Content-type"] = "text/csv"
    return output


@home.route("/report_run_rows/<int:row_id>")
def report_run_row_get(row_id):
    row = g.sess.query(ReportRunRow).filter(ReportRunRow.id == row_id).one()
    raw_data = json.dumps(row.data, sort_keys=True, indent=4)
    tables = []

    if row.report_run.name == "bill_check":
        values = row.data["values"]
        elements = {}
        for t in row.data["values"].keys():
            if t == "difference-tpr-gbp":
                continue

            if (
                t.startswith("covered-")
                or t.startswith("virtual-")
                or t.startswith("difference-")
            ) and t not in (
                "covered-from",
                "covered-to",
                "covered-bills",
                "covered-problem",
                "virtual-problem",
            ):

                toks = t.split("-")
                name = toks[1]
                try:
                    table = elements[name]
                except KeyError:
                    table = elements[name] = {"order": 0}

                if "titles" not in table:
                    table["titles"] = []
                table["titles"].append(toks[0] + "-" + "-".join(toks[2:]))
                if "values" not in table:
                    table["values"] = []
                table["values"].append(values[t])
                if t.startswith("difference-") and t.endswith("-gbp"):
                    table["order"] = abs(values[t])

        for k, v in elements.items():
            if k == "net":
                continue
            v["name"] = k
            tables.append(v)

        tables.sort(key=lambda t: t["order"], reverse=True)
        return render_template(
            "report_run_row_bill_check.html", row=row, raw_data=raw_data, tables=tables
        )

    else:

        return render_template(
            "report_run_row.html", row=row, raw_data=raw_data, tables=tables
        )


@home.route("/report_run_rows/<int:row_id>", methods=["POST"])
def report_run_row_post(row_id):
    row = g.sess.query(ReportRunRow).filter(ReportRunRow.id == row_id).one()

    if row.report_run.name == "bill_check":
        is_checked = req_bool("is_checked")
        note = req_str("note")

        properties = row.data.get("properties", {})
        properties["is_checked"] = is_checked
        properties["note"] = note
        row.data["properties"] = properties
        flag_modified(row, "data")
        g.sess.commit()
        flash("Update successful")

    return chellow_redirect(f"/report_run_rows/{row_id}", 303)


@home.route("/non_core_contracts")
def non_core_contracts_get():
    non_core_contracts = (
        g.sess.query(Contract)
        .join(MarketRole)
        .filter(MarketRole.code == "Z")
        .order_by(Contract.name)
        .all()
    )
    return render_template(
        "non_core_contracts.html", non_core_contracts=non_core_contracts
    )


@home.route("/non_core_contracts/<int:contract_id>")
def non_core_contract_get(contract_id):
    contract = Contract.get_non_core_by_id(g.sess, contract_id)
    rate_scripts = (
        g.sess.query(RateScript)
        .filter(RateScript.contract == contract)
        .order_by(RateScript.start_date.desc())
        .all()
    )
    try:
        import_module("chellow." + contract.name).get_importer()
        has_auto_importer = True
    except AttributeError:
        has_auto_importer = False
    except ImportError:
        has_auto_importer = False

    return render_template(
        "non_core_contract.html",
        contract=contract,
        rate_scripts=rate_scripts,
        has_auto_importer=has_auto_importer,
    )


@home.route("/sites/<int:site_id>/used_graph")
def site_used_graph_get(site_id):
    cache = {}
    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    months = req_int("months")

    finish_date = utc_datetime(finish_year, finish_month) + relativedelta(months=1) - HH
    start_date = utc_datetime(finish_year, finish_month) - relativedelta(
        months=months - 1
    )

    site = Site.get_by_id(g.sess, site_id)
    supplies = (
        g.sess.query(Supply)
        .join(Era)
        .join(Source)
        .join(SiteEra)
        .filter(SiteEra.site == site, not_(Source.code.in_(("sub", "gen-net"))))
        .distinct()
        .all()
    )

    results = iter(
        g.sess.query(
            cast(HhDatum.value, Float),
            HhDatum.start_date,
            HhDatum.status,
            Channel.imp_related,
            Source.code,
        )
        .join(Channel)
        .join(Era)
        .join(Supply)
        .join(Source)
        .filter(
            Channel.channel_type == "ACTIVE",
            HhDatum.start_date >= start_date,
            HhDatum.start_date <= finish_date,
            Supply.id.in_(s.id for s in supplies),
        )
        .order_by(HhDatum.start_date)
    )

    max_scale = 2
    min_scale = 0
    result_data = []
    days = []
    month_list = []
    step = 1

    (
        hh_channel_value,
        hh_channel_start_date,
        hh_channel_status,
        is_import,
        source_code,
    ) = next(results, (None, None, None, None, None))

    for hh_date in hh_range(cache, start_date, finish_date):
        complete = None
        hh_value = 0

        while hh_channel_start_date == hh_date:
            if (is_import and source_code != "3rd-party-reverse") or (
                not is_import and source_code == "3rd-party-reverse"
            ):
                hh_value += hh_channel_value
            else:
                hh_value -= hh_channel_value
            if hh_channel_status == "A":
                if complete is None:
                    complete = True
            else:
                complete = False
            (
                hh_channel_value,
                hh_channel_start_date,
                hh_channel_status,
                is_import,
                source_code,
            ) = next(results, (None, None, None, None, None))

        result_data.append(
            {"value": hh_value, "start_date": hh_date, "is_complete": complete is True}
        )
        max_scale = max(max_scale, int(math.ceil(hh_value)))
        min_scale = min(min_scale, int(math.floor(hh_value)))

    step = 10 ** int(math.floor(math.log10(max_scale - min_scale)))

    max_height = 300
    scale_factor = float(max_height) / (max_scale - min_scale)
    graph_top = 50
    x_axis = int(graph_top + max_scale * scale_factor)

    for i, hh in enumerate(result_data):
        hh["height"] = int(scale_factor * hh["value"])
        hh_start = hh["start_date"]
        if hh_start.hour == 0 and hh_start.minute == 0:
            days.append(
                {
                    "colour": "red" if hh_start.weekday() > 4 else "black",
                    "day": hh_start.day,
                }
            )

            if hh_start.day == 15:
                month_list.append({"name": hh_start.strftime("%B"), "x": i})

    scale_lines = []
    for height in chain(
        range(0, max_scale + 1, step), range(0, min_scale - 1, step * -1)
    ):
        scale_lines.append({"height": height, "y": int(x_axis - height * scale_factor)})

    title = (
        "Electricity use at site "
        + site.code
        + " "
        + site.name
        + " for "
        + str(months)
        + " month"
        + ("s" if months > 1 else "")
        + " ending "
        + finish_date.strftime("%B %Y")
    )

    return render_template(
        "site_used_graph.html",
        result_data=result_data,
        graph_left=100,
        graph_top=graph_top,
        x_axis=x_axis,
        max_height=max_height,
        days=days,
        months=month_list,
        scale_lines=scale_lines,
        title=title,
        site=site,
        finish_date=finish_date,
    )


@home.route("/non_core_contracts/<int:contract_id>/edit")
def non_core_contract_edit_get(contract_id):
    contract = Contract.get_non_core_by_id(g.sess, contract_id)
    return render_template("non_core_contract_edit.html", contract=contract)


@home.route("/non_core_contracts/<int:contract_id>/edit", methods=["POST"])
def non_core_contract_edit_post(contract_id):
    try:
        contract = Contract.get_non_core_by_id(g.sess, contract_id)
        if "delete" in request.values:
            contract.delete(g.sess)
            g.sess.commit()
            return chellow_redirect("/non_core_contracts", 303)
        if "update_state" in request.values:
            state = req_zish("state")
            contract.update_state(state)
            g.sess.commit()
            return chellow_redirect(f"/non_core_contracts/{contract.id}", 303)
        else:
            properties = req_zish("properties")
            contract.update_properties(properties)
            g.sess.commit()
            return chellow_redirect(f"/non_core_contracts/{contract.id}", 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template("non_core_contract_edit.html", contract=contract), 400
        )


@home.route("/sites/<int:site_id>/months")
def site_months_get(site_id):
    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    site = Site.get_by_id(g.sess, site_id)

    typs = ("imp_net", "exp_net", "used", "displaced", "imp_gen", "exp_gen")

    months = []
    for month_start, month_finish in c_months_u(
        finish_year=finish_year, finish_month=finish_month, months=12
    ):
        month = dict((typ, {"md": 0, "md_date": None, "kwh": 0}) for typ in typs)
        month["start_date"] = month_start
        month["start_date_ct"] = to_ct(month_start)
        months.append(month)

        for hh in site.hh_data(g.sess, month_start, month_finish):
            for tp in typs:
                if hh[tp] * 2 > month[tp]["md"]:
                    month[tp]["md"] = hh[tp] * 2
                    month[tp]["md_date"] = hh["start_date"]
                month[tp]["kwh"] += hh[tp]

        month["has_site_snags"] = (
            g.sess.query(Snag)
            .filter(
                Snag.site == site,
                Snag.start_date <= month_finish,
                or_(Snag.finish_date == null(), Snag.finish_date > month_start),
            )
            .count()
            > 0
        )

    totals = dict((typ, {"md": 0, "md_date": None, "kwh": 0}) for typ in typs)

    for month in months:
        for typ in typs:
            if month[typ]["md"] > totals[typ]["md"]:
                totals[typ]["md"] = month[typ]["md"]
                totals[typ]["md_date"] = month[typ]["md_date"]
            totals[typ]["kwh"] += month[typ]["kwh"]

    months.append(totals)

    return render_template("site_months.html", site=site, months=months)


@home.route("/non_core_contracts/<int:contract_id>/add_rate_script")
def non_core_rate_script_add_get(contract_id):
    now = utc_datetime_now()
    initial_date = utc_datetime(now.year, now.month)
    contract = Contract.get_non_core_by_id(g.sess, contract_id)
    return render_template(
        "non_core_rate_script_add.html",
        now=now,
        initial_date=initial_date,
        contract=contract,
    )


@home.route("/non_core_contracts/<int:contract_id>/add_rate_script", methods=["POST"])
def non_core_rate_script_add_post(contract_id):
    try:
        contract = Contract.get_non_core_by_id(g.sess, contract_id)
        start_date = req_date("start")
        rate_script = contract.insert_rate_script(g.sess, start_date, {})
        g.sess.commit()
        return chellow_redirect("/non_core_rate_scripts/" + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = utc_datetime_now()
        initial_date = utc_datetime(now.year, now.month)
        return make_response(
            render_template(
                "non_core_rate_script_add.html",
                now=now,
                initial_date=initial_date,
                contract=contract,
            ),
            400,
        )


@home.route("/non_core_rate_scripts/<int:rs_id>")
def non_core_rate_script_get(rs_id):
    rate_script = RateScript.get_non_core_by_id(g.sess, rs_id)
    contract = rate_script.contract
    next_rate_script = (
        g.sess.query(RateScript)
        .filter(
            RateScript.contract == contract,
            RateScript.start_date > rate_script.start_date,
        )
        .order_by(RateScript.start_date)
        .first()
    )
    previous_rate_script = (
        g.sess.query(RateScript)
        .filter(
            RateScript.contract == contract,
            RateScript.start_date < rate_script.start_date,
        )
        .order_by(RateScript.start_date.desc())
        .first()
    )
    return render_template(
        "non_core_rate_script.html",
        rate_script=rate_script,
        previous_rate_script=previous_rate_script,
        next_rate_script=next_rate_script,
    )


@home.route("/non_core_rate_scripts/<int:rs_id>/edit")
def non_core_rate_script_edit_get(rs_id):
    rate_script = RateScript.get_non_core_by_id(g.sess, rs_id)
    try:
        rs_example_func = chellow.computer.contract_func(
            {}, rate_script.contract, "rate_script_example"
        )
        rs_example = None if rs_example_func is None else rs_example_func()
    except BaseException:
        rs_example = None

    return render_template(
        "non_core_rate_script_edit.html",
        rate_script=rate_script,
        rate_script_example=rs_example,
    )


@home.route("/non_core_rate_scripts/<int:rs_id>/edit", methods=["POST"])
def non_core_rate_script_edit_post(rs_id):
    try:
        rate_script = RateScript.get_non_core_by_id(g.sess, rs_id)
        contract = rate_script.contract
        if "delete" in request.values:
            contract.delete_rate_script(g.sess, rate_script)
            g.sess.commit()
            return chellow_redirect(f"/non_core_contracts/{contract.id}", 303)
        else:
            script = req_zish("script")
            start_date = req_hh_date("start")
            if "has_finished" in request.values:
                finish_date = req_date("finish")
            else:
                finish_date = None
            contract.update_rate_script(
                g.sess, rate_script, start_date, finish_date, script
            )
            g.sess.commit()
            return chellow_redirect(f"/non_core_rate_scripts/{rate_script.id}", 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template("non_core_rate_script_edit.html", rate_script=rate_script),
            400,
        )


@home.route("/non_core_contracts/<int:contract_id>/auto_importer")
def non_core_auto_importer_get(contract_id):
    contract = Contract.get_non_core_by_id(g.sess, contract_id)
    try:
        importer = import_module(f"chellow.{contract.name}").get_importer()
    except ModuleNotFoundError:
        importer = import_module(f"chellow.e.{contract.name}").get_importer()
    return render_template(
        "non_core_auto_importer.html", importer=importer, contract=contract
    )


@home.route("/non_core_contracts/<int:contract_id>/auto_importer", methods=["POST"])
def non_core_auto_importer_post(contract_id):
    try:
        contract = Contract.get_non_core_by_id(g.sess, contract_id)
        try:
            importer = import_module(f"chellow.{contract.name}").get_importer()
        except ModuleNotFoundError:
            importer = import_module(f"chellow.e.{contract.name}").get_importer()
        importer.go()
        return chellow_redirect(f"/non_core_contracts/{contract.id}/auto_importer", 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template(
                "non_core_auto_importer.html", importer=importer, contract=contract
            ),
            400,
        )


@home.route("/rate_server")
def rate_server_get():
    importer = chellow.rate_server.importer
    return render_template("rate_server.html", importer=importer)


@home.route("/rate_server", methods=["POST"])
def rate_server_post():
    importer = chellow.rate_server.importer
    importer.go()
    return chellow_redirect("/rate_server", 303)


@home.route("/tester")
def tester_get():
    tester = chellow.testing.tester
    return render_template("tester.html", tester=tester)


@home.route("/tester", methods=["POST"])
def tester_post():
    tester = chellow.testing.tester
    tester.go()
    return chellow_redirect("/tester", 303)


@home.route("/user_roles")
def user_roles_get():
    user_roles = g.sess.query(UserRole).order_by(UserRole.code)
    return render_template("user_roles.html", user_roles=user_roles)


@home.route("/bill_types/<int:type_id>")
def bill_type_get(type_id):
    bill_type = BillType.get_by_id(g.sess, type_id)
    return render_template("bill_type.html", bill_type=bill_type)


@home.route("/sites/<int:site_id>/gen_graph")
def site_gen_graph_get(site_id):
    cache = {}
    if "finish_year" in request.args:
        finish_year = req_int("finish_year")
        finish_month = req_int("finish_month")
        months = req_int("months")
    else:
        now = ct_datetime_now()
        finish_year = now.year
        finish_month = now.month
        months = 1

    month_list = list(
        c_months_u(finish_year=finish_year, finish_month=finish_month, months=months)
    )
    start_date, finish_date = month_list[0][0], month_list[-1][-1]

    site = Site.get_by_id(g.sess, site_id)

    colour_list = (
        "blue",
        "green",
        "red",
        "yellow",
        "maroon",
        "aqua",
        "fuchsia",
        "olive",
    )

    graph_names = ("used", "disp", "gen", "imp", "exp", "third")
    graphs = dict(
        (
            n,
            {
                "supplies": OrderedDict(),
                "ticks": [],
                "pos_hhs": [],
                "neg_hhs": [],
                "scale_lines": [],
                "scale_values": [],
                "monthly_scale_values": [],
            },
        )
        for n in graph_names
    )

    days = []
    month_points = []
    max_scls = {"pos": 10, "neg": 1}
    supply_ids = list(
        s.id
        for s in g.sess.query(Supply)
        .join(Era)
        .join(SiteEra)
        .join(Source)
        .filter(
            SiteEra.site == site,
            Source.code != "sub",
            SiteEra.is_physical == true(),
            Era.start_date <= finish_date,
            or_(Era.finish_date == null(), Era.finish_date >= start_date),
        )
        .distinct()
    )

    rs = iter(
        g.sess.query(
            cast(HhDatum.value * 2, Float),
            HhDatum.start_date,
            HhDatum.status,
            Channel.imp_related,
            Supply.name,
            Source.code,
            Supply.id,
        )
        .join(Channel)
        .join(Era)
        .join(Supply)
        .join(Source)
        .filter(
            Channel.channel_type == "ACTIVE",
            HhDatum.start_date >= start_date,
            HhDatum.start_date <= finish_date,
            Supply.id.in_(supply_ids),
        )
        .order_by(HhDatum.start_date, Supply.id)
    )
    (
        hhd_value,
        hhd_start_date,
        status,
        imp_related,
        supply_name,
        source_code,
        sup_id,
    ) = next(rs, (None, None, None, None, None, None, None))

    for x, hh_date in enumerate(hh_range(cache, start_date, finish_date)):
        hh_date_ct = to_ct(hh_date)
        rvals = dict((n, {"pos": 0, "neg": 0}) for n in graph_names)

        if hh_date_ct.hour == 0 and hh_date_ct.minute == 0:
            day = hh_date_ct.day
            days.append(
                {
                    "text": str(day),
                    "x": x + 20,
                    "colour": "red" if hh_date_ct.weekday() > 4 else "black",
                }
            )

            for g_name, graph in graphs.items():
                graph["ticks"].append({"x": x})

            if day == 15:
                month_points.append({"x": x, "text": hh_date_ct.strftime("%B")})

        is_complete = None

        while hhd_start_date == hh_date:
            if is_complete is None:
                is_complete = True

            if status != "A":
                is_complete = False

            to_adds = []
            if imp_related and source_code in ("net", "gen-net"):
                to_adds.append(("imp", "pos"))
            if not imp_related and source_code in ("net", "gen-net"):
                to_adds.append(("exp", "pos"))
            if (imp_related and source_code == "gen") or (
                not imp_related and source_code == "gen-net"
            ):
                to_adds.append(("gen", "pos"))
            if (not imp_related and source_code == "gen") or (
                imp_related and source_code == "gen-net"
            ):
                to_adds.append(("gen", "neg"))
            if (imp_related and source_code == "3rd-party") or (
                not imp_related and source_code == "3rd-party-reverse"
            ):
                to_adds.append(("third", "pos"))
            if (not imp_related and source_code == "3rd-party") or (
                imp_related and source_code == "3rd-party-reverse"
            ):
                to_adds.append(("third", "neg"))

            for gname, polarity in to_adds:
                graph = graphs[gname]
                supplies = graph["supplies"]
                if sup_id not in supplies:
                    supplies[sup_id] = {
                        "colour": colour_list[len(supplies)],
                        "text": source_code + " " + supply_name,
                        "source_code": source_code,
                    }

                grvals = rvals[gname]
                graph[polarity + "_hhs"].append(
                    {
                        "colour": graph["supplies"][sup_id]["colour"],
                        "running_total": grvals[polarity],
                        "value": hhd_value,
                        "x": x,
                        "start_date": hh_date,
                        "background_colour": "white",
                    }
                )
                grvals[polarity] += hhd_value
                max_scls[polarity] = max(max_scls[polarity], int(grvals[polarity]))

            (
                hhd_value,
                hhd_start_date,
                status,
                imp_related,
                supply_name,
                source_code,
                sup_id,
            ) = next(rs, (None, None, None, None, None, None, None))

        disp_val = rvals["gen"]["pos"] - rvals["gen"]["neg"] - rvals["exp"]["pos"]
        used_val = (
            rvals["imp"]["pos"]
            + disp_val
            + rvals["third"]["pos"]
            - rvals["third"]["neg"]
        )
        for val, graph_name in ((used_val, "used"), (disp_val, "disp")):
            graph = graphs[graph_name]
            pos_val = max(val, 0)
            neg_val = abs(min(val, 0))
            for gval, prefix in ((pos_val, "pos"), (neg_val, "neg")):
                hh_dict = {
                    "x": x,
                    "start_date": hh_date,
                    "value": gval,
                    "running_total": 0,
                }
                if is_complete is True:
                    hh_dict["colour"] = "blue"
                    hh_dict["background_colour"] = "white"
                else:
                    hh_dict["colour"] = "black"
                    hh_dict["background_colour"] = "grey"

                graph[prefix + "_hhs"].append(hh_dict)
                max_scls[prefix] = max(max_scls[prefix], int(gval))

    max_height = 80
    scl_factor = max_height / max_scls["pos"]

    raw_step_overall = max_scls["pos"] / (max_height / 20)
    factor_overall = 10 ** int(math.floor(math.log10(raw_step_overall)))
    end_overall = raw_step_overall / factor_overall
    new_end_overall = 1
    if end_overall >= 2:
        new_end_overall = 2
    if end_overall >= 5:
        new_end_overall = 5
    step_overall = max(int(new_end_overall * factor_overall), 1)

    graph_titles = {
        "exp": "Exported",
        "gen": "Generated",
        "imp": "Imported",
        "used": "Used",
        "disp": "Displaced",
        "third": "Third Party",
    }

    y = 50
    for graph_name in graph_names:
        graph = graphs[graph_name]
        graph["y"] = y
        graph["height_pos"] = max_scls["pos"] * scl_factor
        graph["height_neg"] = max_scls["neg"] * scl_factor
        graph["height"] = graph["height_pos"] + graph["height_neg"] + 100
        y += graph["height"]

        x_axis_px = max_scls["pos"] * scl_factor
        graph["title"] = graph_titles[graph_name]
        for tick in graph["ticks"]:
            tick["y"] = x_axis_px

        graph["scale_lines"] = []
        for pref in ("pos", "neg"):
            for i in range(0, max_scls[pref], step_overall):
                if pref == "pos":
                    y_scale = (-1 * i + max_scls[pref]) * scl_factor
                    fac = 1
                else:
                    fac = -1
                    y_scale = (i + max_scls["pos"]) * scl_factor
                graph["scale_lines"].append(
                    {
                        "y": y_scale,
                        "y_val": y_scale + 3,
                        "width": len(graphs["used"]["pos_hhs"]),
                        "text": str(fac * i),
                    }
                )

                for month_point in month_points:
                    graph["monthly_scale_values"].append(
                        {
                            "text": str(fac * i),
                            "x": month_point["x"] + 16,
                            "y": y_scale + 5,
                        }
                    )

        for ghh in graph["pos_hhs"]:
            height_px = ghh["value"] * scl_factor
            running_total_px = ghh["running_total"] * scl_factor
            ghh["height"] = height_px
            ghh["y"] = x_axis_px - height_px - running_total_px

        for ghh in graph["neg_hhs"]:
            ghh["height"] = ghh["value"] * scl_factor
            ghh["y"] = x_axis_px

    y += 30
    for day_dict in days:
        day_dict["y"] = graphs["third"]["height"] - 70

    height = y + 30

    for month_dict in month_points:
        month_dict["y"] = graphs["third"]["height"] - 40

    title = {
        "text": "Electricity at site "
        + site.code
        + " "
        + site.name
        + " for "
        + str(months)
        + " month"
        + ("s" if months > 1 else "")
        + " up to and including "
        + (to_ct(finish_date) - HH).strftime("%B %Y"),
        "x": 30,
        "y": 20,
    }

    return render_template(
        "site_gen_graph.html",
        finish_year=finish_year,
        finish_month=finish_month,
        months=months,
        site=site,
        finish_date=finish_date,
        graphs=graphs,
        month_points=month_points,
        graph_names=graph_names,
        title=title,
        height=height,
        days=days,
    )
