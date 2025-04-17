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
from functools import wraps
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
from sqlalchemy.orm.attributes import flag_modified

from werkzeug.exceptions import BadRequest, Forbidden

from zish import dumps

import chellow.bank_holidays
import chellow.dloads
import chellow.e.bill_importer
import chellow.e.bsuos
import chellow.e.computer
import chellow.e.hh_importer
import chellow.e.laf_import
import chellow.e.lcc
import chellow.e.mdd_importer
import chellow.e.rcrc
import chellow.e.system_price
import chellow.e.tlms
import chellow.general_import
import chellow.national_grid
import chellow.rate_server
from chellow.edi_lib import SEGMENTS, parse_edi
from chellow.models import (
    Batch,
    BillType,
    Channel,
    Comm,
    Contract,
    Cop,
    EnergisationStatus,
    Era,
    GBatch,
    GContract,
    GEra,
    GExitZone,
    GRateScript,
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
    Supply,
    User,
    UserRole,
)
from chellow.utils import (
    HH,
    c_months_c,
    c_months_u,
    csv_make_val,
    ct_datetime,
    ct_datetime_now,
    hh_range,
    req_bool,
    req_date,
    req_decimal,
    req_file,
    req_hh_date,
    req_int,
    req_int_none,
    req_str,
    req_zish,
    send_response,
    to_ct,
    to_utc,
    utc_datetime,
    utc_datetime_now,
)

home = Blueprint("home", __name__, url_prefix="", template_folder="templates")


def hx_redirect(path, status=None):
    res = Response(status=status)
    res.headers["HX-Redirect"] = path
    return res


def requires_editor(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if g.user.user_role.code == "editor":
            return f(*args, **kwargs)
        else:
            raise Forbidden("You must be an editor to do this.")

    return decorated_function


@home.route("/configuration", methods=["GET"])
def configuration():
    config = Contract.get_non_core_by_name(g.sess, "configuration")
    return redirect(f"/non_core_contracts/{config.id}")


@home.route("/fake_batch_updater")
def fake_batch_updater_get():
    importer = chellow.fake_batch_updater.importer
    config = Contract.get_non_core_by_name(g.sess, "configuration")
    props = config.make_properties()

    e_fake_batches = g.sess.scalars(
        select(Batch).where(
            Batch.reference.startswith("e_fake_batch_"),
        )
    )

    g_fake_batches = g.sess.scalars(
        select(GBatch).where(
            GBatch.reference.startswith("g_fake_batch_"),
        )
    )

    return render_template(
        "fake_batch_updater.html",
        importer=importer,
        config_state=config.make_state(),
        config_properties=props.get("fake_batch_updater", {}),
        e_fake_batches=e_fake_batches,
        g_fake_batches=g_fake_batches,
    )


@home.route("/fake_batch_updater", methods=["POST"])
def fake_batch_updater_post():
    importer = chellow.fake_batch_updater.importer
    importer.go()
    return redirect("/fake_batch_updater", 303)


@home.route("/health")
def health():
    return Response("healthy\n", mimetype="text/plain")


@home.route("/local_reports/<int:report_id>/output")
def local_report_output_get(report_id):
    report = g.sess.execute(select(Report).where(Report.id == report_id)).scalar_one()
    try:
        ns = {"report_id": report_id, "template": report.template}
        code = compile(report.script, f"<string report {report_id}>", "exec")
        exec(code, ns)
        return ns["do_get"]()
    except BaseException:
        return Response(traceback.format_exc(), status=500)


@home.route("/local_reports/<int:report_id>/output", methods=["GET", "POST"])
def local_report_output_post(report_id):
    report = g.sess.query(Report).get(report_id)
    try:
        ns = {"report_id": report_id, "template": report.template}
        code = compile(report.script, f"<string report {report_id}>", "exec")
        exec(code, ns)
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
    return redirect(f"/local_reports/{report.id}", 303)


@home.route("/local_reports/<int:report_id>")
def local_report_get(report_id):
    report = Report.get_by_id(g.sess, report_id)
    return render_template("local_report.html", report=report)


@home.route("/local_reports/<int:report_id>", methods=["POST"])
def local_report_post(report_id):
    report = Report.get_by_id(g.sess, report_id)
    if "delete" in request.values:
        g.sess.delete(report)
        return redirect("/local_reports", 303)

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
        return redirect(f"/local_reports/{report.id}", 303)


@home.route("/scenarios")
def scenarios_get():
    scenarios = g.sess.query(Scenario).order_by(Scenario.name).all()
    return render_template("scenarios.html", scenarios=scenarios)


@home.route("/scenarios/add", methods=["POST"])
def scenario_add_post():
    try:
        name = req_str("name")
        properties = req_zish("properties")
        scenario = Scenario.insert(g.sess, name, properties)
        g.sess.commit()
        return redirect(f"/scenarios/{scenario.id}", 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        scenarios = g.sess.query(Scenario).order_by(Scenario.name)
        return make_response(
            render_template("scenario_add.html", scenarios=scenarios), 400
        )


@home.route("/scenarios/add")
def scenario_add_get():
    now = utc_datetime_now()
    props = {
        "scenario_start_month": now.month,
        "scenario_start_year": now.year,
        "scenario_duration": 1,
    }
    return render_template("scenario_add.html", initial_props=dumps(props))


@home.route("/scenarios/<int:scenario_id>")
def scenario_get(scenario_id):
    start_date = None
    finish_date = None
    duration = 1

    scenario = Scenario.get_by_id(g.sess, scenario_id)
    props = scenario.props
    site_codes = "\n".join(props.get("site_codes", []))
    try:
        duration = props["scenario_duration"]
        _, finish_date_ct = list(
            c_months_c(
                start_year=props["scenario_start_year"],
                start_month=props["scenario_start_month"],
                months=duration,
            )
        )[-1]
        finish_date = to_utc(finish_date_ct)
    except KeyError:
        pass

    try:
        start_date = to_utc(
            ct_datetime(
                props["scenario_start_year"],
                props["scenario_start_month"],
                props["scenario_start_day"],
                props["scenario_start_hour"],
                props["scenario_start_minute"],
            )
        )
    except KeyError:
        pass

    try:
        finish_date = to_utc(
            ct_datetime(
                props["scenario_finish_year"],
                props["scenario_finish_month"],
                props["scenario_finish_day"],
                props["scenario_finish_hour"],
                props["scenario_finish_minute"],
            )
        )
    except KeyError:
        pass
    return render_template(
        "scenario.html",
        scenario=scenario,
        scenario_start_date=start_date,
        scenario_finish_date=finish_date,
        scenario_duration=duration,
        site_codes=site_codes,
        scenario_props=props,
    )


@home.route("/scenarios/<int:scenario_id>/edit")
def scenario_edit_get(scenario_id):
    scenario = Scenario.get_by_id(g.sess, scenario_id)
    return render_template("scenario_edit.html", scenario=scenario)


@home.route("/scenarios/<int:scenario_id>/edit", methods=["POST"])
def scenario_edit_post(scenario_id):
    try:
        scenario = Scenario.get_by_id(g.sess, scenario_id)
        name = req_str("name")
        properties = req_zish("properties")
        scenario.update(name, properties)
        g.sess.commit()
        return redirect(f"/scenarios/{scenario.id}", 303)
    except BadRequest as e:
        g.sess.rollback()
        description = e.description
        flash(description)
        return make_response(
            render_template("scenario_edit.html", scenario=scenario),
            400,
        )


@home.route("/scenarios/<int:scenario_id>/edit", methods=["DELETE"])
def scenario_edit_delete(scenario_id):
    try:
        scenario = Scenario.get_by_id(g.sess, scenario_id)
        scenario.delete(g.sess)
        g.sess.commit()
        return hx_redirect("/scenarios")
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template("scenario_edit.html", scenario=scenario), 400
        )


@home.route("/system")
def system_get():
    traces = []
    for thread_id, stack in sys._current_frames().items():
        traces.append(f"\n# ThreadID: {thread_id}")
        for filename, lineno, name, line in traceback.extract_stack(stack):
            traces.append(f'File: "{filename}", line {lineno}, in {name}')
            if line:
                traces.append(f"  {line.strip()}")
    pg_stats = g.sess.execute(text("select * from pg_stat_activity")).fetchall()

    pg_indexes = g.sess.execute(
        text(
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
        )
    ).fetchall()

    version_number = chellow.__version__

    return render_template(
        "system.html",
        traces="\n".join(traces),
        version_number=version_number,
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
        return redirect("/users/" + str(user.id), 303)
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
            return redirect("/users/" + str(user.id), 303)
        elif "delete" in request.values:
            g.sess.delete(user)
            g.sess.commit()
            return redirect("/users", 303)
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
            return redirect("/users/" + str(user.id), 303)
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
        return redirect(f"/general_imports/{proc_id}", 303)
    except BadRequest as e:
        flash(e.description)
        return render_template(
            "general_imports.html",
            process_ids=sorted(chellow.general_import.get_process_ids(), reverse=True),
        )


@home.route("/general_imports/<int:import_id>")
def general_import_get(import_id):
    try:
        importer = chellow.general_import.get_process(import_id)
        return render_template(
            "general_import.html", import_id=import_id, importer=importer
        )
    except BadRequest as e:
        flash(e.description)
        return render_template("general_import.html", import_id=import_id)


@home.route("/edi_viewer")
def edi_viewer_get():
    return render_template("edi_viewer.html")


@home.route("/edi_viewer", methods=["POST"])
def edi_viewer_post():
    segments = []
    file_name = None
    try:
        if "edi_file" in request.files:
            file_item = req_file("edi_file")
            edi_str = str(
                file_item.stream.read(), encoding="utf-8-sig", errors="ignore"
            )
            file_name = file_item.filename
        else:
            edi_str = req_str("edi_fragment")

        for line_number, line, segment_name, elements in parse_edi(edi_str):

            if segment_name == "CCD":
                segment_name = segment_name + elements["CCDE"][0]
                try:
                    seg = SEGMENTS[segment_name]
                except KeyError:
                    raise BadRequest(
                        f"The segment name {segment_name} is not recognized."
                    )
            else:
                try:
                    seg = SEGMENTS[segment_name]
                except KeyError:
                    raise BadRequest(
                        f"The segment name {segment_name} is not recognized."
                    )

            titles_element = []
            titles_component = []
            values = []
            elems = {el["code"]: el for el in seg["elements"]}
            if len(elements) > len(elems):
                raise BadRequest(
                    f"There are more elements than recognized for the segment "
                    f"{segment_name}. {line}"
                )
            for element_code, element in elements.items():
                elem = elems[element_code]
                comps = elem["components"]
                colspan = len(comps)
                titles_element.append(
                    {
                        "value": elem["description"],
                        "code": elem["code"],
                        "colspan": str(colspan),
                        "rowspan": "2" if colspan == 1 else "1",
                    }
                )
                if len(element) > len(comps):
                    raise BadRequest(
                        f"For the segment {segment_name} the number of components "
                        f"{element} is greater than the expected components {comps}. "
                        f"{line}"
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
                            raise BadRequest(f"Didn't recognize the type {typ}.")
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
                    "raw_line": line,
                }
            )

        return render_template(
            "edi_viewer.html", segments=segments, file_name=file_name
        )
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template("edi_viewer.html", segments=segments, file_name=file_name),
            400,
        )


@home.route("/sites/<int:site_id>/edit")
def site_edit_get(site_id):
    try:
        site = Site.get_by_id(g.sess, site_id)
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
            return redirect("/sites", 303)

        elif "update" in request.form:
            code = req_str("code")
            name = req_str("site_name")
            site.update(code, name)
            g.sess.commit()
            flash("Site updated successfully.")
            return redirect(f"/sites/{site.id}", 303)

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
            aq = req_decimal("aq")
            soq = req_decimal("soq")
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
                aq,
                soq,
            )
            g.sess.commit()
            return redirect(f"/g/supplies/{g_supply.id}", 303)
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
        return redirect(f"/sites/{site.id}", 303)
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
            return redirect(f"/sites/{sites[0].id}")
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
            return redirect(f"/e/supplies/{e_eras[0].supply.id}", 307)
        elif len(e_eras) == 0 and len(g_eras) == 1:
            return redirect(f"/g/supplies/{g_eras[0].g_supply.id}", 307)
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
    num_running = 0

    for fl in sorted(os.listdir(download_path), reverse=True):
        statinfo = os.stat(os.path.join(download_path, fl))
        fl_parts = fl.split("_")
        if fl_parts[1] == "RUNNING":
            num_running += 1
        files.append(
            {
                "name": fl,
                "last_modified": to_utc(Datetime.utcfromtimestamp(statinfo.st_mtime)),
                "size": statinfo.st_size,
            }
        )

    return render_template("downloads.html", files=files, num_running=num_running)


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


@home.route("/downloads/<fname>", methods=["DELETE"])
def download_delete(fname):
    head, name = os.path.split(os.path.normcase(os.path.normpath(fname)))

    download_path = os.path.join(current_app.instance_path, "downloads")
    full_name = os.path.join(download_path, name)
    os.remove(full_name)
    return hx_redirect("/downloads")


@home.route("/report_runs")
def report_runs_get():
    runs = g.sess.query(ReportRun).order_by(ReportRun.date_created.desc())
    importer = chellow.rrun.get_importer()

    return render_template("report_runs.html", runs=runs, importer=importer)


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
        ROW_LIMIT = 200
        rows = (
            q.order_by(
                func.abs(ReportRunRow.data["values"][order_by].as_float()).desc()
            )
            .limit(ROW_LIMIT)
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
            ROW_LIMIT=ROW_LIMIT,
        )
    elif run.name == "g_bill_check":
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
                t for t in titles if t.startswith("difference_") and t.endswith("_gbp")
            ]
            diff_selects = [
                func.sum(ReportRunRow.data["values"][t].as_float()) for t in diff_titles
            ]
            sum_diffs = (
                g.sess.query(*diff_selects).filter(ReportRunRow.report_run == run).one()
            )

            for t, sum_diff in zip(diff_titles, sum_diffs):
                elem = t[11:-4]
                sdiff = 0 if sum_diff is None else sum_diff
                if elem == "net":
                    summary["sum_difference"] = sdiff
                else:
                    elements.append((elem, sdiff))

            elements.sort(key=lambda x: abs(x[1]), reverse=True)
            elements.insert(0, ("net", summary["sum_difference"]))

        if "order_by" in request.values:
            order_by = req_str("order_by")
        else:
            order_by = "difference_net_gbp"

        g_contract = GContract.get_by_id(g.sess, run.data["g_contract_id"])
        g_contract_props = g_contract.make_properties()
        props = g_contract_props.get("report_run", {})
        sort_absolute = props.get("sort_absolute", True)
        show_elements = props.get("show_elements", True)
        columns = props.get("columns", [f"difference_{el[0]}_gbp" for el in elements])

        ROW_LIMIT = 200
        q = select(ReportRunRow).where(ReportRunRow.report_run == run).limit(ROW_LIMIT)
        if sort_absolute:
            q = q.order_by(
                func.abs(ReportRunRow.data["values"][order_by].as_float()).desc()
            )
        else:
            q = q.order_by(ReportRunRow.data["values"][order_by].as_float().desc())
        rows = g.sess.scalars(q).all()
        return render_template(
            "report_run_g_bill_check.html",
            run=run,
            rows=rows,
            summary=summary,
            elements=elements,
            order_by=order_by,
            ROW_LIMIT=ROW_LIMIT,
            sort_absolute=sort_absolute,
            show_elements=show_elements,
            columns=columns,
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
    elif run.name == "monthly_duration":
        org_rows = (
            g.sess.execute(
                select(ReportRunRow)
                .filter(ReportRunRow.report_run == run, ReportRunRow.tab == "org")
                .order_by(ReportRunRow.data["values"]["month"])
            )
            .scalars()
            .all()
        )
        return render_template(
            "report_run_monthly_duration_org.html",
            run=run,
            org_rows=org_rows,
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
    elif run.name == "missing_e_bills":
        rows = g.sess.scalars(
            select(ReportRunRow)
            .filter(ReportRunRow.report_run == run)
            .order_by(
                ReportRunRow.data["values"]["month_start"],
            )
        ).all()
        return render_template(
            "report_run_missing_e_bills.html",
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


@home.route("/report_runs/<int:run_id>", methods=["DELETE"])
def report_run_delete(run_id):
    run = g.sess.query(ReportRun).filter(ReportRun.id == run_id).one()
    run.delete(g.sess)
    g.sess.commit()
    return hx_redirect("/report_runs", 303)


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
    output.headers["Content-Disposition"] = f'attachment; filename="{run.title}.csv"'
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
                name = "-".join(toks[1:-1])
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
    elif row.report_run.name == "g_bill_check":
        g_contract = GContract.get_by_id(g.sess, row.report_run.data["g_contract_id"])
        g_contract_props = g_contract.make_properties()
        props = g_contract_props.get("report_run", {})
        table_names_hide = props.get("table_names_hide", [])

        values = row.data["values"]
        elements = {}
        for t in row.data["values"].keys():

            if (
                t.startswith("covered_")
                or t.startswith("virtual_")
                or t.startswith("difference_")
            ) and t.endswith("_gbp"):
                toks = t.split("_")
                name = "_".join(toks[1:-1])
                if name in ("vat", "gross", "net") or name in table_names_hide:
                    continue
                try:
                    table = elements[name]
                except KeyError:
                    table = elements[name] = {"order": 0, "name": name, "parts": set()}
                    tables.append(table)

        for t in row.data["values"].keys():

            toks = t.split("_")
            if toks[0] in ("covered", "virtual", "difference"):
                tail = "_".join(toks[1:])
                for element in elements.keys():
                    table = elements[element]
                    elstr = f"{element}_"
                    if tail.startswith(elstr):
                        part = tail[len(elstr) :]
                        if part != "gbp":
                            table["parts"].add(part)
                        if t.startswith("difference_") and t.endswith("_gbp"):
                            table["order"] = abs(values[t])

        tables.sort(key=lambda t: t["order"], reverse=True)
        return render_template(
            "report_run_row_g_bill_check.html",
            row=row,
            raw_data=raw_data,
            tables=tables,
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

    return redirect(f"/report_run_rows/{row_id}", 303)


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
        .filter(SiteEra.site == site, not_(Source.code.in_(("sub", "gen-grid"))))
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
            return redirect("/non_core_contracts", 303)
        if "update_state" in request.values:
            state = req_zish("state")
            contract.update_state(state)
            g.sess.commit()
            return redirect(f"/non_core_contracts/{contract.id}", 303)
        else:
            properties = req_zish("properties")
            contract.update_properties(properties)
            g.sess.commit()
            return redirect(f"/non_core_contracts/{contract.id}", 303)
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

    typs = (
        "imp_grid",
        "imp_3p",
        "exp_grid",
        "exp_3p",
        "used",
        "displaced",
        "imp_gen",
        "exp_gen",
    )

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


@home.route("/national_grid")
def national_grid_get():
    importer = chellow.national_grid.importer
    config = Contract.get_non_core_by_name(g.sess, "configuration")
    props = config.make_properties()
    now_ct = ct_datetime_now()
    fy_year = now_ct.year if now_ct.month > 3 else now_ct.year - 1
    fy_start = to_utc(ct_datetime(fy_year, 4, 1))
    tnuos_rs = g.sess.execute(
        select(RateScript)
        .join(RateScript.contract)
        .join(MarketRole)
        .where(
            MarketRole.code == "Z",
            RateScript.start_date >= fy_start,
            Contract.name == "tnuos",
        )
        .order_by(RateScript.start_date.desc())
    ).scalars()

    return render_template(
        "national_grid.html",
        importer=importer,
        config_state=config.make_state(),
        config_properties=props.get("rate_server", {}),
        tnuos_rs=tnuos_rs,
    )


@home.route("/national_grid", methods=["POST"])
def national_grid_post():
    importer = chellow.national_grid.importer
    importer.go()
    return redirect("/national_grid", 303)


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
        return redirect(f"/non_core_rate_scripts/{rate_script.id}", 303)
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
            return redirect(f"/non_core_contracts/{contract.id}", 303)
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
            return redirect(f"/non_core_rate_scripts/{rate_script.id}", 303)
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
        return redirect(f"/non_core_contracts/{contract.id}/auto_importer", 303)
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
    config = Contract.get_non_core_by_name(g.sess, "configuration")
    props = config.make_properties()
    now_ct = ct_datetime_now()
    fy_year = now_ct.year if now_ct.month > 3 else now_ct.year - 1
    fy_start = to_utc(ct_datetime(fy_year, 4, 1))
    dno_rs = g.sess.execute(
        select(RateScript)
        .join(RateScript.contract)
        .join(MarketRole)
        .where(MarketRole.code == "R", RateScript.start_date >= fy_start)
        .order_by(Contract.name, RateScript.start_date.desc())
    ).scalars()
    nts_rs = g.sess.execute(
        select(GRateScript)
        .join(GRateScript.g_contract)
        .where(
            GContract.is_industry == true(),
            GRateScript.start_date >= fy_start,
            GContract.name == "nts_commodity",
        )
        .order_by(GRateScript.start_date.desc())
    ).scalars()
    dn_rs = g.sess.execute(
        select(GRateScript)
        .join(GRateScript.g_contract)
        .where(
            GContract.is_industry == true(),
            GRateScript.start_date >= fy_start,
            GContract.name == "dn",
        )
        .order_by(GRateScript.start_date.desc())
    ).scalars()
    bsuos_rs = g.sess.execute(
        select(RateScript)
        .join(RateScript.contract)
        .join(MarketRole)
        .where(
            MarketRole.code == "Z",
            RateScript.start_date >= fy_start,
            Contract.name == "bsuos",
        )
        .order_by(RateScript.start_date.desc())
    ).scalars()
    ccl_rs = g.sess.execute(
        select(RateScript)
        .join(RateScript.contract)
        .join(MarketRole)
        .where(
            MarketRole.code == "Z",
            RateScript.start_date >= fy_start,
            Contract.name == "ccl",
        )
        .order_by(RateScript.start_date.desc())
    ).scalars()
    triad_dates_rs = g.sess.execute(
        select(RateScript)
        .join(RateScript.contract)
        .join(MarketRole)
        .where(
            MarketRole.code == "Z",
            RateScript.start_date >= fy_start,
            Contract.name == "triad_dates",
        )
        .order_by(RateScript.start_date.desc())
    ).scalars()
    gas_ccl_rs = g.sess.execute(
        select(GRateScript)
        .join(GRateScript.g_contract)
        .where(
            GContract.is_industry == true(),
            GRateScript.start_date >= fy_start,
            GContract.name == "ccl",
        )
        .order_by(GRateScript.start_date.desc())
    ).scalars()

    return render_template(
        "rate_server.html",
        importer=importer,
        config_state=config.make_state(),
        config_properties=props.get("rate_server", {}),
        dno_rs=dno_rs,
        nts_rs=nts_rs,
        dn_rs=dn_rs,
        bsuos_rs=bsuos_rs,
        triad_dates_rs=triad_dates_rs,
        gas_ccl_rs=gas_ccl_rs,
        ccl_rs=ccl_rs,
    )


@home.route("/rate_server", methods=["POST"])
def rate_server_post():
    importer = chellow.rate_server.importer
    importer.go()
    return redirect("/rate_server", 303)


@home.route("/tester")
def tester_get():
    tester = chellow.testing.tester
    return render_template("tester.html", tester=tester)


@home.route("/tester", methods=["POST"])
def tester_post():
    tester = chellow.testing.tester
    tester.go()
    return redirect("/tester", 303)


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
            if imp_related and source_code in ("grid", "gen-grid"):
                to_adds.append(("imp", "pos"))
            if not imp_related and source_code in ("grid", "gen-grid"):
                to_adds.append(("exp", "pos"))
            if (imp_related and source_code == "gen") or (
                not imp_related and source_code == "gen-grid"
            ):
                to_adds.append(("gen", "pos"))
            if (not imp_related and source_code == "gen") or (
                imp_related and source_code == "gen-grid"
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
        "text": f"Electricity at site {site.code} {site.name} for {months} "
        f" month{'s' if months > 1 else ''} up to and including "
        f"{(to_ct(finish_date) - HH).strftime('%B %Y')}",
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


@home.route("/input_date", methods=["GET"])
def input_date_get():
    prefix = req_str("prefix")
    year_name = f"{prefix}_year"
    month_name = f"{prefix}_month"
    day_name = f"{prefix}_day"
    hour_name = f"{prefix}_hour"
    minute_name = f"{prefix}_minute"

    resolution = req_str("resolution")

    year = req_int_none(year_name)
    if year is None:
        initial = ct_datetime_now()
        year, month, day, hour, minute = (
            initial.year,
            initial.month,
            initial.day,
            initial.hour,
            initial.minute,
        )
    else:
        month = req_int(month_name)
        if resolution in ("day", "hour", "minute"):
            day = req_int(day_name)
        else:
            day = 1

        if resolution in ("hour", "minute"):
            hour = req_int(hour_name)
        else:
            hour = 0

        if resolution == "minute":
            minute = req_int(hour_name)
        else:
            minute = 0

    month_max_day = (ct_datetime(year, month, 1) + relativedelta(months=1) - HH).day

    initial = to_utc(ct_datetime(year, month, min(day, month_max_day), hour, minute))

    return render_template(
        "input_date.html",
        initial=initial,
        resolution=resolution,
        prefix=prefix,
        year_name=year_name,
        month_name=month_name,
        day_name=day_name,
        hour_name=hour_name,
        minute_name=minute_name,
        month_max_day=month_max_day,
    )
