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
from collections import OrderedDict, defaultdict
from datetime import datetime as Datetime
from importlib import import_module
from io import DEFAULT_BUFFER_SIZE, StringIO
from itertools import chain, islice
from operator import itemgetter
from random import choice
from xml.dom import Node

import chellow.bank_holidays
import chellow.bill_importer
import chellow.bsuos
import chellow.computer
import chellow.dloads
import chellow.edi_lib
import chellow.g_bill_import
import chellow.g_cv
import chellow.general_import
import chellow.hh_importer
import chellow.rcrc
import chellow.system_price
import chellow.tlms
from chellow.e_views import get_era_bundles
from chellow.models import (
    Batch, BatchFile, Bill, BillType, Channel, ClockInterval, Contract, Cop,
    Era, GBatch, GBill, GContract, GDn, GEra, GExitZone, GLdz, GRateScript,
    GReadType, GReadingFrequency, GRegisterRead, GSupply, GUnit, GeneratorType,
    GspGroup, HhDatum, Llfc, METER_TYPES, MarketRole, MeasurementRequirement,
    MeterPaymentType, MeterType, Mtc, Participant, Party, Pc, RateScript,
    ReadType, RegisterRead, Report, ReportRun, ReportRunRow, Scenario, Session,
    Site, SiteEra, SiteGEra, Snag, Source, Ssc, Supply, Tpr, User, UserRole,
    VoltageLevel, db_upgrade
)
from chellow.utils import (
    HH, PropDict, c_months_u, csv_make_val, ct_datetime_now, get_file_scripts,
    hh_after, hh_format, hh_max, hh_min, hh_range, parse_mpan_core, req_bool,
    req_date, req_decimal, req_file, req_hh_date, req_int, req_str, req_zish,
    send_response, to_ct, to_utc, utc_datetime, utc_datetime_now
)

from dateutil.relativedelta import relativedelta

from flask import (
    Blueprint, Flask, Response, current_app, flash, g, jsonify, make_response,
    redirect, render_template, request, send_file)

import psutil

from pympler import muppy, summary

from sqlalchemy import (
    Float, case, cast, false, func, not_, null, or_, text, true)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from werkzeug.exceptions import BadRequest, NotFound

from zish import dumps, loads


app = Flask('chellow', instance_relative_config=True)
app.secret_key = os.urandom(24)


@app.before_first_request
def before_first_request():
    db_upgrade(app.root_path)
    chellow.rcrc.startup()
    chellow.bsuos.startup()
    chellow.system_price.startup()
    chellow.hh_importer.startup()
    chellow.tlms.startup()
    chellow.bank_holidays.startup()
    chellow.dloads.startup(app.instance_path)
    chellow.g_cv.startup()
    chellow.utils.root_path = app.root_path

    try:
        scheme = request.headers['X-Forwarded-Proto']
    except KeyError:
        sess = Session()
        try:
            config_contract = Contract.get_non_core_by_name(
                sess, 'configuration')
            props = config_contract.make_properties()
            scheme = props.get('redirect_scheme', 'http')
        finally:
            sess.close()

    try:
        host = request.headers['X-Forwarded-Host']
    except KeyError:
        host = request.host

    chellow.utils.url_root = scheme + '://' + host + '/'


@app.before_request
def before_request():
    g.sess = Session()

    print(
        ' '.join(
            '-' if v is None else v for v in (
                request.remote_addr, str(request.user_agent),
                request.remote_user,
                '[' + Datetime.now().strftime('%d/%b/%Y:%H:%M:%S') + ']',
                '"' + request.method + ' ' + request.path + ' ' +
                request.environ.get('SERVER_PROTOCOL') + '"', None, None)))


@app.teardown_appcontext
def shutdown_session(exception=None):
    if getattr(g, 'sess', None) is not None:
        g.sess.close()


@app.context_processor
def chellow_context_processor():
    global_alerts = []
    for task in chellow.hh_importer.tasks.values():
        if task.is_error:
            try:
                contract = Contract.get_by_id(g.sess, task.contract_id)
                global_alerts.append(
                    "There's a problem with the automatic HH data importer "
                    "for contract '" + str(contract.name) + "'.")
            except NotFound:
                pass

    for importer in (
            chellow.bsuos.bsuos_importer, chellow.g_cv.g_cv_importer):
        if importer is not None and importer.global_alert is not None:
            global_alerts.append(importer.global_alert)

    return {'current_user': g.user, 'global_alerts': global_alerts}


TEMPLATE_FORMATS = {
    'year': '%Y', 'month': '%m', 'day': '%d', 'hour': '%H',
    'minute': '%M', 'full': '%Y-%m-%d %H:%M', 'date': '%Y-%m-%d'}


views = Blueprint('', __name__, template_folder='templates')


def chellow_redirect(path, code=None):
    try:
        scheme = request.headers['X-Forwarded-Proto']
    except KeyError:
        config_contract = Contract.get_non_core_by_name(
            g.sess, 'configuration')
        props = config_contract.make_properties()
        scheme = props.get('redirect_scheme', 'http')

    try:
        host = request.headers['X-Forwarded-Host']
    except KeyError:
        host = request.host

    location = scheme + '://' + host + path
    if code is None:
        return redirect(location)
    else:
        return redirect(location, code)


@views.route('/nationalgrid/<fname>', methods=['GET', 'POST'])
def nationalgrid(fname):
    filename = os.path.join(os.path.dirname(__file__), 'nationalgrid', fname)
    return send_file(
        filename, mimetype='application/binary', as_attachment=True,
        attachment_filename=fname)


ELEXON_LOOKUP = {
    'BESTVIEWPRICES_FILE': ('application/binary', 'prices.xls'),
    'RCRC_FILE': ('text/csv', 'rcrc.csv'),
    'TLM_FILE': ('text/csv', 'tlm.csv')}


@views.route('/elexonportal/file/download/<path:fname>')
def elexonportal(fname):
    key = request.args['key']
    if key != 'xxx':
        raise Exception("The key should be 'xxx'")
    mimetype, filename = ELEXON_LOOKUP[fname]

    fname = os.path.join(os.path.dirname(__file__), 'elexonportal', filename)
    return send_file(
        fname, mimetype=mimetype, as_attachment=True,
        attachment_filename=filename)


@views.route('/ecoes')
def ecoes_get():
    return 'ecoes_get'


@views.route('/ecoes', methods=['POST'])
def ecoes_post():
    return 'ecoes_post'


@views.route('/hh_api')
def hh_api():
    return jsonify(
        {
            'DataPoints': [
                {
                    'Flags': 0,
                    'Time': 636188256000000000,
                    'Value': 21}]})


@views.route('/chellowcss', methods=['GET'])
def chellowcss_get():
    props = Contract.get_non_core_by_name(g.sess, 'configuration'). \
        make_properties()
    response = make_response(
        render_template(
            'css/chellow.css', background_colour=props['background_colour']))
    response.headers['Content-type'] = 'text/css'
    return response


@views.route('/chellowjs', methods=['GET'])
def chellowjs_get():
    response = make_response(
        render_template(
            'js/chellow.js'))
    response.headers['Content-type'] = 'text/javascript'
    return response


@views.route(
    '/ecoes/NonDomesticCustomer/ExportPortfolioMPANs', methods=['GET'])
def ecoes_mpans_get():
    return Response(
        ','.join(
            (
                'MPAN', 'AddressLine1', 'AddressLine2', 'AddressLine3',
                'AddressLine4', 'AddressLine5', 'AddressLine6', 'AddressLine7',
                'AddressLine8', 'AddressLine9', 'PostCode', 'Current Supplier',
                'Registration Effective From Date', 'Meter Timeswitch Class',
                'Meter Timeswitch Class Effective From Date',
                'Line Loss Factor', 'Line Loss Factor Effective From Date',
                'Profile Class', 'Standard Settlement Configuration',
                'Measurement Class', 'Energisation Status', 'Data Aggregator',
                'Data Collector', 'Meter Operator',
                'Meter Operator Effective From Date', 'GSP Group',
                'GSP Group Effective From Date', 'Distributor',
                'Meter Serial Number', 'Meter Installation Date', 'Meter Type',
                'Meter Asset Provider')), mimetype='text/csv')


@views.route('/health')
def health():
    return Response('healthy\n', mimetype='text/plain')


@views.route('/local_reports/<int:report_id>/output', methods=['GET', 'POST'])
def local_report_output_post(report_id):
    report = g.sess.query(Report).get(report_id)
    try:
        ns = {
            'report_id': report_id,
            'template': report.template}
        exec(report.script, ns)
        return ns['response']
    except BaseException:
        return Response(traceback.format_exc(), status=500)


@views.route('/local_reports', methods=['GET'])
def local_reports_get():
    reports = g.sess.query(Report).order_by(Report.id, Report.name).all()
    return render_template('local_reports.html', reports=reports)


@views.route('/local_reports', methods=['POST'])
def local_reports_post():
    name = req_str("name")
    report = Report(name, "", None)
    g.sess.add(report)
    try:
        g.sess.commit()
    except IntegrityError as e:
        if 'duplicate key value violates unique constraint' in str(e):
            return Response(
                "There's already a report with that name.", status=400)
        else:
            raise
    return chellow_redirect('/local_reports/' + str(report.id), 303)


@views.route('/local_reports/<int:report_id>')
def local_report_get(report_id):
    report = Report.get_by_id(g.sess, report_id)
    return render_template('local_report.html', report=report)


@views.route('/local_reports/<int:report_id>', methods=['POST'])
def local_report_post(report_id):
    report = Report.get_by_id(g.sess, report_id)
    name = req_str("name")
    script = req_str("script")
    template = req_str("template")
    report.update(name, script, template)
    try:
        g.sess.commit()
    except BadRequest as e:
        if 'duplicate key value violates unique constraint' in str(e):
            return Response(
                "There's already a report with that name.", status=400)
        else:
            raise
    return chellow_redirect('/local_reports/' + str(report.id), 303)


@views.route('/system')
def system_get():
    traces = []
    for thread_id, stack in sys._current_frames().items():
        traces.append("\n# ThreadID: %s" % thread_id)
        for filename, lineno, name, line in traceback.extract_stack(stack):
            traces.append(
                'File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                traces.append("  %s" % (line.strip()))
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
        """).fetchall()

    return render_template(
        'system.html', traces='\n'.join(traces),
        version_number=chellow.versions['version'],
        version_hash=chellow.versions['full-revisionid'], pg_stats=pg_stats,
        request=request, virtual_memory=psutil.virtual_memory(),
        swap_memory=psutil.swap_memory(),
        python_version=platform.python_version(), pg_indexes=pg_indexes)


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
                desc = 'length: ' + str(len(o))
            else:
                desc = ''
            ls.append('(' + ', '.join([str(type(o)), desc]) + ')')
        return 'length: ' + str(len(obj)) + ' [' + ', '.join(ls)
    elif isinstance(obj, tuple):
        ls = []
        for o in obj[:10]:
            if isinstance(o, (int, float)):
                desc = repr(o)
            elif isinstance(o, str):
                desc = repr(o[:100])
            elif isinstance(o, (list, dict)):
                desc = 'length: ' + str(len(o))
            else:
                desc = ''
            ls.append('(' + ', '.join([str(type(o)), desc]) + ')')
        return 'length: ' + str(len(obj)) + ' (' + ', '.join(ls)
    elif isinstance(obj, dict):
        ls = []
        for k, v in islice(obj.items(), 10):
            if isinstance(v, (int, float)):
                desc = repr(v)
            elif isinstance(v, str):
                desc = repr(v[:100])
            elif isinstance(v, (list, dict)):
                desc = 'length: ' + str(len(v))
            else:
                desc = str(type(v))
            ls.append(str(k) + ': ' + desc)
        return 'length: ' + str(len(obj)) + ' {' + ', '.join(ls)
    elif isinstance(obj, types.CodeType):
        return obj.co_filename
    elif isinstance(obj, types.FunctionType):
        return obj.__name__
    elif isinstance(obj, types.FrameType):
        return obj.f_code.co_filename + ' ' + str(obj.f_lineno)
    elif isinstance(obj, types.MethodType):
        return obj.__name__
    elif isinstance(obj, types.ModuleType):
        return obj.__name__
    elif isinstance(obj, Node):
        parent_node = obj.parentNode
        if parent_node is None:
            id_str = 'None'
        else:
            id_str = str(id(parent_node))
        return 'parent: ' + id_str
    else:
        return ''


def get_path(node):
    path = [node]
    parent = node['parent']
    while parent is not None:
        path.append(parent)
        parent = parent['parent']
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


@views.route('/system/chains')
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
    return render_template('chain.html', paths=paths, unreachable=unreachable)


@views.route('/system/object_summary')
def object_summary_get():
    sumry = summary.summarize(muppy.get_objects())
    sumry_text = '\n'.join(
        summary.format_(sumry, sort='size', order='descending'))
    return render_template('object_summary.html', summary=sumry_text)


@views.route('/')
def home_get():
    config = Contract.get_non_core_by_name(g.sess, 'configuration')
    now = utc_datetime_now()
    month_start = Datetime(now.year, now.month, 1) - \
        relativedelta(months=1)
    month_finish = Datetime(now.year, now.month, 1) - HH

    return render_template(
        'home.html', properties=config.make_properties(),
        month_start=month_start, month_finish=month_finish)


@views.route('/local_reports_home')
def local_reports_home():
    config = Contract.get_non_core_by_name(g.sess, 'configuration')
    properties = config.make_properties()
    report_id = properties['local_reports_id']
    return local_report_output_post(report_id)


@views.errorhandler(500)
def error_500(error):
    return traceback.format_exc(), 500


@views.errorhandler(RuntimeError)
def error_runtime(error):
    return "called rtime handler " + str(error), 500


@views.route('/cops')
def cops_get():
    cops = g.sess.query(Cop).order_by(Cop.code)
    return render_template('cops.html', cops=cops)


@views.route('/cops/<int:cop_id>')
def cop_get(cop_id):
    cop = Cop.get_by_id(g.sess, cop_id)
    return render_template('cop.html', cop=cop)


@views.route('/read_types')
def read_types_get():
    read_types = g.sess.query(ReadType).order_by(ReadType.code)
    return render_template('read_types.html', read_types=read_types)


@views.route('/read_types/<int:read_type_id>')
def read_type_get(read_type_id):
    read_type = ReadType.get_by_id(g.sess, read_type_id)
    return render_template('read_type.html', read_type=read_type)


@views.route('/sources')
def sources_get():
    sources = g.sess.query(Source).order_by(Source.code)
    return render_template('sources.html', sources=sources)


@views.route('/sources/<int:source_id>')
def source_get(source_id):
    source = Source.get_by_id(g.sess, source_id)
    return render_template('source.html', source=source)


@views.route('/meter_types')
def meter_types_get():
    meter_types = g.sess.query(MeterType).order_by(MeterType.code)
    return render_template('meter_types.html', meter_types=meter_types)


@views.route('/meter_types/<int:meter_type_id>')
def meter_type_get(meter_type_id):
    meter_type = MeterType.get_by_id(g.sess, meter_type_id)
    return render_template('meter_type.html', meter_type=meter_type)


@views.route('/generator_types')
def generator_types_get():
    generator_types = g.sess.query(GeneratorType).order_by(GeneratorType.code)
    return render_template(
        'generator_types.html', generator_types=generator_types)


@views.route('/generator_types/<int:generator_type_id>')
def generator_type_get(generator_type_id):
    generator_type = GeneratorType.get_by_id(g.sess, generator_type_id)
    return render_template(
        'generator_type.html', generator_type=generator_type)


@views.route('/bill_types')
def bill_types_get():
    bill_types = g.sess.query(BillType).order_by(BillType.code)
    return render_template('bill_types.html', bill_types=bill_types)


@views.route('/users', methods=['GET'])
def users_get():
    users = g.sess.query(User).order_by(User.email_address).all()
    parties = g.sess.query(Party).join(MarketRole).join(Participant).order_by(
        MarketRole.code, Participant.code).all()

    config_contract = Contract.get_non_core_by_name(g.sess, 'configuration')
    props = config_contract.make_properties()
    ad_props = props.get('ad_authentication', {})
    ad_auth_on = ad_props.get('on', False)
    return render_template(
        'users.html', users=users, parties=parties, ad_auth_on=ad_auth_on)


@views.route('/users', methods=['POST'])
def users_post():
    email_address = req_str('email_address')

    config_contract = Contract.get_non_core_by_name(g.sess, 'configuration')
    props = config_contract.make_properties()
    ad_props = props.get('ad_authentication', {})
    ad_auth_on = ad_props.get('on', False)

    if ad_auth_on:
        password = ''
    else:
        password = req_str('password')
    user_role_code = req_str('user_role_code')
    role = UserRole.get_by_code(g.sess, user_role_code)
    try:
        party = None
        if role.code == 'party-viewer':
            party_id = req_int('party_id')
            party = g.sess.query(Party).get(party_id)
        user = User.insert(g.sess, email_address, password, role, party)
        g.sess.commit()
        return chellow_redirect('/users/' + str(user.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        users = g.sess.query(User).order_by(User.email_address).all()
        parties = g.sess.query(Party).join(MarketRole).join(Participant). \
            order_by(MarketRole.code, Participant.code).all()
        return make_response(
            render_template(
                'users.html', users=users, parties=parties,
                ad_auth_on=ad_auth_on), 400)


@views.route('/users/<int:user_id>', methods=['POST'])
def user_post(user_id):
    try:
        user = User.get_by_id(g.sess, user_id)
        if 'current_password' in request.values:
            current_password = req_str('current_password')
            new_password = req_str('new_password')
            confirm_new_password = req_str('confirm_new_password')
            if not user.password_matches(current_password):
                raise BadRequest("The current password is incorrect.")
            if new_password != confirm_new_password:
                raise BadRequest("The new passwords aren't the same.")
            if len(new_password) < 6:
                raise BadRequest(
                    "The password must be at least 6 characters long.")
            user.set_password(new_password)
            g.sess.commit()
            return chellow_redirect('/users/' + str(user.id), 303)
        elif 'delete' in request.values:
            g.sess.delete(user)
            g.sess.commit()
            return chellow_redirect('/users', 303)
        else:
            email_address = req_str('email_address')
            user_role_code = req_str('user_role_code')
            user_role = UserRole.get_by_code(g.sess, user_role_code)
            party = None
            if user_role.code == 'party-viewer':
                party_id = req_int('party_id')
                party = Party.get_by_id(g.sess, party_id)
            user.update(email_address, user_role, party)
            g.sess.commit()
            return chellow_redirect('/users/' + str(user.id), 303)
    except BadRequest as e:
        flash(e.description)
        parties = g.sess.query(Party).join(MarketRole).join(Participant). \
            order_by(MarketRole.code, Participant.code)
        config_contract = Contract.get_non_core_by_name(
            g.sess, 'configuration')
        props = config_contract.make_properties()
        ad_props = props.get('ad_authentication', {})
        ad_auth_on = ad_props.get('on', False)
        return make_response(
            render_template(
                'user.html',  parties=parties, user=user,
                ad_auth_on=ad_auth_on), 400)


@views.route('/users/<int:user_id>')
def user_get(user_id):
    parties = g.sess.query(Party).join(MarketRole).join(Participant).order_by(
        MarketRole.code, Participant.code)
    user = User.get_by_id(g.sess, user_id)
    config_contract = Contract.get_non_core_by_name(g.sess, 'configuration')
    props = config_contract.make_properties()
    ad_props = props.get('ad_authentication', {})
    ad_auth_on = ad_props.get('on', False)
    return render_template(
        'user.html', parties=parties, user=user, ad_auth_on=ad_auth_on)


@views.route('/general_imports')
def general_imports_get():
    return render_template(
        'general_imports.html',
        process_ids=sorted(
            chellow.general_import.get_process_ids(), reverse=True))


@views.route('/general_imports', methods=['POST'])
def general_imports_post():
    try:
        file_item = request.files["import_file"]
        file_name = file_item.filename
        if not file_name.endswith('.csv'):
            raise BadRequest(
                "The file name should have the extension '.csv'.")
        f = StringIO(
            str(
                file_item.stream.read(), encoding='utf-8-sig',
                errors='ignore'))
        f.seek(0)
        proc_id = chellow.general_import.start_process(f)
        return chellow_redirect('/general_imports/' + str(proc_id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template(
            'general_imports.html',
            process_ids=sorted(
                chellow.general_import.get_process_ids(), reverse=True))


@views.route('/general_imports/<int:import_id>')
def general_import_get(import_id):
    try:
        proc = chellow.general_import.get_process(import_id)
        fields = proc.get_fields()
        fields['is_alive'] = proc.isAlive()
        fields['process_id'] = import_id
        return render_template('general_import.html', **fields)
    except BadRequest as e:
        flash(e.description)
        return render_template('general_import.html', process_id=import_id)


@views.route('/edi_viewer')
def edi_viewer_get():
    return render_template('edi_viewer.html')


@views.route('/edi_viewer', methods=['POST'])
def edi_viewer_post():
    segments = []
    try:
        file_item = request.files["edi_file"]
        file_name = file_item.filename
        f = StringIO(
            str(
                file_item.stream.read(), encoding='utf-8-sig',
                errors='ignore'))
        f.seek(0)
        parser = chellow.edi_lib.EdiParser(f)
        for segment_name in parser:
            elements = parser.elements

            if segment_name == 'CCD':
                segment_name = segment_name + elements[1][0]
                try:
                    seg = chellow.edi_lib.SEGMENTS[segment_name]
                except KeyError:
                    raise BadRequest(
                        "The segment name " + segment_name +
                        " is not recognized.")
            else:
                try:
                    seg = chellow.edi_lib.SEGMENTS[segment_name]
                except KeyError:
                    raise BadRequest(
                        "The segment name " + segment_name +
                        " is not recognized.")

            titles_element = []
            titles_component = []
            values = []
            elems = seg['elements']
            if len(elements) > len(elems):
                raise BadRequest(
                    "There are more elements than recognized for the "
                    "segment " + segment_name + ".")
            for element, elem in zip(elements, elems):
                comps = elem['components']
                colspan = len(comps)
                titles_element.append(
                    {
                        'value': elem['description'],
                        'colspan': str(colspan),
                        'rowspan': '2' if colspan == 1 else '1'
                    }
                )
                if len(element) > len(comps):
                    raise BadRequest(
                        "There are more components than recognized for the "
                        "segment " + segment_name + " and element " +
                        str(element) + ".")

                for i, (title, typ) in enumerate(comps):
                    if colspan > 1:
                        titles_component.append(title)
                    try:
                        component = element[i]

                        if typ == 'X':
                            value = component
                        elif typ == 'date':
                            d = component
                            if len(d) > 0:
                                value = '-'.join((d[:2], d[2:4], d[4:]))
                            else:
                                value = d
                        elif typ == 'time':
                            t = component
                            if len(t) > 0:
                                value = ':'.join((t[:2], t[2:4], t[4:]))
                            else:
                                value = t
                        else:
                            raise BadRequest(
                                "Didn't recognize the type " + typ + ".")
                    except IndexError:
                        value = ''

                    values.append(value)

            segments.append(
                {
                    'name': segment_name,
                    'description': seg['description'],
                    'titles_element': titles_element,
                    'titles_component': titles_component,
                    'vals': values,
                    'raw_line': parser.line
                }
            )

        return render_template(
            'edi_viewer.html', segments=segments, file_name=file_name)
    except BadRequest as e:
        flash(e.description)
        return render_template(
            'edi_viewer.html', segments=segments, file_name=file_name)


@views.route('/sites/<int:site_id>/edit')
def site_edit_get(site_id):
    try:
        site = Site.get_by_id(g.sess, site_id)
        sources = g.sess.query(Source).order_by(Source.code)
        generator_types = g.sess.query(GeneratorType). \
            order_by(GeneratorType.code)
        gsp_groups = g.sess.query(GspGroup).order_by(GspGroup.code)
        eras = g.sess.query(Era).join(SiteEra).filter(
            SiteEra.site == site).order_by(Era.start_date.desc())
        mop_contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == 'M').order_by(Contract.name)
        dc_contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code.in_(('C', 'D'))).order_by(Contract.name)
        supplier_contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == 'X').order_by(Contract.name)
        pcs = g.sess.query(Pc).order_by(Pc.code)
        cops = g.sess.query(Cop).order_by(Cop.code)
        g_contracts = g.sess.query(GContract).order_by(GContract.name)
        g_units = g.sess.query(GUnit).order_by(GUnit.code)
        g_exit_zones = g.sess.query(GExitZone).order_by(GExitZone.code)
        g_reading_frequencies = g.sess.query(GReadingFrequency).order_by(
            GReadingFrequency.code)
        return render_template(
            'site_edit.html', site=site, sources=sources,
            generator_types=generator_types, gsp_groups=gsp_groups, eras=eras,
            mop_contracts=mop_contracts, dc_contracts=dc_contracts,
            supplier_contracts=supplier_contracts, pcs=pcs, cops=cops,
            g_contracts=g_contracts, g_units=g_units,
            g_exit_zones=g_exit_zones,
            g_reading_frequencies=g_reading_frequencies)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return render_template(
            'site_edit.html', site=site, sources=sources,
            generator_types=generator_types, gsp_groups=gsp_groups, eras=eras,
            mop_contracts=mop_contracts, dc_contracts=dc_contracts,
            supplier_contracts=supplier_contracts, pcs=pcs, cops=cops,
            g_contracts=g_contracts, g_units=g_units,
            g_exit_zones=g_exit_zones,
            g_reading_frequencies=g_reading_frequencies)


@views.route('/sites/<int:site_id>/edit', methods=['POST'])
def site_edit_post(site_id):
    try:
        site = Site.get_by_id(g.sess, site_id)
        if 'delete' in request.form:
            site.delete(g.sess)
            g.sess.commit()
            flash("Site deleted successfully.")
            return chellow_redirect('/sites', 303)
        elif 'update' in request.form:
            code = req_str('code')
            name = req_str('site_name')
            site.update(code, name)
            g.sess.commit()
            flash("Site updated successfully.")
            return chellow_redirect('/sites/' + str(site.id), 303)
        elif 'insert_electricity' in request.form:
            name = req_str("name")
            source_id = req_int("source_id")
            source = Source.get_by_id(g.sess, source_id)
            gsp_group_id = req_int("gsp_group_id")
            gsp_group = GspGroup.get_by_id(g.sess, gsp_group_id)
            mop_contract_id = req_int("mop_contract_id")
            mop_contract = Contract.get_mop_by_id(g.sess, mop_contract_id)
            mop_account = req_str("mop_account")
            dc_contract_id = req_str("dc_contract_id")
            dc_contract = Contract.get_dc_by_id(g.sess, dc_contract_id)
            dc_account = req_str("dc_account")
            msn = req_str("msn")
            pc_id = req_int("pc_id")
            pc = Pc.get_by_id(g.sess, pc_id)
            mtc_code = req_str("mtc_code")
            cop_id = req_int("cop_id")
            cop = Cop.get_by_id(g.sess, cop_id)
            ssc_code = req_str("ssc_code")
            ssc_code = ssc_code.strip()
            if len(ssc_code) > 0:
                ssc = Ssc.get_by_code(g.sess, ssc_code)
            else:
                ssc = None
            properties = req_zish("properties")
            start_date = req_date("start")
            if 'generator_type_id' in request.form:
                generator_type_id = req_int("generator_type_id")
                generator_type = GeneratorType.get_by_id(
                    g.sess, generator_type_id)
            else:
                generator_type = None

            if 'imp_mpan_core' in request.form:
                imp_mpan_core_raw = req_str('imp_mpan_core')
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
                imp_supplier_contract_id = req_int(
                    "imp_supplier_contract_id")
                imp_supplier_contract = Contract.get_supplier_by_id(
                    g.sess, imp_supplier_contract_id)
                imp_supplier_account = req_str("imp_supplier_account")
                imp_sc = req_int('imp_sc')
                imp_llfc_code = req_str("imp_llfc_code")

            if 'exp_mpan_core' in request.form:
                exp_mpan_core_raw = req_str('exp_mpan_core')
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
                exp_supplier_contract_id = req_int(
                    "exp_supplier_contract_id")
                exp_supplier_contract = Contract.get_supplier_by_id(
                    g.sess, exp_supplier_contract_id)
                exp_supplier_account = req_str("exp_supplier_account")
                exp_sc = req_int('exp_sc')
                exp_llfc_code = req_str("exp_llfc_code")

            supply = site.insert_e_supply(
                g.sess, source, generator_type, name, start_date, None,
                gsp_group, mop_contract, mop_account, dc_contract, dc_account,
                msn, pc, mtc_code, cop, ssc, properties, imp_mpan_core,
                imp_llfc_code, imp_supplier_contract, imp_supplier_account,
                imp_sc, exp_mpan_core, exp_llfc_code, exp_supplier_contract,
                exp_supplier_account, exp_sc)
            g.sess.commit()
            return chellow_redirect("/supplies/" + str(supply.id), 303)
        elif 'insert_gas' in request.form:
            name = req_str('name')
            msn = req_str('msn')
            mprn = req_str('mprn')
            correction_factor = req_decimal('correction_factor')
            g_unit_id = req_int('g_unit_id')
            g_unit = GUnit.get_by_id(g.sess, g_unit_id)
            g_exit_zone_id = req_int('g_exit_zone_id')
            g_exit_zone = GExitZone.get_by_id(g.sess, g_exit_zone_id)
            g_contract_id = req_int('g_contract_id')
            g_contract = GContract.get_by_id(g.sess, g_contract_id)
            account = req_str('account')
            g_reading_frequency_id = req_int('g_reading_frequency_id')
            g_reading_frequency = GReadingFrequency.get_by_id(
                g.sess, g_reading_frequency_id)
            start_date = req_date('start')
            g_supply = site.insert_g_supply(
                g.sess, mprn, name, g_exit_zone, start_date, None, msn,
                correction_factor, g_unit, g_contract, account,
                g_reading_frequency)
            g.sess.commit()
            return chellow_redirect('/g_supplies/' + str(g_supply.id), 303)
        else:
            raise BadRequest(
                "The request must contain one of the following parameter "
                "names: delete, update, insert_electricity, insert_gas.")

    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        sources = g.sess.query(Source).order_by(Source.code)
        generator_types = g.sess.query(GeneratorType).order_by(
            GeneratorType.code)
        gsp_groups = g.sess.query(GspGroup).order_by(GspGroup.code)
        eras = g.sess.query(Era).join(SiteEra).filter(
            SiteEra.site == site).order_by(Era.start_date.desc())
        mop_contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == 'M').order_by(Contract.name)
        dc_contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code.in_(('C', 'D'))).order_by(Contract.name)
        supplier_contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == 'X').order_by(Contract.name)
        pcs = g.sess.query(Pc).order_by(Pc.code)
        cops = g.sess.query(Cop).order_by(Cop.code)
        g_contracts = g.sess.query(GContract).order_by(GContract.name)
        g_units = g.sess.query(GUnit).order_by(GUnit.code)
        g_exit_zones = g.sess.query(GExitZone).order_by(GExitZone.code)
        g_reading_frequencies = g.sess.query(GReadingFrequency).order_by(
            GReadingFrequency.code)
        return make_response(
            render_template(
                'site_edit.html', site=site, sources=sources,
                generator_types=generator_types, gsp_groups=gsp_groups,
                eras=eras, mop_contracts=mop_contracts,
                dc_contracts=dc_contracts,
                supplier_contracts=supplier_contracts, pcs=pcs, cops=cops,
                g_contracts=g_contracts, g_units=g_units,
                g_exit_zones=g_exit_zones,
                g_reading_frequencies=g_reading_frequencies), 400)


@views.route('/sites/add', methods=['POST'])
def site_add_post():
    try:
        code = req_str("code")
        name = req_str("name")
        site = Site.insert(g.sess, code, name)
        g.sess.commit()
        return chellow_redirect("/sites/" + str(site.id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template('site_add.html')


@views.route('/sites/add')
def site_add_get():
    return render_template('site_add.html')


@views.route('/sites')
def sites_get():
    LIMIT = 50
    if 'pattern' in request.values:
        pattern = req_str("pattern")
        sites = g.sess.query(Site).from_statement(
            text(
                "select * from site "
                "where lower(code || ' ' || name) like '%' || lower(:pattern) "
                "|| '%' order by code limit :lim")).params(
            pattern=pattern.strip(), lim=LIMIT).all()

        if len(sites) == 1:
            return chellow_redirect("/sites/" + str(sites[0].id))
        else:
            return render_template('sites.html', sites=sites, limit=LIMIT)
    else:
        return render_template('sites.html')


@views.route('/dc_contracts')
def dc_contracts_get():
    dc_contracts = g.sess.query(Contract).join(MarketRole).filter(
        MarketRole.code.in_(('C', 'D'))).order_by(Contract.name).all()
    return render_template('dc_contracts.html', dc_contracts=dc_contracts)


@views.route('/dc_contracts/add', methods=['POST'])
def dc_contracts_add_post():
    try:
        party_id = req_int('party_id')
        name = req_str('name')
        start_date = req_date('start')
        party = Party.get_by_id(g.sess, party_id)
        market_role_code = party.market_role.code
        if market_role_code == 'C':
            contract = Contract.insert_hhdc(
                g.sess, name, party.participant, '{}', {}, start_date, None,
                {})
        elif market_role_code == 'D':
            contract = Contract.insert_nhhdc(
                g.sess, name, party.participant, '{}', {}, start_date, None,
                {})
        else:
            raise BadRequest(
                f"The market role {market_role_code} must be C or D.")
        g.sess.commit()
        chellow.hh_importer.startup_contract(contract.id)
        return chellow_redirect(f'/dc_contracts/{contract.id}', 303)
    except BadRequest as e:
        flash(e.description)
        initial_date = utc_datetime_now()
        initial_date = Datetime(initial_date.year, initial_date.month, 1)
        parties = g.sess.query(Party).join(MarketRole).join(
            Participant).filter(MarketRole.code.in_(('C', 'D'))).order_by(
            Participant.code).all()
        return make_response(
            render_template(
                'dc_contracts_add.html', initial_date=initial_date,
                parties=parties), 400)


@views.route('/dc_contracts/add')
def dc_contracts_add_get():
    initial_date = utc_datetime_now()
    initial_date = Datetime(initial_date.year, initial_date.month, 1)
    parties = g.sess.query(Party).join(MarketRole).join(Participant).filter(
        MarketRole.code.in_(('C', 'D'))).order_by(Participant.code).all()
    return render_template(
        'dc_contracts_add.html', initial_date=initial_date, parties=parties)


@views.route('/dc_contracts/<int:dc_contract_id>')
def dc_contract_get(dc_contract_id):
    rate_scripts = None
    try:
        contract = Contract.get_dc_by_id(g.sess, dc_contract_id)
        rate_scripts = g.sess.query(RateScript).filter(
            RateScript.contract == contract).order_by(
            RateScript.start_date.desc()).all()
        now = utc_datetime_now()
        last_month_finish = Datetime(now.year, now.month, 1) - \
            relativedelta(minutes=30)
        return render_template(
            'dc_contract.html', dc_contract=contract,
            rate_scripts=rate_scripts, last_month_finish=last_month_finish)
    except BadRequest as e:
        desc = e.description
        flash(desc)
        if desc.startswith("There isn't a contract"):
            raise e
        else:
            return render_template(
                'dc_contract.html', contract=contract,
                rate_scripts=rate_scripts, last_month_finish=last_month_finish)


@views.route('/parties/<int:party_id>')
def party_get(party_id):
    party = Party.get_by_id(g.sess, party_id)
    return render_template('party.html', party=party)


@views.route('/parties')
def parties_get():
    return render_template(
        'parties.html',
        parties=g.sess.query(Party).join(MarketRole).order_by(
            Party.name, MarketRole.code).all())


@views.route('/market_roles/<int:market_role_id>')
def market_role_get(market_role_id):
    market_role = MarketRole.get_by_id(g.sess, market_role_id)
    return render_template('market_role.html', market_role=market_role)


@views.route('/market_roles')
def market_roles_get():
    market_roles = g.sess.query(MarketRole).order_by(MarketRole.code).all()
    return render_template('market_roles.html', market_roles=market_roles)


@views.route('/participants/<int:participant_id>')
def participant_get(participant_id):
    participant = Participant.get_by_id(g.sess, participant_id)
    return render_template('participant.html', participant=participant)


@views.route('/participants')
def participants_get():
    participants = g.sess.query(Participant).order_by(Participant.code).all()
    return render_template('participants.html', participants=participants)


@views.route('/dc_contracts/<int:dc_contract_id>/edit')
def dc_contract_edit_get(dc_contract_id):
    parties = g.sess.query(Party).join(MarketRole).join(Participant).filter(
        MarketRole.code.in_(('C', 'D'))).order_by(Participant.code).all()
    dc_contract = Contract.get_dc_by_id(g.sess, dc_contract_id)
    initial_date = utc_datetime_now()
    return render_template(
        'dc_contract_edit.html', parties=parties, initial_date=initial_date,
        dc_contract=dc_contract)


@views.route('/dc_contracts/<int:contract_id>/edit', methods=['POST'])
def dc_contract_edit_post(contract_id):
    contract = None
    try:
        contract = Contract.get_dc_by_id(g.sess, contract_id)
        if 'update_state' in request.form:
            state = req_zish("state")
            contract.update_state(state)
            g.sess.commit()
            return chellow_redirect('/dc_contracts/' + str(contract.id), 303)
        elif 'ignore_snags' in request.form:
            ignore_date = req_date('ignore')
            g.sess.execute(
                text(
                    "update snag set is_ignored = true from channel, era "
                    "where snag.channel_id = channel.id "
                    "and channel.era_id = era.id "
                    "and era.dc_contract_id = :contract_id "
                    "and snag.finish_date < :ignore_date"),
                params=dict(contract_id=contract.id, ignore_date=ignore_date))
            g.sess.commit()
            return chellow_redirect("/dc_contracts/" + str(contract.id), 303)
        elif 'delete' in request.form:
            contract.delete(g.sess)
            g.sess.commit()
            return chellow_redirect('/dc_contracts', 303)
        else:
            party_id = req_str('party_id')
            name = req_str("name")
            charge_script = req_str("charge_script")
            properties = req_zish("properties")
            party = Party.get_by_id(g.sess, party_id)
            contract.update(name, party, charge_script, properties)
            g.sess.commit()
            return chellow_redirect('/dc_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        if contract is None:
            raise e
        else:
            parties = g.sess.query(Party).join(MarketRole).join(
                Participant).filter(
                MarketRole.code.in_(('C', 'D'))).order_by(
                Participant.code).all()
            initial_date = utc_datetime_now()
            return make_response(
                render_template(
                    'dc_contract_edit.html', parties=parties,
                    initial_date=initial_date, dc_contract=contract), 400)


@views.route('/dc_contracts/<int:contract_id>/add_rate_script')
def dc_rate_script_add_get(contract_id):
    now = utc_datetime_now()
    initial_date = utc_datetime(now.year, now.month)
    contract = Contract.get_dc_by_id(g.sess, contract_id)
    return render_template(
        'dc_rate_script_add.html', now=now, contract=contract,
        initial_date=initial_date)


@views.route(
    '/dc_contracts/<int:contract_id>/add_rate_script', methods=['POST'])
def dc_rate_script_add_post(contract_id):
    try:
        contract = Contract.get_dc_by_id(g.sess, contract_id)
        start_date = req_date('start')
        rate_script = contract.insert_rate_script(g.sess, start_date, {})
        g.sess.commit()
        return chellow_redirect(
            '/dc_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = utc_datetime_now()
        initial_date = utc_datetime(now.year, now.month)
        return render_template(
            'dc_rate_script_add.html', now=now, contract=contract,
            initial_date=initial_date)


@views.route('/dc_rate_scripts/<int:dc_rate_script_id>')
def dc_rate_script_get(dc_rate_script_id):
    rate_script = RateScript.get_dc_by_id(g.sess, dc_rate_script_id)
    contract = rate_script.contract
    next_rate_script = g.sess.query(RateScript).filter(
        RateScript.contract == contract,
        RateScript.start_date > rate_script.start_date).order_by(
        RateScript.start_date).first()
    previous_rate_script = g.sess.query(RateScript).filter(
        RateScript.contract == contract,
        RateScript.start_date < rate_script.start_date).order_by(
        RateScript.start_date.desc()).first()
    return render_template(
        'dc_rate_script.html', dc_rate_script=rate_script,
        previous_rate_script=previous_rate_script,
        next_rate_script=next_rate_script)


@views.route('/dc_rate_scripts/<int:dc_rate_script_id>/edit')
def dc_rate_script_edit_get(dc_rate_script_id):
    dc_rate_script = RateScript.get_dc_by_id(g.sess, dc_rate_script_id)
    rs_example_func = chellow.computer.contract_func(
            {}, dc_rate_script.contract, 'rate_script_example')
    rs_example = None if rs_example_func is None else rs_example_func()

    return render_template(
        'dc_rate_script_edit.html', dc_rate_script=dc_rate_script,
        rate_script_example=rs_example)


@views.route(
    '/dc_rate_scripts/<int:dc_rate_script_id>/edit', methods=['POST'])
def dc_rate_script_edit_post(dc_rate_script_id):
    try:
        dc_rate_script = RateScript.get_dc_by_id(g.sess, dc_rate_script_id)
        dc_contract = dc_rate_script.contract
        if 'delete' in request.form:
            dc_contract.delete_rate_script(g.sess, dc_rate_script)
            g.sess.commit()
            return chellow_redirect(
                '/dc_contracts/' + str(dc_contract.id), 303)
        else:
            script = req_zish('script')
            start_date = req_date('start')
            has_finished = req_bool('has_finished')
            finish_date = req_date('finish') if has_finished else None
            dc_contract.update_rate_script(
                g.sess, dc_rate_script, start_date, finish_date, script)
            g.sess.commit()
            return chellow_redirect(
                '/dc_rate_scripts/' + str(dc_rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template(
            'dc_rate_script_edit.html', dc_rate_script=dc_rate_script)


@views.route('/supplier_contracts/<int:contract_id>/edit')
def supplier_contract_edit_get(contract_id):
    contract = Contract.get_supplier_by_id(g.sess, contract_id)
    parties = g.sess.query(Party).join(MarketRole, Participant).filter(
        MarketRole.code == 'X').order_by(Participant.code).all()
    return render_template(
        'supplier_contract_edit.html', contract=contract, parties=parties)


@views.route('/supplier_contracts/<int:contract_id>/edit', methods=['POST'])
def supplier_contract_edit_post(contract_id):
    try:
        contract = Contract.get_supplier_by_id(g.sess, contract_id)
        if 'delete' in request.form:
            contract.delete(g.sess)
            g.sess.commit()
            return chellow_redirect('/supplier_contracts', 303)
        else:
            party_id = req_int('party_id')
            party = Party.get_by_id(g.sess, party_id)
            name = req_str('name')
            charge_script = req_str('charge_script')
            properties = req_zish('properties')
            contract.update(name, party, charge_script, properties)
            g.sess.commit()
            return chellow_redirect(
                '/supplier_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        description = e.description
        flash(description)
        if description.startswith("There isn't a contract"):
            raise
        else:
            parties = g.sess.query(Party).join(MarketRole, Participant).filter(
                MarketRole.code == 'X').order_by(Participant.code).all()
            return make_response(
                render_template(
                    'supplier_contract_edit.html', contract=contract,
                    parties=parties), 400)


@views.route('/supplier_rate_scripts/<int:rate_script_id>')
def supplier_rate_script_get(rate_script_id):
    rate_script = RateScript.get_supplier_by_id(g.sess, rate_script_id)
    contract = rate_script.contract
    next_rate_script = g.sess.query(RateScript).filter(
        RateScript.contract == contract,
        RateScript.start_date > rate_script.start_date).order_by(
        RateScript.start_date).first()
    previous_rate_script = g.sess.query(RateScript).filter(
        RateScript.contract == contract,
        RateScript.start_date < rate_script.start_date).order_by(
        RateScript.start_date.desc()).first()
    return render_template(
        'supplier_rate_script.html', previous_rate_script=previous_rate_script,
        next_rate_script=next_rate_script, rate_script=rate_script)


@views.route('/supplier_rate_scripts/<int:rate_script_id>/edit')
def supplier_rate_script_edit_get(rate_script_id):
    rate_script = RateScript.get_supplier_by_id(g.sess, rate_script_id)
    rs_example_func = chellow.computer.contract_func(
            {}, rate_script.contract, 'rate_script_example')
    rs_example = None if rs_example_func is None else rs_example_func()
    return render_template(
        'supplier_rate_script_edit.html', supplier_rate_script=rate_script,
        rate_script_example=rs_example)


@views.route(
    '/supplier_rate_scripts/<int:rate_script_id>/edit', methods=['POST'])
def supplier_rate_script_edit_post(rate_script_id):
    try:
        rate_script = RateScript.get_supplier_by_id(g.sess, rate_script_id)
        contract = rate_script.contract
        if 'delete' in request.values:
            contract.delete_rate_script(g.sess, rate_script)
            g.sess.commit()
            return chellow_redirect(
                '/supplier_contracts/' + str(contract.id), 303)
        else:
            script = req_zish('script')
            start_date = req_date('start')
            has_finished = req_bool('has_finished')
            finish_date = req_date('finish') if has_finished else None
            contract.update_rate_script(
                g.sess, rate_script, start_date, finish_date, script)
            g.sess.commit()
            return chellow_redirect(
                '/supplier_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template(
                'supplier_rate_script_edit.html',
                supplier_rate_script=rate_script), 400)


@views.route('/supplier_contracts')
def supplier_contracts_get():
    contracts = g.sess.query(Contract).join(MarketRole).join(
        Contract.finish_rate_script).filter(MarketRole.code == 'X').order_by(
        Contract.name)
    ongoing_contracts = contracts.filter(RateScript.finish_date == null())
    ended_contracts = contracts.filter(RateScript.finish_date != null())
    return render_template(
        'supplier_contracts.html',
        ongoing_supplier_contracts=ongoing_contracts,
        ended_supplier_contracts=ended_contracts)


@views.route('/supplier_contracts/add', methods=['POST'])
def supplier_contract_add_post():
    try:
        participant_id = req_str("participant_id")
        participant = Participant.get_by_id(g.sess, participant_id)
        name = req_str("name")
        start_date = req_date("start")
        charge_script = req_str("charge_script")
        properties = req_zish("properties")
        contract = Contract.insert_supplier(
            g.sess, name, participant, charge_script, properties, start_date,
            None, {})
        g.sess.commit()
        return chellow_redirect("/supplier_contracts/" + str(contract.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == 'X').order_by(Contract.name)
        parties = g.sess.query(Party).join(MarketRole, Participant).filter(
            MarketRole.code == 'X').order_by(Participant.code)
        return make_response(
            render_template(
                'supplier_contract_add.html', contracts=contracts,
                parties=parties), 400)


@views.route('/supplier_contracts/add')
def supplier_contract_add_get():
    contracts = g.sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'X').order_by(Contract.name)
    parties = g.sess.query(Party).join(MarketRole, Participant).filter(
        MarketRole.code == 'X').order_by(Participant.code)
    return render_template(
        'supplier_contract_add.html', contracts=contracts, parties=parties)


@views.route('/supplier_contracts/<int:contract_id>')
def supplier_contract_get(contract_id):
    print("starting to find supplier contracts")
    contract = Contract.get_supplier_by_id(g.sess, contract_id)
    rate_scripts = g.sess.query(RateScript).filter(
        RateScript.contract == contract).order_by(
        RateScript.start_date.desc()).all()

    now = Datetime.utcnow() - relativedelta(months=1)
    month_start = Datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH

    return render_template(
        'supplier_contract.html', contract=contract, month_start=month_start,
        month_finish=month_finish, rate_scripts=rate_scripts)


@views.route('/supplier_contracts/<int:contract_id>/add_rate_script')
def supplier_rate_script_add_get(contract_id):
    now = utc_datetime_now()
    initial_date = utc_datetime(now.year, now.month)
    contract = Contract.get_supplier_by_id(g.sess, contract_id)
    return render_template(
        'supplier_rate_script_add.html', now=now, contract=contract,
        initial_date=initial_date)


@views.route(
    '/supplier_contracts/<int:contract_id>/add_rate_script', methods=['POST'])
def supplier_rate_script_add_post(contract_id):
    try:
        contract = Contract.get_supplier_by_id(g.sess, contract_id)
        start_date = req_date('start')
        rate_script = contract.insert_rate_script(g.sess, start_date, {})
        g.sess.commit()
        return chellow_redirect(
            '/supplier_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = utc_datetime_now()
        initial_date = utc_datetime(now.year, now.month)
        return render_template(
            'supplier_rate_script_add.html', now=now, contract=contract,
            initial_date=initial_date)


@views.route('/mop_contracts/<int:contract_id>/edit')
def mop_contract_edit_get(contract_id):
    parties = g.sess.query(Party).join(MarketRole).join(Participant).filter(
        MarketRole.code == 'M').order_by(Participant.code).all()
    initial_date = utc_datetime_now()
    contract = Contract.get_mop_by_id(g.sess, contract_id)
    return render_template(
        'mop_contract_edit.html', contract=contract, parties=parties,
        initial_date=initial_date)


@views.route('/mop_contracts/<int:contract_id>/edit', methods=['POST'])
def mop_contract_edit_post(contract_id):
    try:
        contract = Contract.get_mop_by_id(g.sess, contract_id)
        if 'update_state' in request.form:
            state = req_zish('state')
            contract.update_state(state)
            g.sess.commit()
            return chellow_redirect("/mop_contracts/" + str(contract.id), 303)
        elif 'ignore_snags' in request.form:
            ignore_date = req_date('ignore')
            g.sess.execute(
                text(
                    "update snag set is_ignored = true from channel, era "
                    "where snag.channel_id = channel.id "
                    "and channel.era_id = era.id "
                    "and era.dc_contract_id = :contract_id "
                    "and snag.finish_date < :ignore_date"),
                params=dict(contract_id=contract.id, ignore_date=ignore_date))
            g.sess.commit()
            return chellow_redirect('/mop_contracts/' + str(contract.id), 303)
        elif 'delete' in request.form:
            contract.delete(g.sess)
            g.sess.commit()
            return chellow_redirect('/mop_contracts', 303)
        else:
            party_id = req_int("party_id")
            name = req_str("name")
            charge_script = req_str("charge_script")
            properties = req_zish("properties")
            party = Party.get_by_id(g.sess, party_id)
            contract.update(name, party, charge_script, properties)
            g.sess.commit()
            return chellow_redirect('/mop_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        parties = g.sess.query(Party).join(MarketRole).join(Participant). \
            filter(MarketRole.code == 'M').order_by(Participant.code).all()
        initial_date = utc_datetime_now()
        contract = Contract.get_mop_by_id(g.sess, contract_id)
        return make_response(
            render_template(
                'mop_contract_edit.html', contract=contract, parties=parties,
                initial_date=initial_date), 400)


@views.route('/mop_rate_scripts/<int:rate_script_id>')
def mop_rate_script_get(rate_script_id):
    rate_script = RateScript.get_mop_by_id(g.sess, rate_script_id)
    contract = rate_script.contract
    next_rate_script = g.sess.query(RateScript).filter(
        RateScript.contract == contract,
        RateScript.start_date > rate_script.start_date).order_by(
        RateScript.start_date).first()
    previous_rate_script = g.sess.query(RateScript).filter(
        RateScript.contract == contract,
        RateScript.start_date < rate_script.start_date).order_by(
        RateScript.start_date.desc()).first()
    return render_template(
        'mop_rate_script.html', rate_script=rate_script,
        previous_rate_script=previous_rate_script,
        next_rate_script=next_rate_script)


@views.route('/mop_rate_scripts/<int:rate_script_id>/edit')
def mop_rate_script_edit_get(rate_script_id):
    rate_script = RateScript.get_mop_by_id(g.sess, rate_script_id)
    rs_example_func = chellow.computer.contract_func(
            {}, rate_script.contract, 'rate_script_example')
    rs_example = None if rs_example_func is None else rs_example_func()
    return render_template(
        'mop_rate_script_edit.html', rate_script=rate_script,
        rate_script_example=rs_example)


@views.route('/mop_rate_scripts/<int:rate_script_id>/edit', methods=['POST'])
def mop_rate_script_edit_post(rate_script_id):
    rate_script = RateScript.get_mop_by_id(g.sess, rate_script_id)
    contract = rate_script.contract
    if 'delete' in request.form:
        contract.delete_rate_script(g.sess, rate_script)
        g.sess.commit()
        return chellow_redirect('/mop_contracts/' + str(contract.id), 303)
    else:
        try:
            script = req_zish('script')
            start_date = req_date('start')
            if 'has_finished' in request.form:
                finish_date = req_date('finish')
            else:
                finish_date = None
            contract.update_rate_script(
                g.sess, rate_script, start_date, finish_date, script)
            g.sess.commit()
            return chellow_redirect(
                '/mop_rate_scripts/' + str(rate_script.id), 303)
        except BadRequest as e:
            flash(e.description)
            return make_response(
                render_template(
                    'mop_rate_script_edit.html', rate_script=rate_script), 400)


@views.route('/mop_contracts')
def mop_contracts_get():
    mop_contracts = g.sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'M').order_by(Contract.name).all()
    return render_template('mop_contracts.html', mop_contracts=mop_contracts)


@views.route('/mop_contracts/add', methods=['POST'])
def mop_contract_add_post():
    try:
        participant_id = req_int('participant_id')
        name = req_str('name')
        start_date = req_date('start')
        participant = Participant.get_by_id(g.sess, participant_id)
        contract = Contract.insert_mop(
            g.sess, name, participant, '{}', {}, start_date, None, {})
        g.sess.commit()
        return chellow_redirect('/mop_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        initial_date = utc_datetime_now()
        initial_date = Datetime(initial_date.year, initial_date.month, 1)
        parties = g.sess.query(Party).join(MarketRole).join(Participant). \
            filter(MarketRole.code == 'M').order_by(Participant.code).all()
        return make_response(
            render_template(
                'mop_contract_add.html', inital_date=initial_date,
                parties=parties), 400)


@views.route('/mop_contracts/add')
def mop_contract_add_get():
    initial_date = utc_datetime_now()
    initial_date = Datetime(initial_date.year, initial_date.month, 1)
    parties = g.sess.query(Party).join(MarketRole).join(Participant).filter(
        MarketRole.code == 'M').order_by(Participant.code).all()
    return render_template(
        'mop_contract_add.html', inital_date=initial_date, parties=parties)


@views.route('/mop_contracts/<int:contract_id>')
def mop_contract_get(contract_id):
    contract = Contract.get_mop_by_id(g.sess, contract_id)
    rate_scripts = g.sess.query(RateScript).filter(
        RateScript.contract == contract).order_by(
        RateScript.start_date.desc()).all()
    now = utc_datetime_now()
    last_month_start = utc_datetime(now.year, now.month) - \
        relativedelta(months=1)
    last_month_finish = last_month_start + relativedelta(months=1) - HH
    party = contract.party
    return render_template(
        'mop_contract.html', contract=contract, rate_scripts=rate_scripts,
        last_month_start=last_month_start, last_month_finish=last_month_finish,
        party=party)


@views.route('/mop_contracts/<int:contract_id>/add_rate_script')
def mop_rate_script_add_get(contract_id):
    contract = Contract.get_mop_by_id(g.sess, contract_id)
    now = utc_datetime_now()
    initial_date = utc_datetime(now.year, now.month)
    return render_template(
        'mop_rate_script_add.html', contract=contract,
        initial_date=initial_date)


@views.route(
    '/mop_contracts/<int:contract_id>/add_rate_script', methods=['POST'])
def mop_rate_script_add_post(contract_id):
    try:
        contract = Contract.get_mop_by_id(g.sess, contract_id)
        start_date = req_date('start')
        rate_script = contract.insert_rate_script(g.sess, start_date, {})
        g.sess.commit()
        return chellow_redirect(
            '/mop_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = utc_datetime_now()
        initial_date = utc_datetime(now.year, now.month)
        return make_response(
            render_template(
                'mop_rate_script_add.html', contract=contract,
                initial_date=initial_date), 400)


@views.route('/supplies/<int:supply_id>/months')
def supply_months_get(supply_id):
    supply = Supply.get_by_id(g.sess, supply_id)

    is_import = req_bool("is_import")
    year = req_int('year')
    years = req_int('years')

    month_start = utc_datetime(year - years + 1, 1)
    months = []
    for i in range(12 * years):
        next_month_start = month_start + relativedelta(months=1)
        month_finish = next_month_start - HH

        month_data = {}
        months.append(month_data)

        era = supply.find_era_at(g.sess, month_finish)
        if era is not None:
            mpan_core = era.imp_mpan_core if is_import else era.exp_mpan_core
            if mpan_core is not None:
                month_data['mpan_core'] = mpan_core
                month_data['sc'] = era.imp_sc if is_import else era.exp_sc

        md_kvah = 0
        channel_ids = [
            c.id for c in g.sess.query(Channel).join(Era).filter(
                Era.supply == supply, Era.start_date <= month_finish,
                or_(
                    Era.finish_date == null(), Era.finish_date >= month_start),
                Channel.imp_related == is_import)]
        for kwh, kvarh, hh_date in g.sess.query(
                cast(
                    func.max(
                        case(
                            [
                                (
                                    Channel.channel_type == 'ACTIVE',
                                    HhDatum.value)], else_=0)), Float),
                cast(
                    func.max(
                        case(
                            [
                                (
                                    Channel.channel_type.in_(
                                        (
                                            'REACTIVE_IMP', 'REACTIVE_EXP')),
                                    HhDatum.value)], else_=0)), Float),
                HhDatum.start_date).join(
                Channel, HhDatum.channel_id == Channel.id).filter(
                Channel.id.in_(channel_ids),
                HhDatum.start_date >= month_start,
                HhDatum.start_date <= month_finish).group_by(
                HhDatum.start_date):

            kvah = (kwh ** 2 + kvarh ** 2) ** 0.5
            if kvah > md_kvah:
                md_kvah = kvah
                month_data['md_kva'] = 2 * md_kvah
                month_data['md_kvar'] = kvarh * 2
                month_data['md_kw'] = kwh * 2
                month_data['md_pf'] = kwh / kvah
                month_data['md_date'] = hh_date

        total_kwh = g.sess.query(func.sum(HhDatum.value)).join(Channel) \
            .filter(
                Channel.id.in_(channel_ids), Channel.channel_type == 'ACTIVE',
                HhDatum.start_date >= month_start,
                HhDatum.start_date <= month_finish).scalar()

        if total_kwh is not None:
            month_data['total_kwh'] = float(total_kwh)

        month_data['start_date'] = month_start
        month_start = next_month_start

    return render_template(
        'supply_months.html', supply=supply, months=months,
        is_import=is_import, now=utc_datetime_now())


@views.route('/supplies/<int:supply_id>/edit')
def supply_edit_get(supply_id):
    supply = Supply.get_by_id(g.sess, supply_id)
    sources = g.sess.query(Source).order_by(Source.code)
    generator_types = g.sess.query(GeneratorType).order_by(GeneratorType.code)
    gsp_groups = g.sess.query(GspGroup).order_by(GspGroup.code)
    eras = g.sess.query(Era).filter(
        Era.supply == supply).order_by(Era.start_date.desc())
    return render_template(
        'supply_edit.html', supply=supply, sources=sources,
        generator_types=generator_types, gsp_groups=gsp_groups, eras=eras)


@views.route('/supplies/<int:supply_id>/edit', methods=['POST'])
def supply_edit_post(supply_id):
    try:
        supply = Supply.get_by_id(g.sess, supply_id)

        if 'delete' in request.form:
            supply.delete(g.sess)
            g.sess.commit()
            return chellow_redirect("/supplies", 303)
        elif 'insert_era' in request.form:
            start_date = req_date('start')
            supply.insert_era_at(g.sess, start_date)
            g.sess.commit()
            return chellow_redirect("/supplies/" + str(supply.id), 303)
        else:
            name = req_str("name")
            source_id = req_int("source_id")
            gsp_group_id = req_int("gsp_group_id")
            source = Source.get_by_id(g.sess, source_id)
            if source.code in ('gen', 'gen-net'):
                generator_type_id = req_int("generator_type_id")
                generator_type = GeneratorType.get_by_id(
                    g.sess, generator_type_id)
            else:
                generator_type = None
            gsp_group = GspGroup.get_by_id(g.sess, gsp_group_id)
            supply.update(name, source, generator_type, gsp_group, supply.dno)
            g.sess.commit()
            return chellow_redirect("/supplies/" + str(supply.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        sources = g.sess.query(Source).order_by(Source.code)
        generator_types = g.sess.query(GeneratorType). \
            order_by(GeneratorType.code)
        gsp_groups = g.sess.query(GspGroup).order_by(GspGroup.code)
        eras = g.sess.query(Era).filter(
            Era.supply == supply).order_by(Era.start_date.desc())
        return make_response(
            render_template(
                'supply_edit.html', supply=supply, sources=sources,
                generator_types=generator_types, gsp_groups=gsp_groups,
                eras=eras), 400)


@views.route('/eras/<int:era_id>/edit')
def era_edit_get(era_id):
    era = Era.get_by_id(g.sess, era_id)
    pcs = g.sess.query(Pc).order_by(Pc.code)
    cops = g.sess.query(Cop).order_by(Cop.code)
    gsp_groups = g.sess.query(GspGroup).order_by(GspGroup.code)
    mop_contracts = g.sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'M').order_by(Contract.name)
    dc_contracts = g.sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'C').order_by(Contract.name)
    supplier_contracts = g.sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'X').order_by(Contract.name)
    site_eras = g.sess.query(SiteEra).join(Site).filter(
        SiteEra.era == era).order_by(Site.code).all()
    return render_template(
        'era_edit.html', era=era, pcs=pcs, cops=cops, gsp_groups=gsp_groups,
        mop_contracts=mop_contracts, dc_contracts=dc_contracts,
        supplier_contracts=supplier_contracts, site_eras=site_eras)


@views.route('/eras/<int:era_id>/edit', methods=['POST'])
def era_edit_post(era_id):
    try:
        era = Era.get_by_id(g.sess, era_id)

        if 'delete' in request.form:
            supply = era.supply
            supply.delete_era(g.sess, era)
            g.sess.commit()
            return chellow_redirect("/supplies/" + str(supply.id), 303)
        elif 'attach' in request.form:
            site_code = req_str("site_code")
            site = Site.get_by_code(g.sess, site_code)
            era.attach_site(g.sess, site)
            g.sess.commit()
            return chellow_redirect("/supplies/" + str(era.supply.id), 303)
        elif 'detach' in request.form:
            site_id = req_int("site_id")
            site = Site.get_by_id(g.sess, site_id)
            era.detach_site(g.sess, site)
            g.sess.commit()
            return chellow_redirect("/supplies/" + str(era.supply.id), 303)
        elif 'locate' in request.form:
            site_id = req_int("site_id")
            site = Site.get_by_id(g.sess, site_id)
            era.set_physical_location(g.sess, site)
            g.sess.commit()
            return chellow_redirect("/supplies/" + str(era.supply.id), 303)
        else:
            start_date = req_date('start')
            is_ended = req_bool("is_ended")
            if is_ended:
                finish_date = req_hh_date("finish")
            else:
                finish_date = None
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
            mtc = Mtc.get_by_code(g.sess, era.supply.dno, mtc_code)
            cop_id = req_int("cop_id")
            cop = Cop.get_by_id(g.sess, cop_id)
            ssc_code = req_str("ssc_code")
            ssc_code = ssc_code.strip()
            properties = req_zish("properties")
            if len(ssc_code) == 0:
                ssc = None
            else:
                ssc = Ssc.get_by_code(g.sess, ssc_code)

            if 'imp_mpan_core' in request.values:
                imp_mpan_core_raw = req_str('imp_mpan_core')
            else:
                imp_mpan_core_raw = None

            if imp_mpan_core_raw is None or \
                    len(imp_mpan_core_raw.strip()) == 0:
                imp_mpan_core = None
                imp_sc = None
                imp_supplier_contract = None
                imp_supplier_account = None
                imp_llfc_code = None
            else:
                imp_mpan_core = parse_mpan_core(imp_mpan_core_raw)
                imp_llfc_code = req_str('imp_llfc_code')
                imp_supplier_contract_id = req_int("imp_supplier_contract_id")
                imp_supplier_contract = Contract.get_supplier_by_id(
                    g.sess, imp_supplier_contract_id)
                imp_supplier_account = req_str("imp_supplier_account")
                imp_sc = req_int("imp_sc")

            if 'exp_mpan_core' in request.form:
                exp_mpan_core_raw = req_str('exp_mpan_core')
            else:
                exp_mpan_core_raw = None

            if exp_mpan_core_raw is None or \
                    len(exp_mpan_core_raw.strip()) == 0:
                exp_mpan_core = None
                exp_llfc_code = None
                exp_sc = None
                exp_supplier_contract = None
                exp_supplier_account = None
            else:
                exp_mpan_core = parse_mpan_core(exp_mpan_core_raw)
                exp_llfc_code = req_str("exp_llfc_code")
                exp_sc = req_int("exp_sc")
                exp_supplier_contract_id = req_int('exp_supplier_contract_id')
                exp_supplier_contract = Contract.get_supplier_by_id(
                    g.sess, exp_supplier_contract_id)
                exp_supplier_account = req_str('exp_supplier_account')

            era.supply.update_era(
                g.sess, era, start_date, finish_date, mop_contract,
                mop_account, dc_contract, dc_account, msn, pc, mtc, cop, ssc,
                properties, imp_mpan_core, imp_llfc_code,
                imp_supplier_contract, imp_supplier_account,
                imp_sc, exp_mpan_core, exp_llfc_code, exp_supplier_contract,
                exp_supplier_account, exp_sc)
            g.sess.commit()
            return chellow_redirect("/supplies/" + str(era.supply.id), 303)
    except BadRequest as e:
        flash(e.description)
        pcs = g.sess.query(Pc).order_by(Pc.code)
        cops = g.sess.query(Cop).order_by(Cop.code)
        gsp_groups = g.sess.query(GspGroup).order_by(GspGroup.code)
        mop_contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == 'M').order_by(Contract.name)
        dc_contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code.in_(('C', 'D'))).order_by(Contract.name)
        supplier_contracts = g.sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == 'X').order_by(Contract.name)
        site_eras = g.sess.query(SiteEra).join(Site).filter(
            SiteEra.era == era).order_by(Site.code).all()
        return make_response(
            render_template(
                'era_edit.html', era=era, pcs=pcs, cops=cops,
                gsp_groups=gsp_groups, mop_contracts=mop_contracts,
                dc_contracts=dc_contracts,
                supplier_contracts=supplier_contracts, site_eras=site_eras),
            400)


@views.route('/eras/<int:era_id>/add_supplier_bill')
def era_supplier_bill_add_get(era_id):
    era = Era.get_by_id(g.sess, era_id)
    bill_types = g.sess.query(BillType).order_by(BillType.code)
    start_date = account = None
    normal_bill_type_id = g.sess.query(BillType.id).filter(
        BillType.code == 'N').scalar()
    latest_bill = g.sess.query(Bill).join(Batch).join(Contract).join(
        MarketRole).filter(
        Bill.supply == era.supply, MarketRole.code == 'X').order_by(
        Bill.start_date.desc()).first()

    if latest_bill is None:
        next_batch_reference = next_batch_description = ''
    else:
        start_date = latest_bill.finish_date + HH
        account = latest_bill.account
        next_batch_reference, next_batch_description = \
            latest_bill.batch.contract.get_next_batch_details(g.sess)

    return render_template(
        'era_supplier_bill_add.html', era=era, bill_types=bill_types,
        start_date=start_date, account=account,
        normal_bill_type_id=normal_bill_type_id,
        next_batch_reference=next_batch_reference,
        next_batch_description=next_batch_description)


@views.route('/eras/<int:era_id>/add_supplier_bill', methods=['POST'])
def era_supplier_bill_add_post(era_id):
    try:
        era = Era.get_by_id(g.sess, era_id)

        batch_reference = req_str('batch_reference')
        batch_description = req_str('batch_description')

        batch = era.imp_supplier_contract.insert_batch(
            g.sess, batch_reference, batch_description)

        account = req_str('account')
        bill_reference = req_str('bill_reference')
        issue_date = req_date('issue')
        start_date = req_hh_date('start')
        finish_date = req_hh_date('finish')
        kwh = req_decimal('kwh')
        net = req_decimal('net')
        vat = req_decimal('vat')
        gross = req_decimal('gross')
        bill_type_id = req_int('bill_type_id')
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        breakdown_str = req_str('breakdown')
        breakdown = loads(breakdown_str)
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        batch.insert_bill(
            g.sess, account, bill_reference, issue_date, start_date,
            finish_date, kwh, net, vat, gross, bill_type, breakdown,
            era.supply)
        g.sess.commit()
        return chellow_redirect('/supplies/' + str(era.supply.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        bill_types = g.sess.query(BillType).order_by(BillType.code)
        return make_response(
            render_template(
                'era_supplier_bill_add.html', era=era, bill_types=bill_types,
                start_date=None, account=None),
            400)


@views.route('/supplies')
def supplies_get():
    if 'search_pattern' in request.args:
        pattern = req_str('search_pattern')
        pattern = pattern.strip()
        reduced_pattern = pattern.replace(" ", "")
        if 'max_results' in request.args:
            max_results = req_int('max_results')
        else:
            max_results = 50
        e_eras = g.sess.query(Era).from_statement(
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
                "and e1.start_date = sq.max_start_date limit :max_results")
            ).params(
            pattern="%" + pattern + "%",
            reduced_pattern="%" + reduced_pattern + "%",
            max_results=max_results).all()

        g_eras = g.sess.query(GEra).from_statement(
            text("""
select e1.* from g_era as e1 inner join
  (select e2.g_supply_id, max(e2.start_date) as max_start_date
  from g_era as e2 join g_supply on e2.g_supply_id = g_supply.id
  where
    lower(g_supply.mprn) like lower(:pattern)
    or lower(e2.account) like lower(:pattern)
    or lower(e2.msn) like lower(:pattern)
  group by e2.g_supply_id) as sq
on e1.g_supply_id = sq.g_supply_id and e1.start_date = sq.max_start_date
limit :max_results""")
            ).params(
            pattern="%" + pattern + "%",
            max_results=max_results).all()

        if len(e_eras) == 1 and len(g_eras) == 0:
            return chellow_redirect(
                "/supplies/" + str(e_eras[0].supply.id), 307)
        elif len(e_eras) == 0 and len(g_eras) == 1:
            return chellow_redirect(
                "/g_supplies/" + str(g_eras[0].g_supply.id), 307)
        else:
            return render_template(
                'supplies.html', e_eras=e_eras, g_eras=g_eras,
                max_results=max_results)
    else:
        return render_template('supplies.html')


@views.route('/supplies/<int:supply_id>')
def supply_get(supply_id):
    debug = ''
    supply = g.sess.query(Supply).filter(Supply.id == supply_id).options(
        joinedload(Supply.source), joinedload(Supply.generator_type),
        joinedload(Supply.gsp_group), joinedload(Supply.dno)).first()
    if supply is None:
        raise NotFound("There isn't a supply with the id " + str(supply_id))

    supply = Supply.get_by_id(g.sess, supply_id)
    era_bundles = get_era_bundles(g.sess, supply)

    RELATIVE_YEAR = relativedelta(years=1)

    now = Datetime.utcnow()
    triad_year = (now - RELATIVE_YEAR).year if now.month < 3 else now.year
    this_month_start = Datetime(now.year, now.month, 1)
    last_month_start = this_month_start - relativedelta(months=1)
    last_month_finish = this_month_start - relativedelta(minutes=30)

    batch_reports = []
    config_contract = Contract.get_non_core_by_name(g.sess, 'configuration')
    properties = config_contract.make_properties()
    if 'supply_reports' in properties:
        for report_id in properties['supply_reports']:
            batch_reports.append(Report.get_by_id(g.sess, report_id))

    truncated_note = None
    is_truncated = False
    note = None
    if len(supply.note.strip()) == 0:
        note_str = "{'notes': []}"
    else:
        note_str = supply.note

    supply_note = eval(note_str)
    notes = supply_note['notes']
    if len(notes) > 0:
        note = notes[0]
        lines = note['body'].splitlines()
        if len(lines) > 0:
            trunc_line = lines[0][:50]
            if len(lines) > 1 or len(lines[0]) > len(trunc_line):
                is_truncated = True
                truncated_note = trunc_line

    return render_template(
        'supply.html', triad_year=triad_year, now=now,
        last_month_start=last_month_start, last_month_finish=last_month_finish,
        era_bundles=era_bundles, supply=supply, system_properties=properties,
        is_truncated=is_truncated, truncated_note=truncated_note, note=note,
        this_month_start=this_month_start, batch_reports=batch_reports,
        debug=debug)


@views.route('/channels/<int:channel_id>')
def channel_get(channel_id):
    channel = Channel.get_by_id(g.sess, channel_id)
    page = req_int('page') if 'page' in request.values else 0
    page_size = 3000
    prev_page = None if page == 0 else page - 1
    hh_data = g.sess.query(HhDatum).filter(HhDatum.channel == channel). \
        order_by(HhDatum.start_date).offset(page * page_size). \
        limit(page_size)
    if g.sess.query(HhDatum).filter(HhDatum.channel == channel). \
            order_by(HhDatum.start_date).offset((page + 1) * page_size). \
            limit(page_size).count() > 0:
        next_page = page + 1
    else:
        next_page = None
    snags = g.sess.query(Snag).filter(Snag.channel == channel).order_by(
        Snag.start_date)
    return render_template(
        'channel.html', channel=channel, hh_data=hh_data, snags=snags,
        prev_page=prev_page, this_page=page, next_page=next_page)


@views.route('/dc_contracts/<int:contract_id>/hh_imports')
def dc_contracts_hh_imports_get(contract_id):
    contract = Contract.get_dc_by_id(g.sess, contract_id)
    processes = chellow.hh_importer.get_hh_import_processes(contract.id)
    return render_template(
        'dc_contract_hh_imports.html', contract=contract, processes=processes,
        parser_names=', '.join(chellow.hh_importer.extensions))


@views.route('/dc_contracts/<int:contract_id>/hh_imports', methods=['POST'])
def dc_contracts_hh_imports_post(contract_id):
    try:
        contract = Contract.get_dc_by_id(g.sess, contract_id)

        file_item = request.files["import_file"]
        f = StringIO(str(file_item.stream.read(), 'utf-8'))
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        f.seek(0)
        hh_import_process = chellow.hh_importer.start_hh_import_process(
            contract_id, f, file_item.filename, file_size)
        return chellow_redirect(
            "/dc_contracts/" + str(contract.id) + "/hh_imports/" +
            str(hh_import_process.id), 303)
    except BadRequest as e:
        if contract is None:
            raise e
        else:
            flash(e.description)
            processes = chellow.hh_importer.get_hh_import_processes(
                contract.id)
            return make_response(
                render_template(
                    'dc_contract_hh_imports.html', contract=contract,
                    processes=processes), 400)


@views.route('/dc_contracts/<int:contract_id>/hh_imports/<int:import_id>')
def dc_contracts_hh_import_get(contract_id, import_id):
    contract = Contract.get_dc_by_id(g.sess, contract_id)
    process = chellow.hh_importer.get_hh_import_processes(
        contract_id)[import_id]
    return render_template(
        'dc_contract_hh_import.html', contract=contract, process=process)


@views.route('/site_snags')
def site_snags_get():
    snags = g.sess.query(Snag).filter(
        Snag.is_ignored == false(), Snag.site_id != null()).order_by(
        Snag.start_date.desc(), Snag.id).all()
    site_count = g.sess.query(Snag).join(Site).filter(
        Snag.is_ignored == false()).distinct(Site.id).count()
    return render_template(
        'site_snags.html', snags=snags, site_count=site_count)


@views.route('/sites/<int:site_id>/site_snags')
def site_site_snags_get(site_id):
    site = Site.get_by_id(g.sess, site_id)
    snags = g.sess.query(Snag).filter(
        Snag.is_ignored == false(), Snag.site == site).order_by(
        Snag.start_date.desc(), Snag.id)
    return render_template('site_site_snags.html', site=site, snags=snags)


@views.route('/site_snags/edit')
def site_snags_edit_get():
    return render_template('site_snags_edit.html')


@views.route('/site_snags/edit', methods=['POST'])
def site_snags_edit_post():
    try:
        finish_date = req_date('ignore')
        g.sess.execute(
            "update snag set is_ignored = true "
            "where snag.site_id is not null and "
            "snag.finish_date < :finish_date", {'finish_date': finish_date})
        g.sess.commit()
        return chellow_redirect('/site_snags', 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(render_template('site_snags_edit.html'), 400)


@views.route('/channel_snags/<int:snag_id>')
def channel_snag_get(snag_id):
    snag = Snag.get_by_id(g.sess, snag_id)
    return render_template('channel_snag.html', snag=snag)


@views.route('/channel_snags/<int:snag_id>/edit')
def channel_snag_edit_get(snag_id):
    snag = Snag.get_by_id(g.sess, snag_id)
    return render_template('channel_snag_edit.html', snag=snag)


@views.route('/channel_snags/<int:snag_id>/edit', methods=['POST'])
def channel_snag_edit_post(snag_id):
    try:
        ignore = req_bool('ignore')
        snag = Snag.get_by_id(g.sess, snag_id)
        snag.set_is_ignored(ignore)
        g.sess.commit()
        return chellow_redirect("/channel_snags/" + str(snag.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template('channel_snag_edit.html', snag=snag), 400)


@views.route('/channels/<int:channel_id>/edit')
def channel_edit_get(channel_id):
    channel = Channel.get_by_id(g.sess, channel_id)
    now = utc_datetime_now()
    return render_template('channel_edit.html', channel=channel, now=now)


@views.route('/channels/<int:channel_id>/edit', methods=['POST'])
def channel_edit_post(channel_id):
    try:
        channel = Channel.get_by_id(g.sess, channel_id)
        if 'delete' in request.values:
            supply_id = channel.era.supply.id
            channel.era.delete_channel(
                g.sess, channel.imp_related, channel.channel_type)
            g.sess.commit()
            return chellow_redirect('/supplies/' + str(supply_id), 303)
        elif 'delete_data' in request.values:
            start_date = req_hh_date('start')
            finish_date = req_hh_date('finish')
            channel.delete_data(g.sess, start_date, finish_date)
            g.sess.commit()
            flash("Data successfully deleted.")
            return chellow_redirect(
                '/channels/' + str(channel_id) + '/edit', 303)
        elif 'insert' in request.values:
            start_date = req_hh_date('start')
            value = req_decimal('value')
            status = req_str('status')
            if start_date < channel.era.start_date:
                raise BadRequest(
                    "The start date is before the start of this era.")
            if hh_after(start_date, channel.era.finish_date):
                raise BadRequest(
                    "The finish date is after the end of this era.")
            hh_datum = g.sess.query(HhDatum).filter(
                HhDatum.channel == channel,
                HhDatum.start_date == start_date).first()
            if hh_datum is not None:
                raise BadRequest(
                    "There's already a datum in this channel at this time.")
            if channel.imp_related:
                mpan_core = channel.era.imp_mpan_core
            else:
                mpan_core = channel.era.exp_mpan_core
            HhDatum.insert(
                g.sess, [
                    {
                        'start_date': start_date, 'value': value,
                        'status': status,
                        'mpan_core': mpan_core,
                        'channel_type': channel.channel_type}])
            g.sess.commit()
            return chellow_redirect('/channels/' + str(channel_id), 303)
    except BadRequest as e:
        flash(e.description)
        now = utc_datetime_now()
        return render_template('channel_edit.html', channel=channel, now=now)


@views.route('/eras/<int:era_id>/add_channel')
def add_channel_get(era_id):
    era = Era.get_by_id(g.sess, era_id)
    channels = g.sess.query(Channel).filter(
        Channel.era == era).order_by(Channel.imp_related, Channel.channel_type)
    return render_template('channel_add.html', era=era, channels=channels)


@views.route('/eras/<int:era_id>/add_channel', methods=['POST'])
def add_channel_post(era_id):
    try:
        imp_related = req_bool('imp_related')
        channel_type = req_str('channel_type')
        era = Era.get_by_id(g.sess, era_id)
        channel = era.insert_channel(g.sess, imp_related, channel_type)
        g.sess.commit()
        return chellow_redirect('/channels/' + str(channel.id), 303)
    except BadRequest as e:
        flash(e.description)
        channels = g.sess.query(Channel).filter(
            Channel.era == era).order_by(
                Channel.imp_related, Channel.channel_type)
        return render_template('channel_add.html', era=era, channels=channels)


@views.route('/site_snags/<int:snag_id>')
def site_snag_post(snag_id):
    snag = Snag.get_by_id(g.sess, snag_id)
    return render_template('site_snag.html', snag=snag)


@views.route('/reports/<report_id>')
def report_get(report_id):
    report_module = importlib.import_module(
        "chellow.reports.report_" + report_id)
    return report_module.do_get(g.sess)


@views.route('/reports/<report_id>', methods=['POST'])
def report_post(report_id):
    report_module = importlib.import_module(
        "chellow.reports.report_" + report_id)
    return report_module.do_post(g.sess)


@views.route('/supplier_contracts/<int:contract_id>/add_batch')
def supplier_batch_add_get(contract_id):
    contract = Contract.get_supplier_by_id(g.sess, contract_id)
    batches = g.sess.query(Batch).filter(
        Batch.contract == contract).order_by(Batch.reference.desc())
    next_batch_reference, next_batch_description = \
        contract.get_next_batch_details(g.sess)
    return render_template(
        'supplier_batch_add.html', contract=contract, batches=batches,
        next_batch_reference=next_batch_reference,
        next_batch_description=next_batch_description)


@views.route(
    '/supplier_contracts/<int:contract_id>/add_batch', methods=['POST'])
def supplier_batch_add_post(contract_id):
    contract = Contract.get_supplier_by_id(g.sess, contract_id)
    try:
        reference = req_str("reference")
        description = req_str("description")

        batch = contract.insert_batch(g.sess, reference, description)
        g.sess.commit()
        return chellow_redirect(f"/supplier_batches/{batch.id}", 303)

    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        batches = g.sess.query(Batch).filter(
            Batch.contract == contract).order_by(Batch.reference.desc())
        return make_response(
            render_template(
                'supplier_batch_add.html', contract=contract, batches=batches),
            400)


@views.route('/supplier_bill_imports/<int:import_id>')
def supplier_bill_import_get(import_id):
    importer = chellow.bill_importer.get_bill_import(import_id)
    batch = Batch.get_by_id(g.sess, importer.batch_id)
    fields = {}
    if importer is not None:
        imp_fields = importer.make_fields()
        if 'successful_bills' in imp_fields and \
                len(imp_fields['successful_bills']) > 0:
            fields['successful_max_registers'] = \
                max(len(bill['reads']) for bill in
                    imp_fields['successful_bills'])
        fields.update(imp_fields)
        fields['status'] = importer.status()
    return render_template(
        'supplier_bill_import.html', batch=batch, importer=importer, **fields)


@views.route('/supplier_batches')
def supplier_batches_get():
    contract_id = req_int('supplier_contract_id')
    contract = Contract.get_supplier_by_id(g.sess, contract_id)
    batches = g.sess.query(Batch).filter(Batch.contract == contract) \
        .order_by(Batch.reference.desc())
    return render_template(
        'supplier_batches.html', contract=contract, batches=batches)


@views.route('/supplier_batches/<int:batch_id>')
def supplier_batch_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)

    num_bills, sum_net_gbp, sum_vat_gbp, sum_gross_gbp, sum_kwh = g.sess.query(
        func.count(Bill.id), func.sum(Bill.net), func.sum(Bill.vat),
        func.sum(Bill.gross), func.sum(Bill.kwh)).filter(
        Bill.batch == batch).one()
    if sum_net_gbp is None:
        sum_net_gbp = sum_vat_gbp = sum_gross_gbp = sum_kwh = 0

    if 'bill_limit' in request.values and num_bills > req_int('bill_limit'):
        bills = None
    else:
        bills = g.sess.query(Bill).filter(Bill.batch == batch).order_by(
            Bill.reference, Bill.start_date).options(
            joinedload(Bill.bill_type)).all()

    config_contract = Contract.get_non_core_by_name(g.sess, 'configuration')
    properties = config_contract.make_properties()
    if 'batch_reports' in properties:
        batch_reports = []
        for report_id in properties['batch_reports']:
            batch_reports.append(Report.get_by_id(g.sess, report_id))
    else:
        batch_reports = None

    importer_ids = sorted(
        chellow.bill_importer.get_bill_import_ids(batch), reverse=True)
    return render_template(
        'supplier_batch.html', batch=batch, bills=bills,
        batch_reports=batch_reports, num_bills=num_bills,
        sum_net_gbp=sum_net_gbp, sum_vat_gbp=sum_vat_gbp,
        sum_gross_gbp=sum_gross_gbp, sum_kwh=sum_kwh,
        importer_ids=importer_ids)


@views.route('/supplier_batches/<int:batch_id>', methods=['POST'])
def supplier_batch_post(batch_id):
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        if 'import_bills' in request.values:
            import_id = chellow.bill_importer.start_bill_import(batch)
            return chellow_redirect(f"/supplier_bill_imports/{import_id}", 303)
        elif 'delete_bills' in request.values:
            g.sess.query(Bill).filter(Bill.batch_id == batch.id).delete(False)
            g.sess.commit()
            return chellow_redirect(f'/supplier_batches/{batch.id}', 303)
        elif 'delete_import_bills' in request.values:
            g.sess.query(Bill).filter(Bill.batch_id == batch.id).delete(False)
            g.sess.commit()
            import_id = chellow.bill_importer.start_bill_import(batch)
            return chellow_redirect(f"/supplier_bill_imports/{import_id}", 303)
    except BadRequest as e:
        flash(e.description)
        importer_ids = sorted(
            chellow.bill_importer.get_bill_import_ids(batch),
            reverse=True)
        parser_names = chellow.bill_importer.find_parser_names()
        return make_response(
            render_template(
                'supplier_batch.html', batch=batch, importer_ids=importer_ids,
                parser_names=parser_names), 400)


@views.route('/supplier_batches/<int:batch_id>/upload_file')
def supplier_batch_upload_file_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    parser_names = chellow.bill_importer.find_parser_names()
    bf = g.sess.query(BatchFile).join(Batch).filter(
        Batch.contract == batch.contract).order_by(
        BatchFile.upload_timestamp.desc()).first()
    default_parser_name = bf.parser_name if bf is not None else None

    return render_template(
        'supplier_batch_upload_file.html', batch=batch,
        parser_names=parser_names, default_parser_name=default_parser_name)


@views.route('/supplier_batches/<int:batch_id>/upload_file', methods=['POST'])
def supplier_batch_upload_file_post(batch_id):
    batch = None
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        file_item = request.files["import_file"]
        parser_name = req_str('parser_name')

        filename = file_item.filename
        if filename == '':
            raise BadRequest('No file selected')

        batch_file = batch.insert_file(
            g.sess, filename, file_item.stream.read(), parser_name)
        g.sess.commit()
        return chellow_redirect(
            f"/supplier_batches/{batch.id}#batch_file_{batch_file.id}", 303)
    except BadRequest as e:
        flash(e.description)
        parser_names = chellow.bill_importer.find_parser_names()
        return make_response(
            render_template(
                'supplier_batch_upload_file.html', batch=batch,
                parser_names=parser_names), 400)


@views.route('/supplier_batch_files/<int:file_id>')
def supplier_batch_file_get(file_id):
    batch_file = BatchFile.get_by_id(g.sess, file_id)
    return render_template('supplier_batch_file.html', batch_file=batch_file)


@views.route('/supplier_batch_files/<int:file_id>/download')
def supplier_batch_file_download_get(file_id):
    batch_file = BatchFile.get_by_id(g.sess, file_id)

    output = make_response(batch_file.data)
    output.headers["Content-Disposition"] = \
        f'attachment; filename="{batch_file.filename}"'
    output.headers["Content-type"] = "application/octet-stream"
    return output


@views.route('/supplier_batch_files/<int:file_id>/edit')
def supplier_batch_file_edit_get(file_id):
    batch_file = BatchFile.get_by_id(g.sess, file_id)
    parser_names = chellow.bill_importer.find_parser_names()
    return render_template(
        'supplier_batch_file_edit.html',
        batch_file=batch_file, parser_names=parser_names)


@views.route('/supplier_batch_files/<int:file_id>/edit', methods=['POST'])
def supplier_batch_file_edit_post(file_id):
    batch_file = None
    try:
        batch_file = BatchFile.get_by_id(g.sess, file_id)

        if 'delete' in request.values:
            batch_id = batch_file.batch.id
            batch_file.delete(g.sess)
            g.sess.commit()
            flash("Deletion successful")
            return chellow_redirect(f"/supplier_batches/{batch_id}", 303)

        else:
            parser_name = req_str('parser_name')
            batch_file.update(parser_name)
            g.sess.commit()
            flash("Update successful")
            return chellow_redirect(
                f"/supplier_batch_files/{batch_file.id}", 303)

    except BadRequest as e:
        flash(e.description)
        parser_names = chellow.bill_importer.find_parser_names()
        return make_response(
            render_template(
                'supplier_batch_file_edit.html', batch_file=batch_file,
                parser_names=parser_names), 400)


@views.route('/hh_data/<int:datum_id>/edit')
def hh_datum_edit_get(datum_id):
    hh = HhDatum.get_by_id(g.sess, datum_id)
    return render_template('hh_datum_edit.html', hh=hh)


@views.route('/hh_data/<int:datum_id>/edit', methods=['POST'])
def hh_datum_edit_post(datum_id):
    try:
        hh = HhDatum.get_by_id(g.sess, datum_id)
        channel_id = hh.channel.id
        if 'delete' in request.values:
            hh.channel.delete_data(g.sess, hh.start_date, hh.start_date)
            g.sess.commit()
            return chellow_redirect('/channels/' + str(channel_id), 303)
        else:
            value = req_decimal('value')
            status = req_str('status')
            channel = hh.channel
            era = channel.era
            imp_mpan_core = era.imp_mpan_core
            exp_mpan_core = era.exp_mpan_core
            mpan_core = imp_mpan_core if channel.imp_related else exp_mpan_core
            HhDatum.insert(
                g.sess, [
                    {
                        'mpan_core': mpan_core,
                        'channel_type': channel.channel_type,
                        'start_date': hh.start_date, 'value': value,
                        'status': status}])
            g.sess.commit()
            return chellow_redirect('/channels/' + str(channel_id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(render_template('hh_datum_edit.html', hh=hh), 400)


@views.route('/sites/<int:site_id>/hh_data')
def site_hh_data_get(site_id):
    caches = {}
    site = Site.get_by_id(g.sess, site_id)

    year = req_int('year')
    month = req_int('month')
    start_date, finish_date = next(
        c_months_u(start_year=year, start_month=month, months=1))

    supplies = g.sess.query(Supply).join(Era).join(SiteEra).join(Source). \
        filter(
            SiteEra.site == site, SiteEra.is_physical == true(),
            Era.start_date <= finish_date, or_(
                Era.finish_date == null(), Era.finish_date >= start_date),
            Source.code != 'sub').order_by(Supply.id).distinct().options(
            joinedload(Supply.source), joinedload(Supply.generator_type)).all()

    data = iter(
        g.sess.query(HhDatum).join(Channel).join(Era).filter(
            Channel.channel_type == 'ACTIVE',
            Era.supply_id.in_([s.id for s in supplies]),
            HhDatum.start_date >= start_date,
            HhDatum.start_date <= finish_date).order_by(
            HhDatum.start_date, Era.supply_id).options(
            joinedload(HhDatum.channel).joinedload(Channel.era).
            joinedload(Era.supply).joinedload(Supply.source)))
    datum = next(data, None)

    hh_data = []
    for hh_date in hh_range(caches, start_date, finish_date):
        sups = []
        hh_dict = {
            'start_date': hh_date, 'supplies': sups, 'export_kwh': 0,
            'import_kwh': 0, 'parasitic_kwh': 0, 'generated_kwh': 0,
            'third_party_import_kwh': 0, 'third_party_export_kwh': 0}
        hh_data.append(hh_dict)
        for supply in supplies:
            sup_hh = {}
            sups.append(sup_hh)
            while datum is not None and datum.start_date == hh_date and \
                    datum.channel.era.supply_id == supply.id:
                channel = datum.channel
                imp_related = channel.imp_related
                hh_float_value = float(datum.value)
                source_code = channel.era.supply.source.code

                prefix = 'import_' if imp_related else 'export_'
                sup_hh[prefix + 'kwh'] = datum.value
                sup_hh[prefix + 'status'] = datum.status

                if not imp_related and source_code in ('net', 'gen-net'):
                    hh_dict['export_kwh'] += hh_float_value
                if imp_related and source_code in ('net', 'gen-net'):
                    hh_dict['import_kwh'] += hh_float_value
                if (imp_related and source_code == 'gen') or \
                        (not imp_related and source_code == 'gen-net'):
                    hh_dict['generated_kwh'] += hh_float_value
                if (not imp_related and source_code == 'gen') or \
                        (imp_related and source_code == 'gen-net'):
                    hh_dict['parasitic_kwh'] += hh_float_value
                if (imp_related and source_code == '3rd-party') or \
                        (not imp_related and
                            source_code == '3rd-party-reverse'):
                    hh_dict['third_party_import_kwh'] += hh_float_value
                if (not imp_related and source_code == '3rd-party') or \
                        (imp_related and
                            source_code == '3rd-party-reverse'):
                    hh_dict['third_party_export_kwh'] += hh_float_value
                datum = next(data, None)

        hh_dict['displaced_kwh'] = hh_dict['generated_kwh'] - \
            hh_dict['export_kwh'] - hh_dict['parasitic_kwh']
        hh_dict['used_kwh'] = sum(
            (
                hh_dict['import_kwh'], hh_dict['displaced_kwh'],
                hh_dict['third_party_import_kwh'] -
                hh_dict['third_party_export_kwh']))

    return render_template(
        'site_hh_data.html', site=site, supplies=supplies, hh_data=hh_data)


@views.route('/sites/<int:site_id>')
def site_get(site_id):
    configuration_contract = Contract.get_non_core_by_name(
        g.sess, 'configuration')
    site = Site.get_by_id(g.sess, site_id)

    eras = g.sess.query(Era).join(SiteEra).filter(SiteEra.site == site). \
        order_by(Era.supply_id, Era.start_date.desc()).all()

    groups = []
    for idx, era in enumerate(eras):
        if idx == 0 or eras[idx - 1].supply_id != era.supply_id:
            if era.pc.code == '00':
                meter_cat = 'HH'
            elif len(era.channels) > 0:
                meter_cat = 'AMR'
            elif era.mtc.meter_type.code in ['UM', 'PH']:
                meter_cat = 'Unmetered'
            else:
                meter_cat = 'NHH'

            groups.append(
                {
                    'last_era': era, 'is_ongoing': era.finish_date is None,
                    'meter_category': meter_cat})

        if era == eras[-1] or era.supply_id != eras[idx + 1]:
            groups[-1]['first_era'] = era

    groups = sorted(groups, key=itemgetter('is_ongoing'), reverse=True)

    g_eras = g.sess.query(GEra).join(SiteGEra).filter(
        SiteGEra.site == site).order_by(
        GEra.g_supply_id, GEra.start_date.desc()).all()

    g_groups = []
    for idx, g_era in enumerate(g_eras):
        if idx == 0 or g_eras[idx - 1].g_supply_id != g_era.g_supply_id:
            g_groups.append(
                {
                    'last_g_era': g_era,
                    'is_ongoing': g_era.finish_date is None})

        if g_era == g_eras[-1] or g_era.g_supply_id != g_eras[idx + 1]:
            g_groups[-1]['first_g_era'] = g_era

    g_groups = sorted(g_groups, key=itemgetter('is_ongoing'), reverse=True)

    now = utc_datetime_now()
    month_start = Datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH
    last_month_start = month_start - relativedelta(months=1)
    last_month_finish = month_start - HH

    properties = configuration_contract.make_properties()
    other_sites = site.find_linked_sites(g.sess, now, now)
    scenarios = g.sess.query(Scenario).order_by(Scenario.name).all()
    return render_template(
        'site.html', site=site, groups=groups, properties=properties,
        other_sites=other_sites, month_start=month_start,
        month_finish=month_finish, last_month_start=last_month_start,
        last_month_finish=last_month_finish, scenarios=scenarios,
        g_groups=g_groups)


@views.route('/downloads')
def downloads_get():
    files = []
    download_path = chellow.dloads.download_path

    for fl in sorted(os.listdir(download_path), reverse=True):
        statinfo = os.stat(os.path.join(download_path, fl))
        files.append(
            {
                'name': fl,
                'last_modified': Datetime.utcfromtimestamp(statinfo.st_mtime),
                'size': statinfo.st_size})

    return render_template('downloads.html', files=files)


@views.route('/downloads', methods=['POST'])
def downloads_post():
    chellow.dloads.reset()
    return chellow_redirect("/downloads", 303)


@views.route('/downloads/<fname>')
def download_get(fname):
    head, name = os.path.split(os.path.normcase(os.path.normpath(fname)))

    download_path = os.path.join(current_app.instance_path, 'downloads')

    full_name = os.path.join(download_path, name)

    def content():
        try:
            with open(full_name, 'rb') as fl:
                while True:
                    data = fl.read(DEFAULT_BUFFER_SIZE)
                    if len(data) == 0:
                        break
                    yield data
        except BaseException:
            yield traceback.format_exc()

    return send_response(content, file_name=name)


@views.route('/downloads/<fname>', methods=['POST'])
def download_post(fname):
    head, name = os.path.split(os.path.normcase(os.path.normpath(fname)))

    download_path = os.path.join(current_app.instance_path, 'downloads')
    full_name = os.path.join(download_path, name)
    os.remove(full_name)
    return chellow_redirect("/downloads", 303)


@views.route('/report_runs')
def report_runs_get():
    runs = g.sess.query(ReportRun).order_by(ReportRun.date_created.desc())

    return render_template('report_runs.html', runs=runs)


@views.route('/report_runs/<int:run_id>')
def report_run_get(run_id):
    run = g.sess.query(ReportRun).filter(ReportRun.id == run_id).one()
    if run.name == 'bill_check':
        row = g.sess.query(ReportRunRow).filter(
            ReportRunRow.report_run == run).order_by(ReportRunRow.id).first()
        elements = []
        summary = {}
        if row is None:
            pass

        else:
            titles = row.data['titles']
            diff_titles = [
                t for t in titles if t.startswith("difference-") and
                t.endswith("-gbp")]
            diff_selects = [
                func.sum(ReportRunRow.data['values'][t].as_float())
                for t in diff_titles]
            sum_diffs = g.sess.query(*diff_selects).filter(
                ReportRunRow.report_run == run).one()

            for t, sum_diff in zip(diff_titles, sum_diffs):
                elem = t[11:-4]
                if elem == 'net':
                    summary['sum_difference'] = sum_diff
                else:
                    elements.append((elem, sum_diff))

            elements.sort(key=lambda x: abs(x[1]), reverse=True)
            elements.insert(0, ('net', summary['sum_difference']))

        if 'element' in request.values:
            element = req_str('element')
        else:
            element = 'net'

        order_by = f'difference-{element}-gbp'
        rows = g.sess.query(ReportRunRow).filter(
            ReportRunRow.report_run == run).order_by(
                func.abs(
                    ReportRunRow.data['values'][order_by].as_float()).desc()
            ).limit(200).all()
        return render_template(
            'report_run_bill_check.html', run=run, rows=rows,
            summary=summary, elements=elements, element=element)

    else:
        order_by = 'row.id'
        ob = ReportRunRow.id
        summary = {}

        rows = g.sess.query(ReportRunRow).filter(
            ReportRunRow.report_run == run).order_by(ob).limit(200).all()

        return render_template(
            'report_run.html', run=run, rows=rows, order_by=order_by,
            summary=summary)


@views.route('/report_runs/<int:run_id>', methods=['POST'])
def report_run_post(run_id):
    run = g.sess.query(ReportRun).filter(ReportRun.id == run_id).one()
    run.delete(g.sess)
    g.sess.commit()
    return chellow_redirect("/report_runs", 303)


@views.route('/report_runs/<int:run_id>/spreadsheet')
def report_run_spreadsheet_get(run_id):
    run = g.sess.query(ReportRun).filter(ReportRun.id == run_id).one()

    si = StringIO()
    cw = csv.writer(si)

    first_row = g.sess.query(ReportRunRow).filter(
        ReportRunRow.report_run == run).order_by(ReportRunRow.id).first()

    titles = first_row.data['titles']
    cw.writerow(titles)

    for row in g.sess.query(ReportRunRow).filter(
            ReportRunRow.report_run == run).order_by(ReportRunRow.id):
        cw.writerow([csv_make_val(row.data['values'][t]) for t in titles])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = \
        f'attachment; filename="{run.title}"'
    output.headers["Content-type"] = "text/csv"
    return output


@views.route('/report_run_rows/<int:row_id>')
def report_run_row_get(row_id):
    row = g.sess.query(ReportRunRow).filter(ReportRunRow.id == row_id).one()
    raw_data = json.dumps(row.data, sort_keys=True, indent=4)
    tables = []

    if row.report_run.name == 'bill_check':
        values = row.data['values']
        elements = {}
        for t in row.data['values'].keys():
            if t == 'difference-tpr-gbp':
                continue

            if (t.startswith('covered-') or t.startswith('virtual-') or
                    t.startswith('difference-')) and t not in (
                    'covered-from', 'covered-to', 'covered-bills',
                    'covered-problem', 'virtual-problem'):

                toks = t.split('-')
                name = toks[1]
                try:
                    table = elements[name]
                except KeyError:
                    table = elements[name] = {'order': 0}

                if 'titles' not in table:
                    table['titles'] = []
                table['titles'].append(toks[0] + '-' + '-'.join(toks[2:]))
                if 'values' not in table:
                    table['values'] = []
                table['values'].append(values[t])
                if t.startswith('difference-') and t.endswith('-gbp'):
                    table['order'] = abs(values[t])

        for k, v in elements.items():
            if k == 'net':
                continue
            v['name'] = k
            tables.append(v)

        tables.sort(key=lambda t: t['order'], reverse=True)
        return render_template(
            'report_run_row_bill_check.html', row=row, raw_data=raw_data,
            tables=tables)

    else:

        return render_template(
            'report_run_row.html', row=row, raw_data=raw_data, tables=tables)


@views.route('/channel_snags')
def channel_snags_get():
    contract_id = req_int('dc_contract_id')
    contract = Contract.get_dc_by_id(g.sess, contract_id)
    days_hidden = req_int('days_hidden')
    is_ignored = req_bool('is_ignored')

    total_snags = g.sess.query(Snag).join(Channel).join(Era).filter(
        Snag.is_ignored == false(), Era.dc_contract == contract,
        Snag.start_date < utc_datetime_now() -
        relativedelta(days=days_hidden)).count()
    snags = g.sess.query(Snag).join(Channel).join(Era).join(
        Era.site_eras).join(SiteEra.site).filter(
        Snag.is_ignored == is_ignored, Era.dc_contract == contract,
        Snag.start_date < utc_datetime_now() -
        relativedelta(days=days_hidden)).order_by(
        Site.code, Era.id, Snag.start_date, Snag.finish_date,
        Snag.channel_id)
    snag_groups = []
    prev_snag = None
    for snag in islice(snags, 200):
        if prev_snag is None or \
                snag.channel.era != prev_snag.channel.era or \
                snag.start_date != prev_snag.start_date or \
                snag.finish_date != prev_snag.finish_date or \
                snag.description != prev_snag.description:
            era = snag.channel.era
            snag_group = {
                'snags': [],
                'sites': g.sess.query(Site).join(Site.site_eras).filter(
                    SiteEra.era == era).order_by(Site.code),
                'era': era, 'description': snag.description,
                'start_date': snag.start_date,
                'finish_date': snag.finish_date}
            snag_groups.append(snag_group)
        snag_group['snags'].append(snag)
        prev_snag = snag

    return render_template(
        'channel_snags.html', contract=contract, snags=snags,
        total_snags=total_snags, snag_groups=snag_groups,
        is_ignored=is_ignored)


@views.route('/non_core_contracts')
def non_core_contracts_get():
    non_core_contracts = g.sess.query(Contract).join(MarketRole).filter(
        MarketRole.code == 'Z').order_by(Contract.name).all()
    return render_template(
        'non_core_contracts.html', non_core_contracts=non_core_contracts)


@views.route('/non_core_contracts/<int:contract_id>')
def non_core_contract_get(contract_id):
    contract = Contract.get_non_core_by_id(g.sess, contract_id)
    rate_scripts = g.sess.query(RateScript).filter(
        RateScript.contract == contract).order_by(
        RateScript.start_date.desc()).all()
    try:
        import_module('chellow.' + contract.name).get_importer()
        has_auto_importer = True
    except AttributeError:
        has_auto_importer = False
    except ImportError:
        has_auto_importer = False

    return render_template(
        'non_core_contract.html', contract=contract, rate_scripts=rate_scripts,
        has_auto_importer=has_auto_importer)


@views.route('/sites/<int:site_id>/used_graph')
def site_used_graph_get(site_id):
    cache = {}
    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    months = req_int("months")

    finish_date = utc_datetime(finish_year, finish_month) + \
        relativedelta(months=1) - HH
    start_date = utc_datetime(finish_year, finish_month) - \
        relativedelta(months=months-1)

    site = Site.get_by_id(g.sess, site_id)
    supplies = g.sess.query(Supply).join(Era).join(Source).join(SiteEra). \
        filter(
            SiteEra.site == site, not_(Source.code.in_(('sub', 'gen-net')))). \
        distinct().all()

    results = iter(g.sess.query(
        cast(HhDatum.value, Float), HhDatum.start_date, HhDatum.status,
        Channel.imp_related, Source.code).join(Channel).join(Era).join(Supply).
        join(Source).filter(
            Channel.channel_type == 'ACTIVE', HhDatum.start_date >= start_date,
            HhDatum.start_date <= finish_date,
            Supply.id.in_(s.id for s in supplies)).order_by(
                HhDatum.start_date))

    max_scale = 2
    min_scale = 0
    result_data = []
    days = []
    month_list = []
    step = 1

    (
        hh_channel_value, hh_channel_start_date, hh_channel_status,
        is_import, source_code) = next(
        results, (None, None, None, None, None))

    for hh_date in hh_range(cache, start_date, finish_date):
        complete = None
        hh_value = 0

        while hh_channel_start_date == hh_date:
            if (is_import and source_code != '3rd-party-reverse') or \
                    (not is_import and source_code == '3rd-party-reverse'):
                hh_value += hh_channel_value
            else:
                hh_value -= hh_channel_value
            if hh_channel_status == 'A':
                if complete is None:
                    complete = True
            else:
                complete = False
            (
                hh_channel_value, hh_channel_start_date, hh_channel_status,
                is_import, source_code) = next(
                results, (None, None, None, None, None))

        result_data.append(
            {
                'value': hh_value, 'start_date': hh_date,
                'is_complete': complete is True})
        max_scale = max(max_scale, int(math.ceil(hh_value)))
        min_scale = min(min_scale, int(math.floor(hh_value)))

    step = 10 ** int(math.floor(math.log10(max_scale - min_scale)))

    max_height = 300
    scale_factor = float(max_height) / (max_scale - min_scale)
    graph_top = 50
    x_axis = int(graph_top + max_scale * scale_factor)

    for i, hh in enumerate(result_data):
        hh['height'] = int(scale_factor * hh['value'])
        hh_start = hh['start_date']
        if hh_start.hour == 0 and hh_start.minute == 0:
            days.append(
                {
                    'colour': 'red' if hh_start.weekday() > 4 else 'black',
                    'day': hh_start.day})

            if hh_start.day == 15:
                month_list.append({'name': hh_start.strftime("%B"), 'x': i})

    scale_lines = []
    for height in chain(
            range(0, max_scale + 1, step), range(0, min_scale - 1, step * -1)):
        scale_lines.append(
            {
                'height': height, 'y': int(x_axis - height * scale_factor)})

    title = "Electricity use at site " + site.code + " " + site.name + \
            " for " + str(months) + " month" + ('s' if months > 1 else '') + \
            " ending " + finish_date.strftime("%B %Y")

    return render_template(
        'site_used_graph.html', result_data=result_data, graph_left=100,
        graph_top=graph_top, x_axis=x_axis, max_height=max_height, days=days,
        months=month_list, scale_lines=scale_lines, title=title, site=site,
        finish_date=finish_date)


@views.route('/supplies/<int:supply_id>/hh_data')
def supply_hh_data_get(supply_id):
    caches = {}
    months = req_int('months')
    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    supply = Supply.get_by_id(g.sess, supply_id)

    month_pairs = list(
        c_months_u(
            finish_year=finish_year, finish_month=finish_month, months=months))
    start_date, finish_date = month_pairs[0][0], month_pairs[-1][1]

    era = g.sess.query(Era).filter(
        Era.supply == supply, Era.start_date <= finish_date, or_(
            Era.finish_date == null(),
            Era.finish_date >= start_date)).order_by(
        Era.start_date.desc()).first()

    keys = {
        True: {
            'ACTIVE': 'import_active',
            'REACTIVE_IMP': 'import_reactive_imp',
            'REACTIVE_EXP': 'import_reactive_exp'},
        False: {
            'ACTIVE': 'export_active',
            'REACTIVE_IMP': 'export_reactive_imp',
            'REACTIVE_EXP': 'export_reactive_exp'}}

    hh_data = iter(g.sess.query(HhDatum).join(Channel).join(Era).filter(
        Era.supply == supply, HhDatum.start_date >= start_date,
        HhDatum.start_date <= finish_date).order_by(HhDatum.start_date).
        options(joinedload(HhDatum.channel)))
    hh_lines = []

    hh_datum = next(hh_data, None)
    for hh_date in hh_range(caches, start_date, finish_date):
        hh_line = {'timestamp': hh_date}
        hh_lines.append(hh_line)
        while hh_datum is not None and hh_datum.start_date == hh_date:
            channel = hh_datum.channel
            hh_line[keys[channel.imp_related][channel.channel_type]] = hh_datum
            hh_datum = next(hh_data, None)
    return render_template(
        'supply_hh_data.html', supply=supply, era=era, hh_lines=hh_lines,
        start_date=start_date, finish_date=finish_date)


@views.route('/dnos/<int:dno_id>/rate_scripts/<start_date_str>')
def dno_rate_script_get(dno_id, start_date_str):
    dno = Party.get_dno_by_id(g.sess, dno_id)
    start_date = to_utc(Datetime.strptime(start_date_str, '%Y%m%d%H%M'))
    rate_script = None
    for rscript in get_file_scripts(dno.dno_code):
        if rscript[0] == start_date:
            rate_script = rscript
            break
    if rate_script is None:
        raise NotFound()
    return render_template(
        'dno_rate_script.html', dno=dno, rate_script=rate_script)


@views.route('/non_core_contracts/<int:contract_id>/edit')
def non_core_contract_edit_get(contract_id):
    contract = Contract.get_non_core_by_id(g.sess, contract_id)
    return render_template('non_core_contract_edit.html', contract=contract)


@views.route('/non_core_contracts/<int:contract_id>/edit', methods=['POST'])
def non_core_contract_edit_post(contract_id):
    try:
        contract = Contract.get_non_core_by_id(g.sess, contract_id)
        if 'delete' in request.values:
            contract.delete(g.sess)
            g.sess.commit()
            return chellow_redirect('/non_core_contracts', 303)
        if 'update_state' in request.values:
            state = req_zish("state")
            contract.update_state(state)
            g.sess.commit()
            return chellow_redirect(
                '/non_core_contracts/' + str(contract.id), 303)
        else:
            properties = req_zish('properties')
            contract.update_properties(properties)
            g.sess.commit()
            return chellow_redirect(
                '/non_core_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template(
                'non_core_contract_edit.html', contract=contract), 400)


@views.route('/sites/<int:site_id>/months')
def site_months_get(site_id):
    finish_year = req_int('finish_year')
    finish_month = req_int('finish_month')
    site = Site.get_by_id(g.sess, site_id)

    typs = ('imp_net', 'exp_net', 'used', 'displaced', 'imp_gen', 'exp_gen')

    months = []
    for month_start, month_finish in c_months_u(
            finish_year=finish_year, finish_month=finish_month, months=12):
        month = dict(
            (typ, {'md': 0, 'md_date': None, 'kwh': 0}) for typ in typs)
        month['start_date'] = month_start
        month['start_date_ct'] = to_ct(month_start)
        months.append(month)

        for hh in site.hh_data(g.sess, month_start, month_finish):
            for tp in typs:
                if hh[tp] * 2 > month[tp]['md']:
                    month[tp]['md'] = hh[tp] * 2
                    month[tp]['md_date'] = hh['start_date']
                month[tp]['kwh'] += hh[tp]

        month['has_site_snags'] = g.sess.query(Snag).filter(
            Snag.site == site, Snag.start_date <= month_finish,
            or_(
                Snag.finish_date == null(),
                Snag.finish_date > month_start)).count() > 0

    totals = dict((typ, {'md': 0, 'md_date': None, 'kwh': 0}) for typ in typs)

    for month in months:
        for typ in typs:
            if month[typ]['md'] > totals[typ]['md']:
                totals[typ]['md'] = month[typ]['md']
                totals[typ]['md_date'] = month[typ]['md_date']
            totals[typ]['kwh'] += month[typ]['kwh']

    months.append(totals)

    return render_template('site_months.html', site=site, months=months)


@views.route('/supplier_bills/<int:bill_id>')
def supplier_bill_get(bill_id):
    bill = Bill.get_by_id(g.sess, bill_id)
    register_reads = g.sess.query(RegisterRead).filter(
        RegisterRead.bill == bill).order_by(
        RegisterRead.present_date.desc())

    rate_scripts = g.sess.query(RateScript).filter(
        RateScript.contract == bill.batch.contract,
        RateScript.start_date <= bill.finish_date, or_(
            RateScript.finish_date == null(),
            RateScript.finish_date >= bill.start_date)).all()
    fields = {
        'bill': bill,
        'register_reads': register_reads,
        'rate_scripts': rate_scripts
    }
    try:
        breakdown_dict = loads(bill.breakdown)

        raw_lines = []
        for key in ('raw_lines', 'raw-lines'):
            try:
                raw_lines += breakdown_dict[key]
                del breakdown_dict[key]
            except KeyError:
                pass

        rows = set()
        columns = set()
        grid = defaultdict(dict)

        for k, v in tuple(breakdown_dict.items()):
            if k.endswith('-gbp'):
                columns.add('gbp')
                row_name = k[:-4]
                rows.add(row_name)
                grid[row_name]['gbp'] = v
                del breakdown_dict[k]

        for k, v in tuple(breakdown_dict.items()):
            for row_name in sorted(list(rows), key=len, reverse=True):
                if k.startswith(row_name + '-'):
                    col_name = k[len(row_name) + 1:]
                    columns.add(col_name)
                    grid[row_name][col_name] = csv_make_val(v)
                    del breakdown_dict[k]
                    break

        for k, v in breakdown_dict.items():
            pair = k.split('-')
            row_name = '-'.join(pair[:-1])
            column_name = pair[-1]
            rows.add(row_name)
            columns.add(column_name)
            grid[row_name][column_name] = csv_make_val(v)

        column_list = sorted(list(columns))
        for rate_name in [col for col in column_list if col.endswith('rate')]:
            column_list.remove(rate_name)
            column_list.append(rate_name)

        if 'gbp' in column_list:
            column_list.remove('gbp')
            column_list.append('gbp')

        row_list = sorted(list(rows))
        fields.update(
            {
                'raw_lines': raw_lines, 'row_list': row_list,
                'column_list': column_list, 'grid': grid})
    except SyntaxError:
        pass
    return render_template('supplier_bill.html', **fields)


@views.route('/reads/<int:read_id>/edit')
def read_edit_get(read_id):
    read = RegisterRead.get_by_id(g.sess, read_id)
    read_types = g.sess.query(ReadType).order_by(ReadType.code).all()
    tprs = g.sess.query(Tpr).order_by(Tpr.code).all()
    return render_template(
        'read_edit.html', read=read, read_types=read_types, tprs=tprs)


@views.route('/reads/<int:read_id>/edit', methods=['POST'])
def read_edit_post(read_id):
    try:
        read = RegisterRead.get_by_id(g.sess, read_id)
        if 'update' in request.values:
            tpr_id = req_int('tpr_id')
            tpr = Tpr.get_by_id(g.sess, tpr_id)
            coefficient = req_decimal('coefficient')
            units = req_str('units')
            msn = req_str('msn')
            mpan_str = req_str('mpan')
            previous_date = req_date('previous')
            previous_value = req_decimal('previous_value')
            previous_type_id = req_int('previous_type_id')
            previous_type = ReadType.get_by_id(g.sess, previous_type_id)
            present_date = req_date('present')
            present_value = req_decimal('present_value')
            present_type_id = req_int('present_type_id')
            present_type = ReadType.get_by_id(g.sess, present_type_id)

            read.update(
                tpr, coefficient, units, msn, mpan_str, previous_date,
                previous_value, previous_type, present_date, present_value,
                present_type)
            g.sess.commit()
            return chellow_redirect(
                "/supplier_bills/" + str(read.bill.id), 303)
        elif 'delete' in request.values:
            bill = read.bill
            read.delete(g.sess)
            g.sess.commit()
            return chellow_redirect("/supplier_bills/" + str(bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        read_types = g.sess.query(ReadType).order_by(ReadType.code).all()
        tprs = g.sess.query(Tpr).order_by(Tpr.code).all()
        return make_response(
            render_template(
                'read_edit.html', read=read, read_types=read_types, tprs=tprs),
            400)


@views.route('/dc_batches')
def dc_batches_get():
    contract_id = req_int('dc_contract_id')
    contract = Contract.get_dc_by_id(g.sess, contract_id)
    batches = g.sess.query(Batch).filter(Batch.contract == contract).order_by(
        Batch.reference.desc()).all()
    return render_template(
        'dc_batches.html', contract=contract, batches=batches)


@views.route('/dc_batches/<int:batch_id>')
def dc_batch_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    bills = g.sess.query(Bill).filter(Bill.batch == batch).order_by(
        Bill.reference).all()

    config_contract = Contract.get_non_core_by_name(g.sess, 'configuration')
    properties = config_contract.make_properties()
    fields = {'batch': batch, 'bills': bills}
    if 'batch_reports' in properties:
        batch_reports = []
        for report_id in properties['batch_reports']:
            batch_reports.append(Report.get_by_id(g.sess, report_id))
        fields['batch_reports'] = batch_reports
    return render_template('dc_batch.html', **fields)


@views.route('/dc_batches/<int:batch_id>/csv')
def dc_batch_csv_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(
        [
            "HHDC Contract", "Batch Reference", "Bill Reference",
            "Account", "Issued", "From", "To", "kWh", "Net", "VAT", "Gross",
            "Type"])
    for bill in g.sess.query(Bill).filter(Bill.batch == batch).order_by(
            Bill.reference, Bill.start_date).options(
                joinedload(Bill.bill_type)):
        cw.writerow(
            [
                batch.contract.name, batch.reference, bill.reference,
                bill.account, hh_format(bill.issue_date),
                hh_format(bill.start_date), hh_format(bill.finish_date),
                str(bill.kwh), str(bill.net), str(bill.vat), str(bill.gross),
                bill.bill_type.code])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = 'attachment; filename="batch.csv"'
    output.headers["Content-type"] = "text/csv"
    return output


@views.route('/dc_batches/<int:batch_id>', methods=['POST'])
def dc_batch_post(batch_id):
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        if 'import_bills' in request.values:
            import_id = chellow.bill_importer.start_bill_import(batch)
            return chellow_redirect(f"/dc_bill_imports/{import_id}", 303)
        elif 'delete_bills' in request.values:
            g.sess.query(Bill).filter(Bill.batch_id == batch.id).delete(False)
            g.sess.commit()
            return chellow_redirect(f'/dc_batches/{batch.id}', 303)
        elif 'delete_import_bills' in request.values:
            g.sess.query(Bill).filter(Bill.batch_id == batch.id).delete(False)
            g.sess.commit()
            import_id = chellow.bill_importer.start_bill_import(batch)
            return chellow_redirect(f"/dc_bill_imports/{import_id}", 303)
    except BadRequest as e:
        flash(e.description)
        importer_ids = sorted(
            chellow.bill_importer.get_bill_import_ids(batch),
            reverse=True)
        parser_names = chellow.bill_importer.find_parser_names()
        return make_response(
            render_template(
                'dc_batch.html', batch=batch, importer_ids=importer_ids,
                parser_names=parser_names), 400)


@views.route('/supplier_bills/<int:bill_id>/edit')
def supplier_bill_edit_get(bill_id):
    bill_types = g.sess.query(BillType).order_by(BillType.code).all()
    bill = Bill.get_by_id(g.sess, bill_id)
    return render_template(
        'supplier_bill_edit.html', bill=bill, bill_types=bill_types)


@views.route('/supplier_bills/<int:bill_id>/edit', methods=['POST'])
def supplier_bill_edit_post(bill_id):
    try:
        bill = Bill.get_by_id(g.sess, bill_id)
        if 'delete' in request.values:
            batch = bill.batch
            bill.delete(g.sess)
            g.sess.commit()
            return chellow_redirect("/supplier_batches/" + str(batch.id), 303)
        else:
            account = req_str("account")
            reference = req_str("reference")
            issue_date = req_date("issue")
            start_date = req_date("start")
            finish_date = req_date("finish")
            kwh = req_decimal("kwh")
            net = req_decimal("net")
            vat = req_decimal("vat")
            gross = req_decimal("gross")
            type_id = req_int("bill_type_id")
            breakdown_str = req_str("breakdown")
            breakdown = loads(breakdown_str)
            bill_type = BillType.get_by_id(g.sess, type_id)

            bill.update(
                account, reference, issue_date, start_date, finish_date, kwh,
                net, vat, gross, bill_type, breakdown)
            g.sess.commit()
            return chellow_redirect("/supplier_bills/" + str(bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        bill_types = g.sess.query(BillType).order_by(BillType.code).all()
        return make_response(
            render_template(
                'supplier_bill_edit.html', bill=bill, bill_types=bill_types),
            400)


@views.route('/dc_contracts/<int:contract_id>/add_batch')
def dc_batch_add_get(contract_id):
    contract = Contract.get_dc_by_id(g.sess, contract_id)
    batches = g.sess.query(Batch).filter(Batch.contract == contract).order_by(
        Batch.reference.desc())
    next_batch_reference, next_batch_description = \
        contract.get_next_batch_details(g.sess)
    return render_template(
        'dc_batch_add.html', contract=contract, batches=batches,
        next_batch_reference=next_batch_reference,
        next_batch_description=next_batch_description)


@views.route('/dc_contracts/<int:contract_id>/add_batch', methods=['POST'])
def dc_batch_add_post(contract_id):
    try:
        contract = Contract.get_dc_by_id(g.sess, contract_id)
        reference = req_str('reference')
        description = req_str('description')
        batch = contract.insert_batch(g.sess, reference, description)
        g.sess.commit()
        return chellow_redirect("/dc_batches/" + str(batch.id), 303)
    except BadRequest as e:
        flash(e.description)
        batches = g.sess.query(Batch).filter(Batch.contract == contract). \
            order_by(Batch.reference.desc())
        return make_response(
            render_template(
                'dc_batch_add.html', contract=contract, batches=batches),
            400)


@views.route('/dc_batches/<int:batch_id>/edit')
def dc_batch_edit_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    return render_template('dc_batch_edit.html', batch=batch)


@views.route('/dc_batches/<int:batch_id>/edit', methods=['POST'])
def dc_batch_edit_post(batch_id):
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        if 'delete' in request.values:
            contract = batch.contract
            batch.delete(g.sess)
            g.sess.commit()
            return chellow_redirect(
                "/dc_batches?dc_contract_id=" + str(contract.id), 303)
        elif 'delete_bills' in request.values:
            g.sess.query(Bill).filter(Bill.batch == batch).delete(False)
            g.sess.commit()
            return chellow_redirect('/dc_batches/' + str(batch.id), 303)
        else:
            reference = req_str('reference')
            description = req_str('description')
            batch.update(g.sess, reference, description)
            g.sess.commit()
            return chellow_redirect("/dc_batches/" + str(batch.id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template('dc_batch_edit.html', batch=batch), 400)


@views.route('/dc_batches/<int:batch_id>/upload_file')
def dc_batch_upload_file_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    parser_names = chellow.bill_importer.find_parser_names()

    return render_template(
        'dc_batch_upload_file.html', batch=batch, parser_names=parser_names)


@views.route('/dc_batches/<int:batch_id>/upload_file', methods=['POST'])
def dc_batch_upload_file_post(batch_id):
    batch = None
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        file_item = request.files["import_file"]
        parser_name = req_str('parser_name')

        batch_file = batch.insert_file(
            g.sess, file_item.filename, file_item.stream.read(), parser_name)
        g.sess.commit()
        return chellow_redirect(
            f"/dc_batches/{batch.id}#batch_file_{batch_file.id}", 303)
    except BadRequest as e:
        flash(e.description)
        parser_names = chellow.bill_importer.find_parser_names()
        return make_response(
            render_template(
                'dc_batch_upload_file.html', batch=batch,
                parser_names=parser_names), 400)


@views.route('/dc_batch_files/<int:file_id>')
def dc_batch_file_get(file_id):
    batch_file = BatchFile.get_by_id(g.sess, file_id)
    importer_ids = sorted(
        chellow.bill_importer.get_bill_import_ids(batch_file), reverse=True)
    return render_template(
        'dc_batch_file.html', batch_file=batch_file,
        importer_ids=importer_ids)


@views.route('/dc_batch_files/<int:file_id>/download')
def dc_batch_file_download_get(file_id):
    batch_file = BatchFile.get_by_id(g.sess, file_id)

    output = make_response(batch_file.data)
    output.headers["Content-Disposition"] = \
        f'attachment; filename="{batch_file.filename}"'
    output.headers["Content-type"] = "application/octet-stream"
    return output


@views.route('/dc_batch_files/<int:file_id>/edit')
def dc_batch_file_edit_get(file_id):
    batch_file = BatchFile.get_by_id(g.sess, file_id)
    parser_names = chellow.bill_importer.find_parser_names()
    return render_template(
        'dc_batch_file_edit.html', batch_file=batch_file,
        parser_names=parser_names)


@views.route('/dc_batch_files/<int:file_id>/edit', methods=['POST'])
def dc_batch_file_edit_post(file_id):
    batch_file = None
    try:
        batch_file = BatchFile.get_by_id(g.sess, file_id)

        if 'delete' in request.values:
            batch_id = batch_file.batch.id
            batch_file.delete(g.sess)
            g.sess.commit()
            flash("Deletion successful")
            return chellow_redirect(f"/dc_batches/{batch_id}", 303)

        else:
            parser_name = req_str('parser_name')
            batch_file.update(parser_name)
            g.sess.commit()
            flash("Update successful")
            return chellow_redirect(
                f"/dc_batch_files/{batch_file.id}", 303)

    except BadRequest as e:
        flash(e.description)
        parser_names = chellow.bill_importer.find_parser_names()
        return make_response(
            render_template(
                'dc_batch_file_edit.html', batch_file=batch_file,
                parser_names=parser_names), 400)


@views.route('/dc_bill_imports/<int:import_id>')
def dc_bill_import_get(import_id):
    importer = chellow.bill_importer.get_bill_import(import_id)
    batch = Batch.get_by_id(g.sess, importer.batch_id)
    fields = {'batch': batch}
    if importer is not None:
        imp_fields = importer.make_fields()
        if 'successful_bills' in imp_fields and \
                len(imp_fields['successful_bills']) > 0:
            fields['successful_max_registers'] = max(
                len(bill['reads']) for bill in imp_fields['successful_bills'])
        fields.update(imp_fields)
        fields['status'] = importer.status()
    return render_template('dc_bill_import.html', **fields)


@views.route('/dc_bills/<int:bill_id>')
def dc_bill_get(bill_id):
    bill = Bill.get_by_id(g.sess, bill_id)
    fields = {'bill': bill}
    try:
        breakdown_dict = loads(bill.breakdown)

        raw_lines = []
        for key in ('raw_lines', 'raw-lines'):
            try:
                raw_lines += breakdown_dict[key]
                del breakdown_dict[key]
            except KeyError:
                pass

        rows = set()
        columns = set()
        grid = defaultdict(dict)

        for k, v in tuple(breakdown_dict.items()):
            if k.endswith('-gbp'):
                columns.add('gbp')
                row_name = k[:-4]
                rows.add(row_name)
                grid[row_name]['gbp'] = v
                del breakdown_dict[k]

        for k, v in tuple(breakdown_dict.items()):
            for row_name in sorted(list(rows), key=len, reverse=True):
                if k.startswith(row_name + '-'):
                    col_name = k[len(row_name) + 1:]
                    columns.add(col_name)
                    grid[row_name][col_name] = csv_make_val(v)
                    del breakdown_dict[k]
                    break

        for k, v in breakdown_dict.items():
            pair = k.split('-')
            row_name = '-'.join(pair[:-1])
            column_name = pair[-1]
            rows.add(row_name)
            columns.add(column_name)
            grid[row_name][column_name] = csv_make_val(v)

        column_list = sorted(list(columns))
        for rate_name in [col for col in column_list if col.endswith('rate')]:
            column_list.remove(rate_name)
            column_list.append(rate_name)

        if 'gbp' in column_list:
            column_list.remove('gbp')
            column_list.append('gbp')

        row_list = sorted(list(rows))
        fields.update(
            {
                'raw_lines': raw_lines, 'row_list': row_list,
                'column_list': column_list, 'grid': grid})
    except SyntaxError:
        pass
    return render_template('dc_bill.html', **fields)


@views.route('/dc_bills/<int:bill_id>/edit')
def dc_bill_edit_get(bill_id):
    bill = Bill.get_by_id(g.sess, bill_id)
    bill_types = g.sess.query(BillType).order_by(BillType.code)
    return render_template(
        'dc_bill_edit.html', bill=bill, bill_types=bill_types)


@views.route('/dc_bills/<int:bill_id>/edit', methods=["POST"])
def dc_bill_edit_post(bill_id):
    try:
        bill = Bill.get_by_id(g.sess, bill_id)
        if 'delete' in request.values:
            bill.delete(g.sess)
            g.sess.commit()
            return chellow_redirect("/dc_batches/" + str(bill.batch.id), 303)
        else:
            account = req_str('account')
            reference = req_str('reference')
            issue_date = req_date('issue')
            start_date = req_date('start')
            finish_date = req_date('finish')
            kwh = req_decimal('kwh')
            net = req_decimal('net')
            vat = req_decimal('vat')
            gross = req_decimal('gross')
            type_id = req_int('bill_type_id')
            breakdown = req_zish('breakdown')
            bill_type = BillType.get_by_id(g.sess, type_id)

            bill.update(
                account, reference, issue_date, start_date, finish_date, kwh,
                net, vat, gross, bill_type, breakdown)
            g.sess.commit()
            return chellow_redirect("/dc_bills/" + str(bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        bill_types = g.sess.query(BillType).order_by(BillType.code).all()
        return render_template(
            'dc_bill_edit.html', bill=bill, bill_types=bill_types)


@views.route('/mop_contracts/<int:contract_id>/add_batch')
def mop_batch_add_get(contract_id):
    contract = Contract.get_mop_by_id(g.sess, contract_id)
    batches = g.sess.query(Batch).filter(Batch.contract == contract).order_by(
        Batch.reference.desc())
    next_batch_reference, next_batch_description = \
        contract.get_next_batch_details(g.sess)
    return render_template(
        'mop_batch_add.html', contract=contract, batches=batches,
        next_batch_reference=next_batch_reference,
        next_batch_description=next_batch_description)


@views.route('/mop_contracts/<int:contract_id>/add_batch', methods=['POST'])
def mop_batch_add_post(contract_id):
    try:
        contract = Contract.get_mop_by_id(g.sess, contract_id)
        reference = req_str("reference")
        description = req_str("description")

        batch = contract.insert_batch(g.sess, reference, description)
        g.sess.commit()
        return chellow_redirect("/mop_batches/" + str(batch.id), 303)
    except BadRequest as e:
        flash(e.description)
        batches = g.sess.query(Batch).filter(Batch.contract == contract). \
            order_by(Batch.reference.desc())
        return make_response(
            render_template(
                'mop_batch_add.html', contract=contract, batches=batches), 303)


@views.route('/mop_batches/<int:batch_id>/edit')
def mop_batch_edit_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    return render_template('mop_batch_edit.html', batch=batch)


@views.route('/mop_batches/<int:batch_id>/edit', methods=['POST'])
def mop_batch_edit_post(batch_id):
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        if 'delete' in request.values:
            contract = batch.contract
            batch.delete(g.sess)
            g.sess.commit()
            return chellow_redirect("/mop_contracts/" + str(contract.id), 303)
        elif 'delete_bills' in request.values:
            g.sess.query(Bill).filter(Bill.batch_id == batch.id).delete(False)
            g.sess.commit()
            return chellow_redirect('/mop_batches/' + str(batch.id), 303)
        else:
            reference = req_str('reference')
            description = req_str('description')
            batch.update(g.sess, reference, description)
            g.sess.commit()
            return chellow_redirect("/mop_batches/" + str(batch.id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template('mop_batch_edit.html', batch=batch)


@views.route('/mop_batches/<int:batch_id>')
def mop_batch_get(batch_id):
    batch = Batch.get_mop_by_id(g.sess, batch_id)
    bills = g.sess.query(Bill).filter(Bill.batch == batch).order_by(
        Bill.reference).all()

    config_contract = Contract.get_non_core_by_name(g.sess, 'configuration')
    properties = config_contract.make_properties()
    fields = {'batch': batch, 'bills': bills}
    if 'batch_reports' in properties:
        batch_reports = []
        for report_id in properties['batch_reports']:
            batch_reports.append(Report.get_by_id(g.sess, report_id))
        fields['batch_reports'] = batch_reports
    return render_template('mop_batch.html', **fields)


@views.route('/mop_batches/<int:batch_id>', methods=['POST'])
def mop_batch_post(batch_id):
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        if 'import_bills' in request.values:
            import_id = chellow.bill_importer.start_bill_import(batch)
            return chellow_redirect(f"/mop_bill_imports/{import_id}", 303)
        elif 'delete_bills' in request.values:
            g.sess.query(Bill).filter(Bill.batch_id == batch.id).delete(False)
            g.sess.commit()
            return chellow_redirect(f'/mop_batches/{batch.id}', 303)
        elif 'delete_import_bills' in request.values:
            g.sess.query(Bill).filter(Bill.batch_id == batch.id).delete(False)
            g.sess.commit()
            import_id = chellow.bill_importer.start_bill_import(batch)
            return chellow_redirect(f"/mop_bill_imports/{import_id}", 303)
    except BadRequest as e:
        flash(e.description)
        importer_ids = sorted(
            chellow.bill_importer.get_bill_import_ids(batch),
            reverse=True)
        parser_names = chellow.bill_importer.find_parser_names()
        return make_response(
            render_template(
                'mop_batch.html', batch=batch, importer_ids=importer_ids,
                parser_names=parser_names), 400)


@views.route('/mop_batches/<int:batch_id>/csv')
def mop_batch_csv_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(
        [
            "MOP Contract", "Batch Reference", "Bill Reference",
            "Account", "Issued", "From", "To", "kWh", "Net", "VAT", "Gross",
            "Type"])
    for bill in g.sess.query(Bill).filter(Bill.batch == batch).order_by(
            Bill.reference, Bill.start_date).options(
                joinedload(Bill.bill_type)):
        cw.writerow(
            [
                batch.contract.name, batch.reference, bill.reference,
                bill.account, hh_format(bill.issue_date),
                hh_format(bill.start_date), hh_format(bill.finish_date),
                str(bill.kwh), str(bill.net), str(bill.vat), str(bill.gross),
                bill.bill_type.code])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = 'attachment; filename="batch.csv"'
    output.headers["Content-type"] = "text/csv"
    return output


@views.route('/mop_batches/<int:batch_id>/upload_file')
def mop_batch_upload_file_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    parser_names = chellow.bill_importer.find_parser_names()

    return render_template(
        'mop_batch_upload_file.html', batch=batch, parser_names=parser_names)


@views.route('/mop_batches/<int:batch_id>/upload_file', methods=['POST'])
def mop_batch_upload_file_post(batch_id):
    batch = None
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        file_item = request.files["import_file"]
        parser_name = req_str('parser_name')

        batch_file = batch.insert_file(
            g.sess, file_item.filename, file_item.stream.read(), parser_name)
        g.sess.commit()
        return chellow_redirect(
            f"/mop_batches/{batch.id}#batch_file_{batch_file.id}", 303)
    except BadRequest as e:
        flash(e.description)
        parser_names = chellow.bill_importer.find_parser_names()
        return make_response(
            render_template(
                'mop_batch_upload_file.html', batch=batch,
                parser_names=parser_names), 400)


@views.route('/mop_batch_files/<int:file_id>')
def mop_batch_file_get(file_id):
    batch_file = BatchFile.get_by_id(g.sess, file_id)
    importer_ids = sorted(
        chellow.bill_importer.get_bill_import_ids(batch_file), reverse=True)
    return render_template(
        'mop_batch_file.html', batch_file=batch_file,
        importer_ids=importer_ids)


@views.route('/mop_batch_files/<int:file_id>/download')
def mop_batch_file_download_get(file_id):
    batch_file = BatchFile.get_by_id(g.sess, file_id)

    output = make_response(batch_file.data)
    output.headers["Content-Disposition"] = \
        f'attachment; filename="{batch_file.filename}"'
    output.headers["Content-type"] = "application/octet-stream"
    return output


@views.route('/mop_batch_files/<int:file_id>/edit')
def mop_batch_file_edit_get(file_id):
    batch_file = BatchFile.get_by_id(g.sess, file_id)
    parser_names = chellow.bill_importer.find_parser_names()
    return render_template(
        'mop_batch_file_edit.html', batch_file=batch_file,
        parser_names=parser_names)


@views.route('/mop_batch_files/<int:file_id>/edit', methods=['POST'])
def mop_batch_file_edit_post(file_id):
    batch_file = None
    try:
        batch_file = BatchFile.get_by_id(g.sess, file_id)

        if 'delete' in request.values:
            batch_id = batch_file.batch.id
            batch_file.delete(g.sess)
            g.sess.commit()
            flash("Deletion successful")
            return chellow_redirect(f"/mop_batches/{batch_id}", 303)

        else:
            parser_name = req_str('parser_name')
            batch_file.update(parser_name)
            g.sess.commit()
            flash("Update successful")
            return chellow_redirect(
                f"/mop_batch_files/{batch_file.id}", 303)

    except BadRequest as e:
        flash(e.description)
        parser_names = chellow.bill_importer.find_parser_names()
        return make_response(
            render_template(
                'mop_batch_file_edit.html', batch_file=batch_file,
                parser_names=parser_names), 400)


@views.route('/mop_bill_imports/<int:import_id>')
def mop_bill_import_get(import_id):
    importer = chellow.bill_importer.get_bill_import(import_id)
    batch = Batch.get_by_id(g.sess, importer.batch_id)
    fields = {'batch': batch}
    if importer is not None:
        imp_fields = importer.make_fields()
        if 'successful_bills' in imp_fields and \
                len(imp_fields['successful_bills']) > 0:
            fields['successful_max_registers'] = max(
                len(bill['reads']) for bill in imp_fields['successful_bills'])
        fields.update(imp_fields)
        fields['status'] = importer.status()
    return render_template('mop_bill_import.html', **fields)


@views.route('/mop_batches/<int:batch_id>/add_bill')
def mop_bill_add_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    bill_types = g.sess.query(BillType).order_by(BillType.code)
    bills = g.sess.query(Bill).filter(Bill.batch == batch).order_by(
        Bill.start_date)
    return render_template(
        'mop_bill_add.html', batch=batch, bill_types=bill_types, bills=bills)


@views.route('/mop_batches/<int:batch_id>/add_bill', methods=['POST'])
def mop_bill_add_post(batch_id):
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        mpan_core = req_str("mpan_core")
        mpan_core = parse_mpan_core(mpan_core)
        account = req_str("account")
        reference = req_str("reference")
        issue_date = req_date("issue")
        start_date = req_hh_date("start")
        finish_date = req_hh_date("finish")
        kwh = req_decimal("kwh")
        net = req_decimal("net")
        vat = req_decimal("vat")
        gross = req_decimal("gross")
        bill_type_id = req_int("bill_type_id")
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        breakdown_str = req_str("breakdown")

        breakdown = loads(breakdown_str)
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        bill = batch.insert_bill(
            g.sess, account, reference, issue_date, start_date, finish_date,
            kwh, net, vat, gross, bill_type, breakdown,
            Supply.get_by_mpan_core(g.sess, mpan_core))
        g.sess.commit()
        return chellow_redirect("/mop_bills/" + str(bill.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        bill_types = g.sess.query(BillType).order_by(BillType.code)
        bills = g.sess.query(Bill).filter(Bill.batch == batch).order_by(
            Bill.start_date)
        return make_response(
            render_template(
                'mop_bill_add.html', batch=batch, bill_types=bill_types,
                bills=bills), 400)


@views.route('/meter_payment_types')
def meter_payment_types_get():
    meter_payment_types = g.sess.query(MeterPaymentType).order_by(
        MeterPaymentType.code).all()
    return render_template(
        'meter_payment_types.html', meter_payment_types=meter_payment_types)


@views.route('/meter_payment_types/<int:type_id>')
def meter_payment_type_get(type_id):
    meter_payment_type = MeterPaymentType.get_by_id(g.sess, type_id)
    return render_template(
        'meter_payment_type.html', meter_payment_type=meter_payment_type)


@views.route('/non_core_contracts/<int:contract_id>/add_rate_script')
def non_core_rate_script_add_get(contract_id):
    now = utc_datetime_now()
    initial_date = utc_datetime(now.year, now.month)
    contract = Contract.get_non_core_by_id(g.sess, contract_id)
    return render_template(
        'non_core_rate_script_add.html', now=now, initial_date=initial_date,
        contract=contract)


@views.route(
    '/non_core_contracts/<int:contract_id>/add_rate_script', methods=['POST'])
def non_core_rate_script_add_post(contract_id):
    try:
        contract = Contract.get_non_core_by_id(g.sess, contract_id)
        start_date = req_date('start')
        rate_script = contract.insert_rate_script(g.sess, start_date, {})
        g.sess.commit()
        return chellow_redirect(
            '/non_core_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = utc_datetime_now()
        initial_date = utc_datetime(now.year, now.month)
        return make_response(
            render_template(
                'non_core_rate_script_add.html', now=now,
                initial_date=initial_date, contract=contract), 400)


@views.route('/non_core_rate_scripts/<int:rs_id>')
def non_core_rate_script_get(rs_id):
    rate_script = RateScript.get_non_core_by_id(g.sess, rs_id)
    contract = rate_script.contract
    next_rate_script = g.sess.query(RateScript).filter(
        RateScript.contract == contract,
        RateScript.start_date > rate_script.start_date).order_by(
        RateScript.start_date).first()
    previous_rate_script = g.sess.query(RateScript).filter(
        RateScript.contract == contract,
        RateScript.start_date < rate_script.start_date).order_by(
        RateScript.start_date.desc()).first()
    return render_template(
        'non_core_rate_script.html', rate_script=rate_script,
        previous_rate_script=previous_rate_script,
        next_rate_script=next_rate_script)


@views.route('/non_core_rate_scripts/<int:rs_id>/edit')
def non_core_rate_script_edit_get(rs_id):
    rate_script = RateScript.get_non_core_by_id(g.sess, rs_id)
    rs_example_func = chellow.computer.contract_func(
            {}, rate_script.contract, 'rate_script_example')
    rs_example = None if rs_example_func is None else rs_example_func()
    return render_template(
        'non_core_rate_script_edit.html', rate_script=rate_script,
        rate_script_example=rs_example)


@views.route('/non_core_rate_scripts/<int:rs_id>/edit', methods=['POST'])
def non_core_rate_script_edit_post(rs_id):
    try:
        rate_script = RateScript.get_non_core_by_id(g.sess, rs_id)
        contract = rate_script.contract
        if 'delete' in request.values:
            contract.delete_rate_script(g.sess, rate_script)
            g.sess.commit()
            return chellow_redirect(
                '/non_core_contracts/' + str(contract.id), 303)
        else:
            script = req_zish('script')
            start_date = req_hh_date('start')
            if 'has_finished' in request.values:
                finish_date = req_date('finish')
            else:
                finish_date = None
            contract.update_rate_script(
                g.sess, rate_script, start_date, finish_date, script)
            g.sess.commit()
            return chellow_redirect(
                '/non_core_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template(
                'non_core_rate_script_edit.html', rate_script=rate_script),
            400)


@views.route('/supplier_batches/<int:batch_id>/add_bill')
def supplier_bill_add_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    bill_types = g.sess.query(BillType).order_by(BillType.code)
    supply = start_date = account = None
    normal_bill_type_id = g.sess.query(BillType.id).filter(
        BillType.code == 'N').scalar()
    try:
        if 'mpan_core' in request.values:
            mpan_core_raw = req_str('mpan_core')
            mpan_core = mpan_core_raw.strip()
            supply = Supply.get_by_mpan_core(g.sess, mpan_core)
            latest_bill = g.sess.query(Bill).join(Batch).join(Contract).join(
                MarketRole).filter(
                Bill.supply == supply, MarketRole.code == 'X').order_by(
                Bill.start_date.desc()).first()
            if latest_bill is not None:
                start_date = latest_bill.finish_date + HH
                account = latest_bill.account
        return render_template(
            'supplier_bill_add.html', batch=batch, bill_types=bill_types,
            start_date=start_date, account=account, supply=supply,
            normal_bill_type_id=normal_bill_type_id)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template(
                'supplier_bill_add.html', batch=batch, bill_types=bill_types,
                supply=supply, start_date=start_date, account=account,
                normal_bill_type_id=normal_bill_type_id), 400)


@views.route('/supplier_batches/<int:batch_id>/add_bill', methods=['POST'])
def supplier_bill_add_post(batch_id):
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        mpan_core = req_str('mpan_core')
        mpan_core = parse_mpan_core(mpan_core)
        account = req_str('account')
        reference = req_str('reference')
        issue_date = req_date('issue')
        start_date = req_hh_date('start')
        finish_date = req_hh_date('finish')
        kwh = req_decimal('kwh')
        net = req_decimal('net')
        vat = req_decimal('vat')
        gross = req_decimal('gross')
        bill_type_id = req_int('bill_type_id')
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        breakdown_str = req_str('breakdown')
        breakdown = loads(breakdown_str)
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        bill = batch.insert_bill(
            g.sess, account, reference, issue_date, start_date, finish_date,
            kwh, net, vat, gross, bill_type, breakdown,
            Supply.get_by_mpan_core(g.sess, mpan_core))
        g.sess.commit()
        return chellow_redirect('/supplier_bills/' + str(bill.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        bill_types = g.sess.query(BillType).order_by(BillType.code)
        bills = g.sess.query(Bill).filter(Bill.batch == batch).order_by(
            Bill.start_date)
        return make_response(
            render_template(
                'supplier_bill_add.html', batch=batch, bill_types=bill_types,
                bills=bills), 400)


@views.route('/supplier_batches/<int:batch_id>/edit')
def supplier_batch_edit_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    return render_template('supplier_batch_edit.html', batch=batch)


@views.route('/supplier_batches/<int:batch_id>/edit', methods=['POST'])
def supplier_batch_edit_post(batch_id):
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        if 'update' in request.values:
            reference = req_str('reference')
            description = req_str('description')
            batch.update(g.sess, reference, description)
            g.sess.commit()
            return chellow_redirect("/supplier_batches/" + str(batch.id), 303)
        elif 'delete' in request.values:
            contract_id = batch.contract.id
            batch.delete(g.sess)
            g.sess.commit()
            return chellow_redirect(
                '/supplier_batches?supplier_contract_id=' +
                str(contract_id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template('supplier_batch_edit.html', batch=batch), 400)


@views.route('/supplier_batches/<int:batch_id>/csv')
def supplier_batch_csv_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(
        [
            "Supplier Contract", "Batch Reference", "Bill Reference",
            "Account", "Issued", "From", "To", "kWh", "Net", "VAT", "Gross",
            "Type"])
    for bill in g.sess.query(Bill).filter(Bill.batch == batch).order_by(
            Bill.reference, Bill.start_date).options(
                joinedload(Bill.bill_type)):
        cw.writerow(
            [
                batch.contract.name, batch.reference, bill.reference,
                bill.account, hh_format(bill.issue_date),
                hh_format(bill.start_date), hh_format(bill.finish_date),
                str(bill.kwh), str(bill.net), str(bill.vat), str(bill.gross),
                bill.bill_type.code])

    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = 'attachment; filename="batch.csv"'
    output.headers["Content-type"] = "text/csv"
    return output


@views.route('/mop_batches')
def mop_batches_get():
    contract_id = req_int('mop_contract_id')
    contract = Contract.get_mop_by_id(g.sess, contract_id)
    batches = g.sess.query(Batch).filter(Batch.contract == contract).order_by(
        Batch.reference.desc()).all()
    return render_template(
        'mop_batches.html', contract=contract, batches=batches)


@views.route('/supplies/<int:supply_id>/notes')
def supply_notes_get(supply_id):
    supply = Supply.get_by_id(g.sess, supply_id)

    if len(supply.note.strip()) > 0:
        note_str = supply.note
    else:
        note_str = "{'notes': []}"
    supply_note = eval(note_str)

    return render_template(
        'supply_notes.html', supply=supply, supply_note=supply_note)


@views.route('/supplies/<int:supply_id>/notes/add')
def supply_note_add_get(supply_id):
    supply = Supply.get_by_id(g.sess, supply_id)
    return render_template('supply_note_add.html', supply=supply)


@views.route('/supplies/<int:supply_id>/notes/add', methods=['POST'])
def supply_note_add_post(supply_id):
    try:
        supply = Supply.get_by_id(g.sess, supply_id)
        body = req_str('body')
        category = req_str('category')
        is_important = req_bool('is_important')
        if len(supply.note.strip()) == 0:
            supply.note = "{'notes': []}"
        note_dict = eval(supply.note)
        note_dict['notes'].append(
            {
                'category': category, 'is_important': is_important,
                'body': body})
        supply.note = str(note_dict)
        g.sess.commit()
        return chellow_redirect('/supplies/' + str(supply_id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template('supply_note_add.html', supply=supply), 400)


@views.route('/supplies/<int:supply_id>/notes/<int:index>/edit')
def supply_note_edit_get(supply_id, index):
    supply = Supply.get_by_id(g.sess, supply_id)
    supply_note = eval(supply.note)
    note = supply_note['notes'][index]
    note['index'] = index
    return render_template('supply_note_edit.html', supply=supply, note=note)


@views.route(
    '/supplies/<int:supply_id>/notes/<int:index>/edit', methods=['POST'])
def supply_note_edit_post(supply_id, index):
    try:
        supply = Supply.get_by_id(g.sess, supply_id)
        supply_note = eval(supply.note)
        if 'delete' in request.values:
            del supply_note['notes'][index]
            supply.note = str(supply_note)
            g.sess.commit()
            return chellow_redirect(
                "/supplies/" + str(supply_id) + '/notes', 303)
        else:
            category = req_str('category')
            is_important = req_bool('is_important')
            body = req_str('body')
            note = supply_note['notes'][index]
            note['category'] = category
            note['is_important'] = is_important
            note['body'] = body
            supply.note = str(supply_note)
            g.sess.commit()
            return chellow_redirect(
                '/supplies/' + str(supply_id) + '/notes', 303)
    except BadRequest as e:
        flash(e.description)
        supply_note = eval(supply.note)
        note = supply_note['notes'][index]
        note['index'] = index
        return render_template(
            'supply_note_edit.html', supply=supply, note=note)


@views.route('/dc_contracts/<int:contract_id>/auto_importer')
def dc_auto_importer_get(contract_id):
    contract = Contract.get_dc_by_id(g.sess, contract_id)
    task = chellow.hh_importer.get_hh_import_task(contract)
    return render_template(
        'dc_auto_importer.html', contract=contract, task=task)


@views.route('/dc_contracts/<int:contract_id>/auto_importer', methods=['POST'])
def dc_auto_importer_post(contract_id):
    try:
        contract = Contract.get_dc_by_id(g.sess, contract_id)
        task = chellow.hh_importer.get_hh_import_task(contract)
        task.go()
        return chellow_redirect(
            f'/dc_contracts/{contract.id}/auto_importer', 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template(
                'dc_auto_importer.html', contract=contract, task=task), 400)


@views.route('/non_core_contracts/<int:contract_id>/auto_importer')
def non_core_auto_importer_get(contract_id):
    contract = Contract.get_non_core_by_id(g.sess, contract_id)
    importer = import_module(f'chellow.{contract.name}').get_importer()
    return render_template(
        'non_core_auto_importer.html', importer=importer, contract=contract)


@views.route(
    '/non_core_contracts/<int:contract_id>/auto_importer', methods=['POST'])
def non_core_auto_importer_post(contract_id):
    try:
        contract = Contract.get_non_core_by_id(g.sess, contract_id)
        importer = import_module(f'chellow.{contract.name}').get_importer()
        importer.go()
        return chellow_redirect(
            f'/non_core_contracts/{contract.id}/auto_importer', 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template(
                'non_core_auto_importer.html', importer=importer,
                contract=contract), 400)


@views.route('/mop_bills/<int:bill_id>')
def mop_bill_get(bill_id):
    bill = Bill.get_by_id(g.sess, bill_id)
    register_reads = g.sess.query(RegisterRead).filter(
        RegisterRead.bill == bill).order_by(RegisterRead.present_date.desc())
    fields = {'bill': bill, 'register_reads': register_reads}
    try:
        breakdown_dict = loads(bill.breakdown)

        raw_lines = []
        for key in ('raw_lines', 'raw-lines'):
            try:
                raw_lines += breakdown_dict[key]
                del breakdown_dict[key]
            except KeyError:
                pass

        rows = set()
        columns = set()
        grid = defaultdict(dict)

        for k, v in tuple(breakdown_dict.items()):
            if k.endswith('-gbp'):
                columns.add('gbp')
                row_name = k[:-4]
                rows.add(row_name)
                grid[row_name]['gbp'] = v
                del breakdown_dict[k]

        for k, v in tuple(breakdown_dict.items()):
            for row_name in sorted(list(rows), key=len, reverse=True):
                if k.startswith(row_name + '-'):
                    col_name = k[len(row_name) + 1:]
                    columns.add(col_name)
                    grid[row_name][col_name] = csv_make_val(v)
                    del breakdown_dict[k]
                    break

        for k, v in breakdown_dict.items():
            pair = k.split('-')
            row_name = '-'.join(pair[:-1])
            column_name = pair[-1]
            rows.add(row_name)
            columns.add(column_name)
            grid[row_name][column_name] = csv_make_val(v)

        column_list = sorted(list(columns))
        for rate_name in [col for col in column_list if col.endswith('rate')]:
            column_list.remove(rate_name)
            column_list.append(rate_name)

        if 'gbp' in column_list:
            column_list.remove('gbp')
            column_list.append('gbp')

        row_list = sorted(list(rows))
        fields.update(
            {
                'raw_lines': raw_lines, 'row_list': row_list,
                'column_list': column_list, 'grid': grid})
    except SyntaxError:
        pass
    return render_template('mop_bill.html', **fields)


@views.route('/mop_bills/<int:bill_id>/edit')
def mop_bill_edit_get(bill_id):
    bill_types = g.sess.query(BillType).order_by(BillType.code).all()
    bill = Bill.get_by_id(g.sess, bill_id)
    return render_template(
        'mop_bill_edit.html', bill=bill, bill_types=bill_types)


@views.route('/mop_bills/<int:bill_id>/edit', methods=["POST"])
def mop_bill_edit_post(bill_id):
    try:
        bill = Bill.get_by_id(g.sess, bill_id)
        if 'delete' in request.values:
            bill.delete(g.sess)
            g.sess.commit()
            return chellow_redirect("/mop_batches/" + str(bill.batch.id), 303)
        else:
            account = req_str('account')
            reference = req_str('reference')
            issue_date = req_date('issue')
            start_date = req_date('start')
            finish_date = req_date('finish')
            kwh = req_decimal('kwh')
            net = req_decimal('net')
            vat = req_decimal('vat')
            gross = req_decimal('gross')
            type_id = req_int('bill_type_id')
            breakdown = req_zish('breakdown')
            bill_type = BillType.get_by_id(g.sess, type_id)

            bill.update(
                account, reference, issue_date, start_date, finish_date, kwh,
                net, vat, gross, bill_type, breakdown)
            g.sess.commit()
            return chellow_redirect("/mop_bills/" + str(bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        bill_types = g.sess.query(BillType).order_by(BillType.code).all()
        return render_template(
            'mop_bill_edit.html', bill=bill, bill_types=bill_types)


@views.route('/csv_sites_triad')
def csv_sites_triad_get():
    now = Datetime.utcnow()
    if now.month < 3:
        now -= relativedelta(years=1)
    return render_template('csv_sites_triad.html', year=now.year)


@views.route('/csv_sites_hh_data')
def csv_sites_hh_data_get():
    now = Datetime.utcnow()
    start_date = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    finish_date = Datetime(now.year, now.month, 1) - HH
    return render_template(
        'csv_sites_hh_data.html', start_date=start_date,
        finish_date=finish_date)


@views.route('/csv_sites_duration')
def csv_sites_duration_get():
    now = utc_datetime_now()
    month_start = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = month_start + relativedelta(months=1) - HH
    return render_template(
        'csv_sites_duration.html', month_start=month_start,
        month_finish=month_finish)


@views.route('/csv_register_reads')
def csv_register_reads_get():
    init = Datetime.utcnow()
    init = Datetime(init.year, init.month, 1) - relativedelta(months=1)
    return render_template('csv_register_reads.html', init=init)


@views.route('/csv_supplies_hh_data')
def csv_supplies_hh_data_get():
    now = Datetime.utcnow()
    start_date = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    finish_date = Datetime(now.year, now.month, 1) - HH
    return render_template(
        'csv_supplies_hh_data.html', start_date=start_date,
        finish_date=finish_date)


@views.route('/csv_supplies_snapshot')
def csv_supplies_snapshot_get():
    now = utc_datetime_now()
    return render_template(
        'csv_supplies_snapshot.html', default_timestamp=utc_datetime(
            now.year, now.month, now.day))


@views.route('/csv_supplies_duration')
def csv_supplies_duration_get():
    last_month = utc_datetime_now() - relativedelta(months=1)
    last_month_start = utc_datetime(last_month.year, last_month.month)
    last_month_finish = last_month_start + relativedelta(months=1) - HH
    return render_template(
        'csv_supplies_duration.html', last_month_start=last_month_start,
        last_month_finish=last_month_finish)


@views.route('/csv_supplies_monthly_duration')
def csv_supplies_monthly_duration_get():
    init = Datetime.utcnow()
    init = Datetime(init.year, init.month, 1) - relativedelta(months=1)
    return render_template('csv_supplies_monthly_duration.html', init=init)


@views.route('/csv_bills')
def csv_bills_get():
    init = Datetime.utcnow()
    init = Datetime(init.year, init.month, 1) - relativedelta(months=1)
    return render_template('csv_bills.html', init=init)


@views.route('/tprs')
def tprs_get():
    tprs = g.sess.query(Tpr).order_by(Tpr.code).all()
    return render_template('tprs.html', tprs=tprs)


@views.route('/tprs/<int:tpr_id>')
def tpr_get(tpr_id):
    tpr = Tpr.get_by_id(g.sess, tpr_id)
    clock_intervals = g.sess.query(ClockInterval).filter(
        ClockInterval.tpr == tpr).order_by(ClockInterval.id)
    return render_template(
        'tpr.html', tpr=tpr, clock_intervals=clock_intervals)


@views.route('/user_roles')
def user_roles_get():
    user_roles = g.sess.query(UserRole).order_by(UserRole.code)
    return render_template('user_roles.html', user_roles=user_roles)


@views.route('/bill_types/<int:type_id>')
def bill_type_get(type_id):
    bill_type = BillType.get_by_id(g.sess, type_id)
    return render_template('bill_type.html', bill_type=bill_type)


@views.route('/ods_monthly_duration')
def ods_monthly_duration_get():
    now = Datetime.utcnow()
    month_start = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = Datetime(now.year, now.month, 1) - HH
    return render_template(
        'ods_monthly_duration.html', month_start=month_start,
        month_finish=month_finish)


@views.route('/scenarios')
def scenarios_get():
    scenarios = g.sess.query(Scenario).order_by(Scenario.name).all()
    return render_template('scenarios.html', scenarios=scenarios)


@views.route('/scenarios/add', methods=['POST'])
def scenario_add_post():
    try:
        name = req_str("name")
        properties = req_zish("properties")
        scenario = Scenario.insert(g.sess, name, properties)
        g.sess.commit()
        return chellow_redirect("/scenarios/" + str(scenario.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        scenarios = g.sess.query(Scenario).order_by(Scenario.name)
        return make_response(
            render_template('scenario_add.html', scenarios=scenarios), 400)


@views.route('/scenarios/add')
def scenario_add_get():
    now = utc_datetime_now()
    props = {
        'scenario_start_month': now.month,
        'scenario_start_year': now.year,
        'scenario_duration': 1
    }
    return render_template('scenario_add.html', initial_props=dumps(props))


@views.route('/scenarios/<int:scenario_id>')
def scenario_get(scenario_id):
    scenario = Scenario.get_by_id(g.sess, scenario_id)
    return render_template('scenario.html', scenario=scenario)


@views.route('/scenarios/<int:scenario_id>/edit')
def scenario_edit_get(scenario_id):
    scenario = Scenario.get_by_id(g.sess, scenario_id)
    return render_template('scenario_edit.html', scenario=scenario)


@views.route('/scenarios/<int:scenario_id>/edit', methods=['POST'])
def scenario_edit_post(scenario_id):
    try:
        scenario = Scenario.get_by_id(g.sess, scenario_id)
        if 'delete' in request.form:
            scenario.delete(g.sess)
            g.sess.commit()
            return chellow_redirect('/scenarios', 303)
        else:
            name = req_str('name')
            properties = req_zish('properties')
            scenario.update(name, properties)
            g.sess.commit()
            return chellow_redirect('/scenarios/' + str(scenario.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        description = e.description
        flash(description)
        return make_response(
            render_template('scenario_edit.html', scenario=scenario, ), 400)


@views.route('/site_snags/<int:snag_id>/edit')
def site_snag_edit_get(snag_id):
    snag = Snag.get_by_id(g.sess, snag_id)
    return render_template('site_snag_edit.html', snag=snag)


@views.route('/site_snags/<int:snag_id>/edit', methods=['POST'])
def site_snag_edit_post(snag_id):
    try:
        ignore = req_bool('ignore')
        snag = Snag.get_by_id(g.sess, snag_id)
        snag.set_is_ignored(ignore)
        g.sess.commit()
        return chellow_redirect("/site_snags/" + str(snag.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(
            render_template('site_snag_edit.html', snag=snag), 400)


@views.route('/supplies/<int:supply_id>/virtual_bill')
def supply_virtual_bill_get(supply_id):
    supply = Supply.get_by_id(g.sess, supply_id)
    start_date = req_date('start')
    finish_date = req_date('finish')
    forecast_date = chellow.computer.forecast_date()

    net_gbp = 0
    caches = {}
    meras = []
    debug = ''

    month_start = utc_datetime(start_date.year, start_date.month)

    while not month_start > finish_date:
        month_finish = month_start + relativedelta(months=1) - HH

        chunk_start = hh_max(start_date, month_start)
        chunk_finish = hh_min(finish_date, month_finish)

        for era in g.sess.query(Era).filter(
                Era.supply == supply, Era.imp_mpan_core != null(),
                Era.start_date <= chunk_finish, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= chunk_start)):
            block_start = hh_max(era.start_date, chunk_start)
            block_finish = hh_min(era.finish_date, chunk_finish)

            debug += 'found an era'

            contract = era.imp_supplier_contract
            data_source = chellow.computer.SupplySource(
                g.sess, block_start, block_finish, forecast_date, era, True,
                caches)
            headings = [
                'id', 'supplier_contract', 'account', 'start date',
                'finish date']
            data = [
                data_source.id, contract.name, data_source.supplier_account,
                data_source.start_date, data_source.finish_date]
            mera = {'headings': headings, 'data': data, 'skip': False}

            meras.append(mera)
            chellow.computer.contract_func(
                caches, contract, 'virtual_bill')(data_source)
            bill = data_source.supplier_bill
            net_gbp += bill['net-gbp']

            for title in chellow.computer.contract_func(
                    caches, contract, 'virtual_bill_titles')():
                if title == 'consumption-info':
                    del bill[title]
                    continue
                headings.append(title)
                if title in bill:
                    data.append(bill[title])
                    del bill[title]
                else:
                    data.append('')

            for k in sorted(bill.keys()):
                headings.append(k)
                data.append(bill[k])

            if len(meras) > 1 and meras[-2]['headings'] == mera['headings']:
                mera['skip'] = True

        month_start += relativedelta(months=1)

    return render_template(
        'supply_virtual_bill.html', supply=supply, start_date=start_date,
        finish_date=finish_date, meras=meras, net_gbp=net_gbp)


@views.route('/mtcs')
def mtcs_get():
    mtcs = g.sess.query(Mtc).outerjoin(Mtc.dno).order_by(
        Mtc.code, Party.dno_code).options(joinedload(Mtc.dno)).all()
    return render_template('mtcs.html', mtcs=mtcs)


@views.route('/mtcs/<int:mtc_id>')
def mtc_get(mtc_id):
    mtc = g.sess.query(Mtc).outerjoin(Mtc.dno).filter(
        Mtc.id == mtc_id).options(joinedload(Mtc.dno)).one()
    return render_template('mtc.html', mtc=mtc)


@views.route('/mtcs/<int:mtc_id>/edit')
def mtc_edit_get(mtc_id):
    mtc = Mtc.get_by_id(g.sess, mtc_id)
    meter_types = g.sess.query(MeterType).order_by(MeterType.code).all()
    meter_payment_types = g.sess.query(MeterPaymentType).order_by(
        MeterPaymentType.code).all()
    return render_template(
        'mtc_edit.html', mtc=mtc, meter_types=meter_types,
        meter_payment_types=meter_payment_types)


@views.route('/mtcs/<int:mtc_id>/edit', methods=['POST'])
def mtc_edit_post(mtc_id):
    try:
        mtc = Mtc.get_by_id(g.sess, mtc_id)
        if 'delete' in request.values:
            mtc.delete(g.sess)
            g.sess.commit()
            return chellow_redirect('/mtcs/', 303)
        else:
            description = req_str('description')
            has_related_metering = req_bool('has_related_metering')
            has_comms = req_bool('has_comms')
            is_hh = req_bool('is_hh')
            meter_type_id = req_int('meter_type_id')
            meter_payment_type_id = req_int('meter_payment_type_id')
            tpr_count = req_int('tpr_count')
            valid_from = req_date('valid_from')
            has_finished = req_bool('has_finished')
            valid_to = req_date('valid_to') if has_finished else None
            mtc.update(
                g.sess, description, has_related_metering, has_comms, is_hh,
                meter_type_id, meter_payment_type_id, tpr_count, valid_from,
                valid_to)
            g.sess.commit()
            return chellow_redirect('/mtcs/' + str(mtc.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        meter_types = g.sess.query(MeterType).order_by(MeterType.code).all()
        meter_payment_types = g.sess.query(MeterPaymentType).order_by(
            MeterPaymentType.code).all()
        return make_response(
            render_template(
                'mtc_edit.html', mtc=mtc, meter_types=meter_types,
                meter_payment_types=meter_payment_types), 400)


@views.route('/csv_crc')
def csv_crc_get():
    start_date = utc_datetime_now()
    if start_date.month < 3:
        start_date = start_date - relativedelta(years=1)
    return render_template('csv_crc.html', start_date=start_date)


@views.route('/dnos')
def dnos_get():
    dnos = []
    for dno in g.sess.query(Party).join(MarketRole).filter(
            MarketRole.code == 'R').order_by(Party.dno_code):
        scripts = get_file_scripts(dno.dno_code)
        try:
            dno_dict = {
                'dno': dno,
                'start_date': scripts[0][0],
                'finish_date': scripts[-1][1]}
            dnos.append(dno_dict)
        except IndexError:
            raise BadRequest(
                "Can't find any rate scripts for the DNO '" + dno.dno_code +
                "'.")
    gsp_groups = g.sess.query(GspGroup).order_by(GspGroup.code)
    return render_template('dnos.html', dnos=dnos, gsp_groups=gsp_groups)


@views.route('/dnos/<int:dno_id>')
def dno_get(dno_id):
    dno = Party.get_dno_by_id(g.sess, dno_id)
    rate_scripts = get_file_scripts(dno.dno_code)[::-1]
    return render_template(
        'dno.html', dno=dno, rate_scripts=rate_scripts, reports=[])


@views.route('/industry_contracts')
def industry_contracts_get():
    contracts = []
    contracts_path = os.path.join(current_app.root_path, 'rate_scripts')

    for contract_code in sorted(os.listdir(contracts_path)):
        try:
            int(contract_code)
            continue
        except ValueError:
            scripts = get_file_scripts(contract_code)
            contracts.append(
                {
                    'code': contract_code,
                    'start_date': scripts[0][0],
                    'finish_date': scripts[-1][1]})

    return render_template('industry_contracts.html', contracts=contracts)


@views.route('/industry_contracts/<contract_code>')
def industry_contract_get(contract_code):
    rate_scripts = get_file_scripts(contract_code)[::-1]
    return render_template(
        'industry_contract.html', rate_scripts=rate_scripts,
        contract_code=contract_code)


@views.route(
    '/industry_contracts/<contract_code>/rate_scripts/<start_date_str>')
def industry_rate_script_get(contract_code, start_date_str):
    rate_script = None
    start_date = to_utc(Datetime.strptime(start_date_str, '%Y%m%d%H%M'))
    for rscript in get_file_scripts(contract_code):
        if rscript[0] == start_date:
            rate_script = rscript
            break
    if rate_script is None:
        raise NotFound()
    return render_template(
        'industry_rate_script.html', contract_code=contract_code,
        rate_script=rate_script)


@views.route('/llfcs')
def llfcs_get():
    dno_id = req_int('dno_id')
    dno = Party.get_dno_by_id(g.sess, dno_id)
    llfcs = g.sess.query(Llfc).filter(Llfc.dno == dno).order_by(Llfc.code)
    return render_template('llfcs.html', llfcs=llfcs, dno=dno)


@views.route('/llfcs/<int:llfc_id>')
def llfc_get(llfc_id):
    llfc = Llfc.get_by_id(g.sess, llfc_id)
    return render_template('llfc.html', llfc=llfc)


@views.route('/llfcs/<int:llfc_id>/edit')
def llfc_edit_get(llfc_id):
    llfc = Llfc.get_by_id(g.sess, llfc_id)
    voltage_levels = g.sess.query(VoltageLevel).order_by(
        VoltageLevel.code).all()
    return render_template(
        'llfc_edit.html', llfc=llfc, voltage_levels=voltage_levels)


@views.route('/llfcs/<int:llfc_id>/edit', methods=['POST'])
def llfc_edit_post(llfc_id):
    try:
        llfc = Llfc.get_by_id(g.sess, llfc_id)
        if 'delete' in request.values:
            dno = llfc.dno
            llfc.delete(g.sess)
            g.sess.commit()
            return chellow_redirect(
                '/dnos/' + str(dno.dno_code) + '/llfcs', 303)
        else:
            description = req_str('description')
            voltage_level_id = req_int('voltage_level_id')
            voltage_level = VoltageLevel.get_by_id(g.sess, voltage_level_id)
            is_substation = req_bool('is_substation')
            is_import = req_bool('is_import')
            valid_from = req_date('valid_from')
            has_finished = req_bool('has_finished')
            valid_to = req_date('valid_to') if has_finished else None
            llfc.update(
                g.sess, description, voltage_level, is_substation, is_import,
                valid_from, valid_to)
            g.sess.commit()
            return chellow_redirect('/llfcs/' + str(llfc.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        return make_response(render_template('llfc_edit.html', llfc=llfc), 400)


@views.route('/sscs')
def sscs_get():
    sscs = g.sess.query(Ssc).options(
        joinedload(Ssc.measurement_requirements).
        joinedload(MeasurementRequirement.tpr)).order_by(Ssc.code)
    return render_template('sscs.html', sscs=sscs)


@views.route('/sscs/<int:ssc_id>')
def ssc_get(ssc_id):
    ssc = Ssc.get_by_id(g.sess, ssc_id)
    return render_template('ssc.html', ssc=ssc)


@views.route('/csv_supplies_triad')
def csv_supplies_triad_get():
    now = Datetime.utcnow()
    return render_template('csv_supplies_triad.html', year=now.year - 1)


@views.route('/supplier_bills/<int:bill_id>/add_read')
def read_add_get(bill_id):
    read_types = g.sess.query(ReadType).order_by(ReadType.code)
    estimated_read_type_id = g.sess.query(ReadType.id).filter(
        ReadType.code == 'E').scalar()
    tprs = g.sess.query(Tpr).order_by(Tpr.code)
    bill = Bill.get_by_id(g.sess, bill_id)
    coefficient = 1
    mpan_str = msn = previous_date = previous_value = previous_type_id = None

    era = bill.supply.find_era_at(g.sess, bill.start_date)
    if era is not None:
        era_properties = PropDict(
            chellow.utils.url_root + 'eras/' + str(era.id),
            loads(era.properties))
        try:
            coefficient = float(era_properties['coefficient'])
        except KeyError:
            pass
        mpan_str = era.imp_mpan_core
        msn = era.msn

    prev_read = g.sess.query(RegisterRead).join(Bill).filter(
        Bill.supply == bill.supply,
        RegisterRead.present_date <= bill.finish_date).order_by(
        RegisterRead.present_date.desc()).first()
    if prev_read is not None:
        previous_date = prev_read.present_date
        previous_value = prev_read.present_value
        previous_type_id = prev_read.present_type.id

    return render_template(
        'read_add.html', bill=bill, read_types=read_types, tprs=tprs,
        coefficient=coefficient, mpan_str=mpan_str, msn=msn,
        previous_date=previous_date, previous_value=previous_value,
        previous_type_id=previous_type_id,
        estimated_read_type_id=estimated_read_type_id)


@views.route('/supplier_bills/<int:bill_id>/add_read', methods=["POST"])
def read_add_post(bill_id):
    try:
        bill = Bill.get_by_id(g.sess, bill_id)
        tpr_id = req_int("tpr_id")
        tpr = Tpr.get_by_id(g.sess, tpr_id)
        coefficient = req_decimal("coefficient")
        units_str = req_str("units")
        msn = req_str("msn")
        mpan_str = req_str("mpan")
        previous_date = req_date("previous")
        previous_value = req_decimal("previous_value")
        previous_type_id = req_int("previous_type_id")
        previous_type = ReadType.get_by_id(g.sess, previous_type_id)
        present_date = req_date("present")
        present_value = req_decimal("present_value")
        present_type_id = req_int("present_type_id")
        present_type = ReadType.get_by_id(g.sess, present_type_id)

        bill.insert_read(
            g.sess, tpr, coefficient, units_str, msn, mpan_str, previous_date,
            previous_value, previous_type, present_date, present_value,
            present_type)
        g.sess.commit()
        return chellow_redirect("/supplier_bills/" + str(bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        read_types = g.sess.query(ReadType).order_by(ReadType.code)
        tprs = g.sess.query(Tpr).order_by(Tpr.code)
        return make_response(
            render_template(
                'read_add.html', bill=bill, read_types=read_types, tprs=tprs),
            400)


@views.route('/dc_batches/<int:batch_id>/add_bill')
def dc_bill_add_get(batch_id):
    batch = Batch.get_by_id(g.sess, batch_id)
    bill_types = g.sess.query(BillType).order_by(BillType.code)
    bills = g.sess.query(Bill).filter(Bill.batch == batch).order_by(
        Bill.start_date)
    return render_template(
        'dc_bill_add.html', batch=batch, bill_types=bill_types, bills=bills)


@views.route('/dc_batches/<int:batch_id>/add_bill', methods=['POST'])
def dc_bill_add_post(batch_id):
    try:
        batch = Batch.get_by_id(g.sess, batch_id)
        mpan_core = req_str("mpan_core")
        mpan_core = parse_mpan_core(mpan_core)
        account = req_str("account")
        reference = req_str("reference")
        issue_date = req_date("issue")
        start_date = req_hh_date("start")
        finish_date = req_hh_date("finish")
        kwh = req_decimal("kwh")
        net = req_decimal("net")
        vat = req_decimal("vat")
        gross = req_decimal("gross")
        bill_type_id = req_int("bill_type_id")
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        breakdown_str = req_str("breakdown")

        breakdown = loads(breakdown_str)
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        bill = batch.insert_bill(
            g.sess, account, reference, issue_date, start_date, finish_date,
            kwh, net, vat, gross, bill_type, breakdown,
            Supply.get_by_mpan_core(g.sess, mpan_core))
        g.sess.commit()
        return chellow_redirect("/dc_bills/" + str(bill.id), 303)
    except BadRequest as e:
        g.sess.rollback()
        flash(e.description)
        bill_types = g.sess.query(BillType).order_by(BillType.code)
        bills = g.sess.query(Bill).filter(Bill.batch == batch).order_by(
            Bill.start_date)
        return make_response(
            render_template(
                'dc_bill_add.html', batch=batch, bill_types=bill_types,
                bills=bills), 400)


@views.route('/pcs')
def pcs_get():
    return render_template('pcs.html', pcs=g.sess.query(Pc).order_by(Pc.code))


@views.route('/pcs/<int:pc_id>')
def pc_get(pc_id):
    pc = Pc.get_by_id(g.sess, pc_id)
    return render_template('pc.html', pc=pc)


@views.route('/gsp_groups')
def gsp_groups_get():
    return render_template(
        'gsp_groups.html',
        groups=g.sess.query(GspGroup).order_by(GspGroup.code).all())


@views.route('/gsp_groups/<int:group_id>')
def gsp_group_get(group_id):
    group = GspGroup.get_by_id(g.sess, group_id)
    return render_template('gsp_group.html', gsp_group=group)


@views.route('/dtc_meter_types')
def dtc_meter_types_get():
    return render_template('dtc_meter_types.html', dtc_meter_types=METER_TYPES)


@views.route('/dtc_meter_types/<code>')
def dtc_meter_type_get(code):
    desc = METER_TYPES[code]
    return render_template(
        'dtc_meter_type.html',
        dtc_meter_type_code=code, dtc_meter_type_description=desc)


@views.route('/sites/<int:site_id>/gen_graph')
def site_gen_graph_get(site_id):
    cache = {}
    if 'finish_year' in request.args:
        finish_year = req_int("finish_year")
        finish_month = req_int("finish_month")
        months = req_int("months")
    else:
        now = ct_datetime_now()
        finish_year = now.year
        finish_month = now.month
        months = 1

    month_list = list(
        c_months_u(
            finish_year=finish_year, finish_month=finish_month, months=months))
    start_date, finish_date = month_list[0][0], month_list[-1][-1]

    site = Site.get_by_id(g.sess, site_id)

    colour_list = (
        'blue', 'green', 'red', 'yellow', 'maroon', 'aqua', 'fuchsia', 'olive')

    graph_names = ('used', 'disp', 'gen', 'imp', 'exp', 'third')
    graphs = dict(
        (
            n, {
                'supplies': OrderedDict(), 'ticks': [], 'pos_hhs': [],
                'neg_hhs': [], 'scale_lines': [], 'scale_values': [],
                'monthly_scale_values': []}) for n in graph_names)

    days = []
    month_points = []
    max_scls = {'pos': 10, 'neg': 1}
    supply_ids = list(
        s.id for s in g.sess.query(Supply).join(Era).join(SiteEra).
        join(Source).filter(
            SiteEra.site == site, Source.code != 'sub',
            SiteEra.is_physical == true(), Era.start_date <= finish_date,
            or_(Era.finish_date == null(), Era.finish_date >= start_date))
        .distinct())

    rs = iter(
        g.sess.query(
            cast(HhDatum.value * 2, Float), HhDatum.start_date, HhDatum.status,
            Channel.imp_related, Supply.name, Source.code, Supply.id).
        join(Channel).join(Era).join(Supply).join(Source).filter(
            Channel.channel_type == 'ACTIVE', HhDatum.start_date >= start_date,
            HhDatum.start_date <= finish_date, Supply.id.in_(supply_ids)).
        order_by(HhDatum.start_date, Supply.id))
    (
        hhd_value, hhd_start_date, status, imp_related, supply_name,
        source_code, sup_id) = next(
            rs, (None, None, None, None, None, None, None))

    for x, hh_date in enumerate(hh_range(cache, start_date, finish_date)):
        hh_date_ct = to_ct(hh_date)
        rvals = dict((n, {'pos': 0, 'neg': 0}) for n in graph_names)

        if hh_date_ct.hour == 0 and hh_date_ct.minute == 0:
            day = hh_date_ct.day
            days.append(
                {
                    'text': str(day), 'x': x + 20,
                    'colour': 'red' if hh_date_ct.weekday() > 4 else 'black'})

            for g_name, graph in graphs.items():
                graph['ticks'].append({'x': x})

            if day == 15:
                month_points.append(
                    {'x': x, 'text': hh_date_ct.strftime("%B")})

        is_complete = None

        while hhd_start_date == hh_date:
            if is_complete is None:
                is_complete = True

            if status != 'A':
                is_complete = False

            to_adds = []
            if imp_related and source_code in ('net', 'gen-net'):
                to_adds.append(('imp', 'pos'))
            if not imp_related and source_code in ('net', 'gen-net'):
                to_adds.append(('exp', 'pos'))
            if (imp_related and source_code == 'gen') or \
                    (not imp_related and source_code == 'gen-net'):
                to_adds.append(('gen', 'pos'))
            if (not imp_related and source_code == 'gen') or \
                    (imp_related and source_code == 'gen-net'):
                to_adds.append(('gen', 'neg'))
            if (imp_related and source_code == '3rd-party') or (
                    not imp_related and source_code ==
                    '3rd-party-reverse'):
                to_adds.append(('third', 'pos'))
            if (not imp_related and source_code == '3rd-party') or (
                    imp_related and source_code == '3rd-party-reverse'):
                to_adds.append(('third', 'neg'))

            for gname, polarity in to_adds:
                graph = graphs[gname]
                supplies = graph['supplies']
                if sup_id not in supplies:
                    supplies[sup_id] = {
                        'colour': colour_list[len(supplies)],
                        'text': source_code + ' ' + supply_name,
                        'source_code': source_code}

                grvals = rvals[gname]
                graph[polarity + '_hhs'].append(
                    {
                        'colour': graph['supplies'][sup_id]['colour'],
                        'running_total': grvals[polarity],
                        'value': hhd_value, 'x': x, 'start_date': hh_date,
                        'background_colour': 'white'
                    }
                )
                grvals[polarity] += hhd_value
                max_scls[polarity] = max(
                    max_scls[polarity], int(grvals[polarity]))

            (
                hhd_value, hhd_start_date, status, imp_related,
                supply_name, source_code, sup_id) = next(
                    rs, (None, None, None, None, None, None, None))

        disp_val = rvals['gen']['pos'] - rvals['gen']['neg'] - \
            rvals['exp']['pos']
        used_val = rvals['imp']['pos'] + disp_val + rvals['third']['pos'] - \
            rvals['third']['neg']
        for val, graph_name in ((used_val, 'used'), (disp_val, 'disp')):
            graph = graphs[graph_name]
            pos_val = max(val, 0)
            neg_val = abs(min(val, 0))
            for gval, prefix in ((pos_val, 'pos'), (neg_val, 'neg')):
                hh_dict = {
                    'x': x, 'start_date': hh_date, 'value': gval,
                    'running_total': 0
                }
                if is_complete is True:
                    hh_dict['colour'] = 'blue'
                    hh_dict['background_colour'] = 'white'
                else:
                    hh_dict['colour'] = 'black'
                    hh_dict['background_colour'] = 'grey'

                graph[prefix + '_hhs'].append(hh_dict)
                max_scls[prefix] = max(max_scls[prefix], int(gval))

    max_height = 80
    scl_factor = max_height / max_scls['pos']

    raw_step_overall = max_scls['pos'] / (max_height / 20)
    factor_overall = 10**int(math.floor(math.log10(raw_step_overall)))
    end_overall = raw_step_overall / factor_overall
    new_end_overall = 1
    if end_overall >= 2:
        new_end_overall = 2
    if end_overall >= 5:
        new_end_overall = 5
    step_overall = max(int(new_end_overall * factor_overall), 1)

    graph_titles = {
        'exp': "Exported", 'gen': "Generated", 'imp': "Imported",
        'used': "Used", 'disp': "Displaced", 'third': "Third Party"}

    y = 50
    for graph_name in graph_names:
        graph = graphs[graph_name]
        graph['y'] = y
        graph['height_pos'] = max_scls['pos'] * scl_factor
        graph['height_neg'] = max_scls['neg'] * scl_factor
        graph['height'] = graph['height_pos'] + graph['height_neg'] + 100
        y += graph['height']

        x_axis_px = max_scls['pos'] * scl_factor
        graph['title'] = graph_titles[graph_name]
        for tick in graph['ticks']:
            tick['y'] = x_axis_px

        graph['scale_lines'] = []
        for pref in ('pos', 'neg'):
            for i in range(0, max_scls[pref], step_overall):
                if pref == 'pos':
                    y_scale = (-1 * i + max_scls[pref]) * scl_factor
                    fac = 1
                else:
                    fac = -1
                    y_scale = (i + max_scls['pos']) * scl_factor
                graph['scale_lines'].append(
                    {
                        'y': y_scale,
                        'y_val': y_scale + 3,
                        'width': len(graphs['used']['pos_hhs']),
                        'text': str(fac * i)})

                for month_point in month_points:
                    graph['monthly_scale_values'].append(
                        {
                            'text': str(fac * i),
                            'x': month_point['x'] + 16,
                            'y': y_scale + 5})

        for ghh in graph['pos_hhs']:
            height_px = ghh['value'] * scl_factor
            running_total_px = ghh['running_total'] * scl_factor
            ghh['height'] = height_px
            ghh['y'] = x_axis_px - height_px - running_total_px

        for ghh in graph['neg_hhs']:
            ghh['height'] = ghh['value'] * scl_factor
            ghh['y'] = x_axis_px

    y += 30
    for day_dict in days:
        day_dict['y'] = graphs['third']['height'] - 70

    height = y + 30

    for month_dict in month_points:
        month_dict['y'] = graphs['third']['height'] - 40

    title = {
        'text': "Electricity at site " + site.code + " " + site.name +
        " for " + str(months) + " month" + ('s' if months > 1 else '') +
        " up to and including " + (to_ct(finish_date) - HH).strftime("%B %Y"),
        'x': 30, 'y': 20}

    return render_template(
        'site_gen_graph.html', finish_year=finish_year,
        finish_month=finish_month, months=months, site=site,
        finish_date=finish_date, graphs=graphs, month_points=month_points,
        graph_names=graph_names, title=title, height=height, days=days)


@views.route('/g_supplies')
def g_supplies_get():
    if 'search_pattern' in request.values:
        pattern = req_str('search_pattern')
        pattern = pattern.strip()
        reduced_pattern = pattern.replace(" ", "")
        if 'max_results' in request.values:
            max_results = req_int('max_results')
        else:
            max_results = 50

        g_eras = g.sess.query(GEra).from_statement(
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
                "and e1.start_date = sq.max_start_date limit :max_results")
            ).params(
            pattern="%" + pattern + "%",
            reducedPattern="%" + reduced_pattern + "%",
            max_results=max_results).all()
        if len(g_eras) == 1:
            return chellow_redirect(
                "/g_supplies/" + str(g_eras[0].g_supply.id))
        else:
            return render_template(
                'g_supplies.html', g_eras=g_eras, max_results=max_results)
    else:
        return render_template('g_supplies.html')


@views.route('/g_supplies/<int:g_supply_id>')
def g_supply_get(g_supply_id):
    debug = ''
    try:
        g_era_bundles = []
        g_supply = GSupply.get_by_id(g.sess, g_supply_id)
        g_eras = g.sess.query(GEra).filter(GEra.g_supply == g_supply).order_by(
            GEra.start_date.desc()).all()
        for g_era in g_eras:
            physical_site = g.sess.query(Site).join(SiteGEra).filter(
                SiteGEra.is_physical == true(), SiteGEra.g_era == g_era).one()
            other_sites = g.sess.query(Site).join(SiteGEra).filter(
                SiteGEra.is_physical != true(), SiteGEra.g_era == g_era).all()
            g_bill_dicts = []
            g_era_bundle = {
                'g_era': g_era, 'physical_site': physical_site,
                'other_sites': other_sites, 'g_bill_dicts': g_bill_dicts}
            g_era_bundles.append(g_era_bundle)

            g_era_bundle['shared_accounts'] = \
                g.sess.query(GSupply).distinct().join(GEra).filter(
                    GSupply.id != g_supply.id, GEra.account == g_era.account,
                    GEra.g_contract == g_era.g_contract).all()

            g_bills = g.sess.query(GBill).filter(
                GBill.g_supply == g_supply).order_by(
                    GBill.start_date.desc(), GBill.issue_date.desc(),
                    GBill.reference.desc())
            if g_era.finish_date is not None:
                g_bills = g_bills.filter(GBill.start_date <= g_era.finish_date)
            if g_era != g_eras[-1]:
                g_bills = g_bills.filter(GBill.start_date >= g_era.start_date)

            for g_bill in g_bills:
                g_reads = g.sess.query(GRegisterRead).filter(
                    GRegisterRead.g_bill == g_bill).order_by(
                    GRegisterRead.pres_date.desc()).options(
                    joinedload(GRegisterRead.prev_type),
                    joinedload(GRegisterRead.pres_type)).all()
                g_bill_dicts.append(
                    {
                        'g_bill': g_bill,
                        'g_reads': g_reads
                    }
                )

            b_dicts = list(reversed(g_bill_dicts))
            for i, b_dict in enumerate(b_dicts):
                if i < (len(b_dicts) - 1):
                    g_bill = b_dict['g_bill']
                    next_b_dict = b_dicts[i+1]
                    next_g_bill = next_b_dict['g_bill']
                    if (
                            g_bill.start_date, g_bill.finish_date, g_bill.kwh,
                            g_bill.net) == (
                            next_g_bill.start_date, next_g_bill.finish_date,
                            -1 * next_g_bill.kwh, -1 * next_g_bill.net) and \
                            'collapsible' not in b_dict:
                        b_dict['collapsible'] = True
                        next_b_dict['first_collapsible'] = True
                        next_b_dict['collapsible'] = True
                        b_dict['collapse_id'] = next_b_dict['collapse_id'] = \
                            g_bill.id

        RELATIVE_YEAR = relativedelta(years=1)

        now = Datetime.utcnow()
        triad_year = (now - RELATIVE_YEAR).year if now.month < 3 else now.year
        this_month_start = Datetime(now.year, now.month, 1)
        last_month_start = this_month_start - relativedelta(months=1)
        last_month_finish = this_month_start - relativedelta(minutes=30)

        batch_reports = []
        config_contract = Contract.get_non_core_by_name(
            g.sess, 'configuration')
        properties = config_contract.make_properties()
        if 'g_supply_reports' in properties:
            for report_id in properties['g_supply_reports']:
                batch_reports.append(Report.get_by_id(g.sess, report_id))

        truncated_note = None
        is_truncated = False
        note = None
        if len(g_supply.note.strip()) == 0:
            note_str = "{'notes': []}"
        else:
            note_str = g_supply.note

        supply_note = eval(note_str)
        notes = supply_note['notes']
        if len(notes) > 0:
            note = notes[0]
            lines = note['body'].splitlines()
            if len(lines) > 0:
                trunc_line = lines[0][:50]
                if len(lines) > 1 or len(lines[0]) > len(trunc_line):
                    is_truncated = True
                    truncated_note = trunc_line
        return render_template(
            'g_supply.html', triad_year=triad_year, now=now,
            last_month_start=last_month_start,
            last_month_finish=last_month_finish,
            g_era_bundles=g_era_bundles, g_supply=g_supply,
            system_properties=properties, is_truncated=is_truncated,
            truncated_note=truncated_note, note=note,
            this_month_start=this_month_start, batch_reports=batch_reports,
            debug=debug)

    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return render_template('g_supply.html')


@views.route('/g_supplies/<int:g_supply_id>/edit')
def g_supply_edit_get(g_supply_id):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)
    g_eras = g.sess.query(GEra).filter(
        GEra.g_supply == g_supply).order_by(GEra.start_date.desc())
    g_exit_zones = g.sess.query(GExitZone).order_by(GExitZone.code).all()
    return render_template(
        'g_supply_edit.html', g_supply=g_supply, g_eras=g_eras,
        g_exit_zones=g_exit_zones)


@views.route('/g_supplies/<int:g_supply_id>/edit', methods=["POST"])
def g_supply_edit_post(g_supply_id):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)
    try:
        if 'delete' in request.values:
            g_supply.delete(g.sess)
            g.sess.commit()
            return chellow_redirect("/g_supplies", 303)
        elif 'insert_g_era' in request.values:
            start_date = req_date('start')
            g_supply.insert_g_era_at(g.sess, start_date)
            g.sess.commit()
            return chellow_redirect("/g_supplies/" + str(g_supply.id), 303)
        else:
            mprn = req_str("mprn")
            name = req_str("name")
            g_exit_zone_id = req_int("g_exit_zone_id")
            g_exit_zone = GExitZone.get_by_id(g.sess, g_exit_zone_id)
            g_supply.update(mprn, name, g_exit_zone)
            g.sess.commit()
            return chellow_redirect("/g_supplies/" + str(g_supply.id), 303)
    except BadRequest as e:
        flash(e.description)
        g_eras = g.sess.query(GEra).filter(
            GEra.g_supply == g_supply).order_by(GEra.start_date.desc())
        g_exit_zones = g.sess.query(GExitZone).order_by(GExitZone.code).all()
        return make_response(
            render_template(
                'g_supply_edit.html', g_supply=g_supply, g_eras=g_eras,
                g_exit_zones=g_exit_zones), 400)


@views.route('/g_contracts')
def g_contracts_get():
    contracts = g.sess.query(GContract).order_by(GContract.name)
    return render_template('g_contracts.html', contracts=contracts)


@views.route('/g_contracts/<int:contract_id>')
def g_contract_get(contract_id):
    contract = GContract.get_by_id(g.sess, contract_id)
    rate_scripts = g.sess.query(GRateScript).filter(
        GRateScript.g_contract == contract).order_by(
        GRateScript.start_date.desc()).all()

    now = Datetime.utcnow() - relativedelta(months=1)
    month_start = Datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH

    return render_template(
        'g_contract.html', contract=contract, month_start=month_start,
        month_finish=month_finish, rate_scripts=rate_scripts)


@views.route('/g_contracts/add')
def g_contract_add_get():
    contracts = g.sess.query(GContract).order_by(GContract.name)
    return render_template('g_contract_add.html', contracts=contracts)


@views.route('/g_contracts/add', methods=["POST"])
def g_contract_add_post():
    try:
        name = req_str('name')
        start_date = req_date('start')
        charge_script = req_str('charge_script')
        properties = req_zish('properties')

        contract = GContract.insert(
            g.sess, name, charge_script, properties, start_date, None, {})
        g.sess.commit()
        return chellow_redirect("/g_contracts/" + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        contracts = g.sess.query(GContract).order_by(GContract.name)
        return make_response(
            render_template('g_contract_add.html', contracts=contracts), 400)


@views.route('/g_contracts/<int:g_contract_id>/edit')
def g_contract_edit_get(g_contract_id):
    g_contract = GContract.get_by_id(g.sess, g_contract_id)
    return render_template('g_contract_edit.html', g_contract=g_contract)


@views.route('/g_contracts/<int:g_contract_id>/edit', methods=["POST"])
def g_contract_edit_post(g_contract_id):
    try:
        g_contract = GContract.get_by_id(g.sess, g_contract_id)
        if 'delete' in request.values:
            g_contract.delete(g.sess)
            g.sess.commit()
            return chellow_redirect('/g_contracts', 303)
        else:
            name = req_str('name')
            charge_script = req_str('charge_script')
            properties = req_zish('properties')
            g_contract.update(name, charge_script, properties)
            g.sess.commit()
            return chellow_redirect('/g_contracts/' + str(g_contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return make_response(
            render_template('g_contract_edit.html', g_contract=g_contract),
            400)


@views.route('/g_contracts/<int:g_contract_id>/add_rate_script')
def g_rate_script_add_get(g_contract_id):
    now = utc_datetime_now()
    initial_date = utc_datetime(now.year, now.month)
    g_contract = GContract.get_by_id(g.sess, g_contract_id)
    return render_template(
        'g_rate_script_add.html', g_contract=g_contract,
        initial_date=initial_date)


@views.route(
    '/g_contracts/<int:g_contract_id>/add_rate_script', methods=["POST"])
def g_rate_script_add_post(g_contract_id):
    try:
        g_contract = GContract.get_by_id(g.sess, g_contract_id)
        start_date = req_date('start')
        g_rate_script = g_contract.insert_g_rate_script(
            g.sess, start_date, {})
        g.sess.commit()
        return chellow_redirect(
            '/g_rate_scripts/' + str(g_rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = utc_datetime_now()
        initial_date = utc_datetime(now.year, now.month)
        return make_response(
            render_template(
                'g_rate_script_add.html', g_contract=g_contract,
                initial_date=initial_date), 400)


@views.route('/g_rate_scripts/<int:g_rate_script_id>/edit')
def g_rate_script_edit_get(g_rate_script_id):
    g_rate_script = GRateScript.get_by_id(g.sess, g_rate_script_id)
    return render_template(
        'g_rate_script_edit.html', g_rate_script=g_rate_script)


@views.route(
    '/g_rate_scripts/<int:g_rate_script_id>/edit', methods=["POST"])
def g_rate_script_edit_post(g_rate_script_id):
    try:
        g_rate_script = GRateScript.get_by_id(g.sess, g_rate_script_id)
        g_contract = g_rate_script.g_contract
        if 'delete' in request.values:
            g_contract.delete_g_rate_script(g.sess, g_rate_script)
            g.sess.commit()
            return chellow_redirect('/g_contracts/' + str(g_contract.id), 303)
        else:
            script = req_zish('script')
            start_date = req_date('start')
            has_finished = req_bool('has_finished')
            finish_date = req_date('finish') if has_finished else None
            g_contract.update_g_rate_script(
                g.sess, g_rate_script, start_date, finish_date, script)
            g.sess.commit()
            return chellow_redirect(
                '/g_rate_scripts/' + str(g_rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        return make_response(
            render_template(
                'g_rate_script_edit.html', g_rate_script=g_rate_script), 400)


@views.route('/g_rate_scripts/<int:g_rate_script_id>')
def g_rate_script_get(g_rate_script_id):
    g_rate_script = GRateScript.get_by_id(g.sess, g_rate_script_id)
    return render_template('g_rate_script.html', g_rate_script=g_rate_script)


@views.route('/g_batches')
def g_batches_get():
    g_contract_id = req_int('g_contract_id')
    g_contract = GContract.get_by_id(g.sess, g_contract_id)
    g_batches = g.sess.query(GBatch).filter(GBatch.g_contract == g_contract) \
        .order_by(GBatch.reference.desc())
    return render_template(
        'g_batches.html', g_contract=g_contract, g_batches=g_batches)


@views.route('/g_contracts/<int:g_contract_id>/add_batch')
def g_batch_add_get(g_contract_id):
    g_contract = GContract.get_by_id(g.sess, g_contract_id)
    g_batches = g.sess.query(GBatch).filter(
        GBatch.g_contract == g_contract).order_by(GBatch.reference.desc())
    return render_template(
        'g_batch_add.html', g_contract=g_contract, g_batches=g_batches)


@views.route('/g_contracts/<int:g_contract_id>/add_batch', methods=["POST"])
def g_batch_add_post(g_contract_id):
    try:
        g_contract = GContract.get_by_id(g.sess, g_contract_id)
        reference = req_str("reference")
        description = req_str("description")

        g_batch = g_contract.insert_g_batch(g.sess, reference, description)
        g.sess.commit()
        return chellow_redirect("/g_batches/" + str(g_batch.id), 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        g_batches = g.sess.query(GBatch).filter(
            GBatch.g_contract == g_contract).order_by(GBatch.reference.desc())
        return make_response(
            render_template(
                'g_batch_add.html', g_contract=g_contract,
                g_batches=g_batches), 400)


@views.route('/g_batches/<int:g_batch_id>')
def g_batch_get(g_batch_id):
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)
    g_bills = g.sess.query(GBill).options(joinedload('g_reads')).filter(
        GBill.g_batch == g_batch).order_by(
        GBill.reference, GBill.start_date).all()

    num_bills, sum_net_gbp, sum_vat_gbp, sum_gross_gbp, sum_kwh = g.sess.query(
        func.count(GBill.id), func.sum(GBill.net), func.sum(GBill.vat),
        func.sum(GBill.gross), func.sum(GBill.kwh)).filter(
        GBill.g_batch == g_batch).one()

    if sum_net_gbp is None:
        sum_net_gbp = sum_vat_gbp = sum_gross_gbp = sum_kwh = 0

    if len(g_bills) > 0:
        max_reads = max([len(g_bill.g_reads) for g_bill in g_bills])
    else:
        max_reads = 0
    config_contract = Contract.get_non_core_by_name(g.sess, 'configuration')
    properties = config_contract.make_properties()

    if 'g_batch_reports' in properties:
        g_batch_reports = []
        for report_id in properties['g_batch_reports']:
            g_batch_reports.append(Report.get_by_id(g.sess, report_id))
    else:
        g_batch_reports = None

    return render_template(
        'g_batch.html', g_batch_reports=g_batch_reports,
        g_batch=g_batch, g_bills=g_bills, max_reads=max_reads,
        num_bills=num_bills, sum_net_gbp=sum_net_gbp, sum_vat_gbp=sum_vat_gbp,
        sum_gross_gbp=sum_gross_gbp, sum_kwh=sum_kwh)


@views.route('/g_batches/<int:g_batch_id>/edit')
def g_batch_edit_get(g_batch_id):
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)
    return render_template('g_batch_edit.html', g_batch=g_batch)


@views.route('/g_batches/<int:g_batch_id>/edit', methods=["POST"])
def g_batch_edit_post(g_batch_id):
    try:
        g_batch = GBatch.get_by_id(g.sess, g_batch_id)
        if 'update' in request.values:
            reference = req_str('reference')
            description = req_str('description')
            g_batch.update(g.sess, reference, description)
            g.sess.commit()
            return chellow_redirect("/g_batches/" + str(g_batch.id), 303)
        elif 'delete' in request.values:
            g_contract = g_batch.g_contract
            g_batch.delete(g.sess)
            g.sess.commit()
            return chellow_redirect(
                "/g_batches?g_contract_id=" + str(g_contract.id), 303)
        elif 'delete_bills' in request.values:
            g.sess.query(GBill).filter(GBill.g_batch == g_batch).delete(False)
            g.sess.commit()
            return chellow_redirect('/g_batches/' + str(g_batch.id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template('g_batch_edit.html', g_batch=g_batch), 400)


@views.route('/g_bills/<int:g_bill_id>')
def g_bill_get(g_bill_id):
    g_bill = GBill.get_by_id(g.sess, g_bill_id)
    g_reads = g.sess.query(GRegisterRead).filter(
        GRegisterRead.g_bill == g_bill).order_by(
        GRegisterRead.pres_date.desc())
    fields = {'g_bill': g_bill, 'g_reads': g_reads}
    try:
        breakdown = g_bill.make_breakdown()

        raw_lines = g_bill.raw_lines

        rows = set()
        columns = set()
        grid = defaultdict(dict)

        for k, v in tuple(breakdown.items()):
            if k.endswith('_gbp'):
                columns.add('gbp')
                row_name = k[:-4]
                rows.add(row_name)
                grid[row_name]['gbp'] = v
                del breakdown[k]

        for k, v in tuple(breakdown.items()):
            for row_name in sorted(list(rows), key=len, reverse=True):
                if k.startswith(row_name + '_'):
                    col_name = k[len(row_name) + 1:]
                    columns.add(col_name)
                    grid[row_name][col_name] = csv_make_val(v)
                    del breakdown[k]
                    break

        for k, v in breakdown.items():
            pair = k.split('_')
            row_name = '_'.join(pair[:-1])
            column_name = pair[-1]
            rows.add(row_name)
            columns.add(column_name)
            grid[row_name][column_name] = csv_make_val(v)

        column_list = sorted(list(columns))
        for rate_name in [col for col in column_list if col.endswith('rate')]:
            column_list.remove(rate_name)
            column_list.append(rate_name)

        if 'gbp' in column_list:
            column_list.remove('gbp')
            column_list.append('gbp')

        row_list = sorted(list(rows))
        fields.update(
            {
                'raw_lines': raw_lines, 'row_list': row_list,
                'column_list': column_list, 'grid': grid})
    except SyntaxError:
        pass
    return render_template('g_bill.html', **fields)


@views.route('/g_bill_imports')
def g_bill_imports_get():
    g_batch_id = req_int('g_batch_id')
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)
    importer_ids = sorted(
        chellow.g_bill_import.get_bill_importer_ids(g_batch.id), reverse=True)

    return render_template(
        'g_bill_imports.html', importer_ids=importer_ids, g_batch=g_batch,
        parser_names=chellow.g_bill_import.find_parser_names())


@views.route('/g_bill_imports', methods=["POST"])
def g_bill_imports_post():
    try:
        g_batch_id = req_int('g_batch_id')
        g_batch = GBatch.get_by_id(g.sess, g_batch_id)
        file_item = req_file("import_file")
        file_bytes = file_item.stream.read()
        imp_id = chellow.g_bill_import.start_bill_importer(
            g.sess, g_batch.id, file_item.filename, file_bytes)
        return chellow_redirect("/g_bill_imports/" + str(imp_id), 303)
    except BadRequest as e:
        flash(e.description)
        importer_ids = sorted(
            chellow.g_bill_import.get_bill_importer_ids(g_batch.id),
            reverse=True)
        return make_response(
            render_template(
                'g_bill_imports.html', importer_ids=importer_ids,
                g_batch=g_batch,
                parser_names=chellow.g_bill_import.find_parser_names()), 400)


@views.route('/g_bill_imports/<int:imp_id>')
def g_bill_import_get(imp_id):
    importer = chellow.g_bill_import.get_bill_importer(imp_id)
    g_batch = GBatch.get_by_id(g.sess, importer.g_batch_id)
    fields = {'g_batch': g_batch}
    if importer is not None:
        imp_fields = importer.make_fields()
        if 'successful_bills' in imp_fields and \
                len(imp_fields['successful_bills']) > 0:
            fields['successful_max_registers'] = \
                max(len(bill['reads']) for bill in
                    imp_fields['successful_bills'])
        fields.update(imp_fields)
        fields['status'] = importer.status()
    return render_template('g_bill_import.html', **fields)


@views.route('/g_batches/<int:g_batch_id>/add_bill')
def g_bill_add_get(g_batch_id):
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)
    g_bills = g.sess.query(GBill).filter(GBill.g_batch == g_batch).order_by(
        GBill.start_date)
    bill_types = g.sess.query(BillType).order_by(BillType.code).all()
    return render_template(
        'g_bill_add.html', g_batch=g_batch, g_bills=g_bills,
        bill_types=bill_types)


@views.route('/g_batches/<int:g_batch_id>/add_bill', methods=['POST'])
def g_bill_add_post(g_batch_id):
    try:
        g_batch = GBatch.get_by_id(g.sess, g_batch_id)
        bill_type_id = req_int('bill_type_id')
        bill_type = BillType.get_by_id(g.sess, bill_type_id)
        mprn = req_str('mprn')
        g_supply = GSupply.get_by_mprn(g.sess, mprn)
        account = req_str('account')
        reference = req_str('reference')
        issue_date = req_date('issue')
        start_date = req_date('start')
        finish_date = req_date('finish')
        kwh = req_decimal('kwh')
        net = req_decimal('net')
        vat = req_decimal('vat')
        gross = req_decimal('gross')
        breakdown = req_zish("breakdown")
        g_bill = g_batch.insert_g_bill(
            g.sess, g_supply, bill_type, reference, account, issue_date,
            start_date, finish_date, kwh, net, vat, gross, '', breakdown)
        g.sess.commit()
        return chellow_redirect("/g_bills/" + str(g_bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        g.sess.rollback()
        g_bills = g.sess.query(GBill).filter(GBill.g_batch == g_batch). \
            order_by(GBill.start_date)
        bill_types = g.sess.query(BillType).order_by(BillType.code).all()
        return make_response(
            render_template(
                'g_bill_add.html', g_batch=g_batch, g_bills=g_bills,
                bill_types=bill_types), 400)


@views.route('/g_supplies/<int:g_supply_id>/notes')
def g_supply_notes_get(g_supply_id):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)

    if len(g_supply.note.strip()) > 0:
        note_str = g_supply.note
    else:
        note_str = "{'notes': []}"
    g_supply_note = eval(note_str)

    return render_template(
        'g_supply_notes.html', g_supply=g_supply, g_supply_note=g_supply_note)


@views.route('/g_supplies/<int:g_supply_id>/notes/add')
def g_supply_note_add_get(g_supply_id):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)
    return render_template('g_supply_note_add.html', g_supply=g_supply)


@views.route('/g_supplies/<int:g_supply_id>/notes/add', methods=['POST'])
def g_supply_note_add_post(g_supply_id):
    try:
        g_supply = GSupply.get_by_id(g.sess, g_supply_id)
        body = req_str('body')
        category = req_str('category')
        is_important = req_bool('is_important')
        if len(g_supply.note.strip()) == 0:
            g_supply.note = "{'notes': []}"
        note_dict = eval(g_supply.note)
        note_dict['notes'].append(
            {
                'category': category, 'is_important': is_important,
                'body': body})
        g_supply.note = str(note_dict)
        g.sess.commit()
        return chellow_redirect('/g_supplies/' + str(g_supply_id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template('g_supply_note_add.html', g_supply=g_supply), 400)


@views.route('/g_supplies/<int:g_supply_id>/notes/<int:index>/edit')
def g_supply_note_edit_get(g_supply_id, index):
    g_supply = GSupply.get_by_id(g.sess, g_supply_id)
    g_supply_note = eval(g_supply.note)
    note = g_supply_note['notes'][index]
    note['index'] = index
    return render_template(
        'g_supply_note_edit.html', g_supply=g_supply, note=note)


@views.route(
    '/g_supplies/<int:g_supply_id>/notes/<int:index>/edit', methods=['POST'])
def g_supply_note_edit_post(g_supply_id, index):
    try:
        g_supply = GSupply.get_by_id(g.sess, g_supply_id)
        g_supply_note = eval(g_supply.note)
        if 'delete' in request.values:
            del g_supply_note['notes'][index]
            g_supply.note = str(g_supply_note)
            g.sess.commit()
            return chellow_redirect(
                "/g_supplies/" + str(g_supply_id) + '/notes', 303)
        else:
            category = req_str('category')
            is_important = req_bool('is_important')
            body = req_str('body')
            note = g_supply_note['notes'][index]
            note['category'] = category
            note['is_important'] = is_important
            note['body'] = body
            g_supply.note = str(g_supply_note)
            g.sess.commit()
            return chellow_redirect(
                '/g_supplies/' + str(g_supply_id) + '/notes', 303)
    except BadRequest as e:
        flash(e.description)
        g_supply_note = eval(g_supply.note)
        note = g_supply_note['notes'][index]
        note['index'] = index
        return render_template(
            'g_supply_note_edit.html', g_supply=g_supply, note=note)


@views.route('/g_eras/<int:g_era_id>/edit')
def g_era_edit_get(g_era_id):
    g_era = GEra.get_by_id(g.sess, g_era_id)
    supplier_g_contracts = g.sess.query(GContract).order_by(GContract.name)
    site_g_eras = g.sess.query(SiteGEra).join(Site).filter(
        SiteGEra.g_era == g_era).order_by(Site.code).all()
    g_units = g.sess.query(GUnit).order_by(GUnit.code).all()
    g_reading_frequencies = g.sess.query(GReadingFrequency).order_by(
        GReadingFrequency.code).all()
    return render_template(
        'g_era_edit.html', g_era=g_era,
        supplier_g_contracts=supplier_g_contracts, site_g_eras=site_g_eras,
        g_units=g_units, g_reading_frequencies=g_reading_frequencies)


@views.route('/g_eras/<int:g_era_id>/edit', methods=['POST'])
def g_era_edit_post(g_era_id):
    try:
        g_era = GEra.get_by_id(g.sess, g_era_id)

        if 'delete' in request.values:
            g_supply = g_era.g_supply
            g_supply.delete_g_era(g.sess, g_era)
            g.sess.commit()
            return chellow_redirect('/g_supplies/' + str(g_supply.id), 303)
        elif 'attach' in request.values:
            site_code = req_str('site_code')
            site = Site.get_by_code(g.sess, site_code)
            g_era.attach_site(g.sess, site)
            g.sess.commit()
            return chellow_redirect(
                '/g_supplies/' + str(g_era.g_supply.id), 303)
        elif 'detach' in request.values:
            site_id = req_int('site_id')
            site = Site.get_by_id(g.sess, site_id)
            g_era.detach_site(g.sess, site)
            g.sess.commit()
            return chellow_redirect(
                '/g_supplies/' + str(g_era.g_supply.id), 303)
        elif 'locate' in request.values:
            site_id = req_int('site_id')
            site = Site.get_by_id(g.sess, site_id)
            g_era.set_physical_location(g.sess, site)
            g.sess.commit()
            return chellow_redirect(
                '/g_supplies/' + str(g_era.g_supply.id), 303)
        else:
            start_date = req_date('start')
            is_ended = req_bool('is_ended')
            finish_date = req_date('finish') if is_ended else None
            msn = req_str('msn')
            correction_factor = req_decimal('correction_factor')
            g_contract_id = req_int('g_contract_id')
            g_contract = GContract.get_by_id(g.sess, g_contract_id)
            account = req_str('account')
            g_unit_id = req_int('g_unit_id')
            g_unit = GUnit.get_by_id(g.sess, g_unit_id)
            g_reading_frequency_id = req_int('g_reading_frequency_id')
            g_reading_frequency = GReadingFrequency.get_by_id(
                g.sess, g_reading_frequency_id)
            g_era.g_supply.update_g_era(
                g.sess, g_era, start_date, finish_date, msn, correction_factor,
                g_unit, g_contract, account, g_reading_frequency)
            g.sess.commit()
            return chellow_redirect(
                '/g_supplies/' + str(g_era.g_supply.id), 303)
    except BadRequest as e:
        flash(e.description)
        supplier_g_contracts = g.sess.query(GContract).order_by(GContract.name)
        site_g_eras = g.sess.query(SiteGEra).join(Site).filter(
            SiteGEra.g_era == g_era).order_by(Site.code).all()
        g_units = g.sess.query(GUnit).order_by(GUnit.code).all()
        g_reading_frequencies = g.sess.query(GReadingFrequency).order_by(
            GReadingFrequency.code).all()
        return make_response(
            render_template(
                'g_era_edit.html', g_era=g_era,
                supplier_g_contracts=supplier_g_contracts,
                site_g_eras=site_g_eras, g_units=g_units,
                g_reading_frequencies=g_reading_frequencies), 400)


@views.route('/g_bills/<int:g_bill_id>/edit')
def g_bill_edit_get(g_bill_id):
    g_bill = GBill.get_by_id(g.sess, g_bill_id)
    bill_types = g.sess.query(BillType).order_by(BillType.code).all()
    return render_template(
        'g_bill_edit.html', g_bill=g_bill, bill_types=bill_types)


@views.route('/g_bills/<int:g_bill_id>/edit', methods=['POST'])
def g_bill_edit_post(g_bill_id):
    try:
        g_bill = GBill.get_by_id(g.sess, g_bill_id)
        if 'delete' in request.values:
            g_batch = g_bill.g_batch
            g_bill.delete(g.sess)
            g.sess.commit()
            return chellow_redirect("/g_batches/" + str(g_batch.id), 303)
        else:
            account = req_str('account')
            reference = req_str('reference')
            issue_date = req_date('issue')
            start_date = req_date('start')
            finish_date = req_date('finish')
            kwh = req_decimal('kwh')
            net_gbp = req_decimal('net_gbp')
            vat_gbp = req_decimal('vat_gbp')
            gross_gbp = req_decimal('gross_gbp')
            type_id = req_int('bill_type_id')
            raw_lines = req_str('raw_lines')
            breakdown = req_zish('breakdown')
            bill_type = BillType.get_by_id(g.sess, type_id)

            g_bill.update(
                bill_type, reference, account, issue_date, start_date,
                finish_date, kwh, net_gbp, vat_gbp, gross_gbp, raw_lines,
                breakdown)
            g.sess.commit()
            return chellow_redirect("/g_bills/" + str(g_bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        g_bill = GBill.get_by_id(g.sess, g_bill_id)
        bill_types = g.sess.query(BillType).order_by(BillType.code).all()
        return make_response(
            render_template(
                'g_bill_edit.html', g_bill=g_bill, bill_types=bill_types),
            400)


@views.route('/g_bills/<int:g_bill_id>/add_read')
def g_read_add_get(g_bill_id):
    g_read_types = g.sess.query(GReadType).order_by(GReadType.code)
    g_bill = GBill.get_by_id(g.sess, g_bill_id)
    g_units = g.sess.query(GUnit).order_by(GUnit.code)
    return render_template(
        'g_read_add.html', g_bill=g_bill, g_read_types=g_read_types,
        g_units=g_units)


@views.route('/g_bills/<int:g_bill_id>/add_read', methods=['POST'])
def g_read_add_post(g_bill_id):
    try:
        g_bill = GBill.get_by_id(g.sess, g_bill_id)
        msn = req_str('msn')
        g_unit_id = req_int('g_unit_id')
        g_unit = GUnit.get_by_id(g.sess, g_unit_id)
        correction_factor = req_decimal('correction_factor')
        calorific_value = req_decimal('calorific_value')
        prev_date = req_date('prev_date')
        prev_value = req_decimal('prev_value')
        prev_type_id = req_int('prev_type_id')
        prev_type = GReadType.get_by_id(g.sess, prev_type_id)
        pres_date = req_date('pres_date')
        pres_value = req_decimal('pres_value')
        pres_type_id = req_int('pres_type_id')
        pres_type = GReadType.get_by_id(g.sess, pres_type_id)

        g_bill.insert_g_read(
            g.sess, msn, g_unit, correction_factor, calorific_value,
            prev_value, prev_date, prev_type, pres_value, pres_date, pres_type)
        g.sess.commit()
        return chellow_redirect("/g_bills/" + str(g_bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        g_read_types = g.sess.query(GReadType).order_by(GReadType.code)
        return render_template(
            'g_read_add.html', g_bill=g_bill, g_read_types=g_read_types)


@views.route('/g_reads/<int:g_read_id>/edit')
def g_read_edit_get(g_read_id):
    g_read_types = g.sess.query(GReadType).order_by(GReadType.code).all()
    g_read = GRegisterRead.get_by_id(g.sess, g_read_id)
    g_units = g.sess.query(GUnit).order_by(GUnit.code)
    return render_template(
        'g_read_edit.html', g_read=g_read, g_read_types=g_read_types,
        g_units=g_units)


@views.route('/g_reads/<int:g_read_id>/edit', methods=['POST'])
def g_read_edit_post(g_read_id):
    try:
        g_read = GRegisterRead.get_by_id(g.sess, g_read_id)
        if 'update' in request.values:
            msn = req_str('msn')
            prev_date = req_date('prev_date')
            prev_value = req_decimal('prev_value')
            prev_type_id = req_int('prev_type_id')
            prev_type = GReadType.get_by_id(g.sess, prev_type_id)
            pres_date = req_date('pres_date')
            pres_value = req_decimal('pres_value')
            pres_type_id = req_int('pres_type_id')
            pres_type = GReadType.get_by_id(g.sess, pres_type_id)
            g_unit_id = req_int('g_unit_id')
            g_unit = GUnit.get_by_id(g.sess, g_unit_id)
            correction_factor = req_decimal('correction_factor')
            calorific_value = req_decimal('calorific_value')

            g_read.update(
                msn, g_unit, correction_factor, calorific_value, prev_value,
                prev_date, prev_type, pres_value, pres_date, pres_type)

            g.sess.commit()
            return chellow_redirect("/g_bills/" + str(g_read.g_bill.id), 303)
        elif 'delete' in request.values:
            g_bill = g_read.g_bill
            g_read.delete(g.sess)
            g.sess.commit()
            return chellow_redirect('/g_bills/' + str(g_bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        g_read_types = g.sess.query(GReadType).order_by(GReadType.code).all()
        g_units = g.sess.query(GUnit).order_by(GUnit.code)
        return make_response(
            render_template(
                'g_read_edit.html', g_read=g_read, g_read_types=g_read_types,
                g_units=g_units), 400)


@views.route('/g_units')
def g_units_get():
    g_units = g.sess.query(GUnit).order_by(GUnit.code)
    return render_template('g_units.html', g_units=g_units)


@views.route('/g_units/<int:g_unit_id>')
def g_unit_get(g_unit_id):
    g_unit = GUnit.get_by_id(g.sess, g_unit_id)
    return render_template('g_unit.html', g_unit=g_unit)


@views.route('/g_read_types/<int:g_read_type_id>')
def g_read_type_get(g_read_type_id):
    g_read_type = GReadType.get_by_id(g.sess, g_read_type_id)
    return render_template('g_read_type.html', g_read_type=g_read_type)


@views.route('/g_read_types')
def g_read_types_get():
    g_read_types = g.sess.query(GReadType).order_by(GReadType.code)
    return render_template('g_read_types.html', g_read_types=g_read_types)


@views.route('/g_reports')
def g_reports_get():
    now = utc_datetime_now()
    now_day = utc_datetime(now.year, now.month, now.day)
    month_start = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = Datetime(now.year, now.month, 1) - HH
    return render_template(
        'g_reports.html', month_start=month_start, month_finish=month_finish,
        now_day=now_day)


@views.route('/g_dns')
def g_dns_get():
    g_dns = g.sess.query(GDn).order_by(GDn.code)
    return render_template('g_dns.html', g_dns=g_dns)


@views.route('/g_dns/<int:g_dn_id>')
def g_dn_get(g_dn_id):
    g_dn = GDn.get_by_id(g.sess, g_dn_id)
    g_ldzs = g.sess.query(GLdz).filter(
        GLdz.g_dn == g_dn).order_by(GLdz.code).all()
    return render_template('g_dn.html', g_dn=g_dn, g_ldzs=g_ldzs)


@views.route('/g_ldzs/<int:g_ldz_id>')
def g_ldz_get(g_ldz_id):
    g_ldz = GLdz.get_by_id(g.sess, g_ldz_id)
    g_exit_zones = g.sess.query(GExitZone).filter(
        GExitZone.g_ldz == g_ldz).order_by(GExitZone.code).all()
    return render_template(
        'g_ldz.html', g_ldz=g_ldz, g_exit_zones=g_exit_zones)


@views.route('/g_ldzs')
def g_ldzs_get():
    g_ldzs = g.sess.query(GLdz).order_by(GLdz.code)
    return render_template('g_ldzs.html', g_ldzs=g_ldzs)


@views.route('/g_reading_frequencies/<int:g_reading_frequency_id>')
def g_reading_frequency_get(g_reading_frequency_id):
    g_reading_frequency = GReadingFrequency.get_by_id(
        g.sess, g_reading_frequency_id)
    return render_template(
        'g_reading_frequency.html', g_reading_frequency=g_reading_frequency)


@views.route('/g_reading_frequencies')
def g_reading_frequencies_get():
    g_reading_frequencies = g.sess.query(GReadingFrequency).order_by(
        GReadingFrequency.code)
    return render_template(
        'g_reading_frequencies.html',
        g_reading_frequencies=g_reading_frequencies)


@views.route('/g_exit_zones/<int:g_exit_zone_id>')
def g_exit_zone_get(g_exit_zone_id):
    g_exit_zone = GExitZone.get_by_id(g.sess, g_exit_zone_id)
    return render_template('g_exit_zone.html', g_exit_zone=g_exit_zone)


@views.route('/g_batches/<int:g_batch_id>/csv')
def g_batch_csv_get(g_batch_id):
    g_batch = GBatch.get_by_id(g.sess, g_batch_id)
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(
        [
            "Contract", "Batch Reference", "Bill Reference", "Account",
            "Issued", "From", "To", "kWh", "Net", "VAT", "Gross", "Type"])
    for g_bill in g.sess.query(GBill).filter(
            GBill.g_batch == g_batch).order_by(
            GBill.reference, GBill.start_date).options(
                joinedload(GBill.bill_type)):
        cw.writerow(
            [
                g_batch.g_contract.name, g_batch.reference, g_bill.reference,
                g_bill.account, hh_format(g_bill.issue_date),
                hh_format(g_bill.start_date), hh_format(g_bill.finish_date),
                str(g_bill.kwh), str(g_bill.net), str(g_bill.vat),
                str(g_bill.gross), g_bill.bill_type.code])

    disp = 'attachment; filename="g_batch_' + str(g_batch.id) + '.csv"'
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = disp
    output.headers["Content-type"] = "text/csv"
    return output
