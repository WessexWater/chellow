import hashlib
from flask import (
    request, Response, g, redirect, render_template, send_file, flash,
    make_response)
from chellow import app
from chellow.models import (
    Contract, Report, User, set_read_write, db, Party, MarketRole, Participant,
    UserRole, Site, Source, GeneratorType, GspGroup, Era, SiteEra, Pc, Cop,
    Ssc, RateScript, Supply, Mtc, Channel, Tpr, MeasurementRequirement, Bill,
    RegisterRead, HhDatum, Snag, Batch, ReadType, BillType, MeterPaymentType,
    ClockInterval, db_upgrade)
from sqlalchemy.exc import ProgrammingError
import traceback
from datetime import datetime as Datetime
import os
import pytz
from dateutil.relativedelta import relativedelta
from chellow.utils import (
    HH, req_str, req_int, req_date, parse_mpan_core, req_bool, req_hh_date,
    hh_after, req_decimal, send_response, hh_before)
from werkzeug.exceptions import BadRequest
import chellow.general_import
import io
import chellow.hh_importer
import chellow.bill_importer
import chellow.system_price
from sqlalchemy import text, true, false, null, func, not_, or_
from sqlalchemy.orm import joinedload
from collections import defaultdict
from itertools import chain, islice
import importlib
import math
import operator
import ast
from importlib import import_module
import sys
import chellow.rcrc
import chellow.bsuos
import chellow.tlms
import chellow.bank_holidays
import chellow.dloads


APPLICATION_ROOT = app.config['APPLICATION_ROOT']
CONTEXT_PATH = '' if APPLICATION_ROOT is None else APPLICATION_ROOT


@app.before_first_request
def before_first_request():
    db_upgrade()
    chellow.rcrc.startup()
    chellow.bsuos.startup()
    chellow.system_price.startup()
    chellow.hh_importer.startup()
    chellow.tlms.startup()
    chellow.bank_holidays.startup()
    chellow.dloads.startup()


@app.context_processor
def chellow_context_processor():
    return {
        'context_path': CONTEXT_PATH,
        'current_user': g.user}

TEMPLATE_FORMATS = {
    'year': '%Y', 'month': '%m', 'day': '%d', 'hour': '%H',
    'minute': '%M', 'full': '%Y-%m-%d %H:%M', 'date': '%Y-%m-%d'}


@app.template_filter('hh_format')
def hh_format_filter(dt, modifier='full'):
    return "Ongoing" if dt is None else dt.strftime(TEMPLATE_FORMATS[modifier])


@app.template_filter('now_if_none')
def now_if_none(dt):
    return Datetime.utcnow() if dt is None else dt


'''
def chellow_redirect(path, code=None):
    try:
        scheme = request.headers['X-Forwarded-Proto']
    except KeyError:
        scheme = 'http'

    location = scheme + '://' + request.host + path
    if code is None:
        return redirect(location)
    else:
        return redirect(location, code)
'''


@app.before_request
def check_permissions(*args, **kwargs):
    g.user = None
    sess = db.session()
    auth = request.authorization

    if auth is None:
        config_contract = Contract.get_non_core_by_name(sess, 'configuration')
        try:
            ips = config_contract.make_properties()['ips']
            if request.remote_addr in ips:
                key = request.remote_addr
            elif '*.*.*.*' in ips:
                key = '*.*.*.*'
            else:
                key = None

            email = ips[key]
            g.user = User.query.filter(User.email_address == email).first()
        except KeyError:
            pass
    else:
        pword_digest = hashlib.md5(auth.password.encode()).hexdigest()
        g.user = User.query.filter(
            User.email_address == auth.username,
            User.password_digest == pword_digest).first()

    # Got our user
    path = request.path
    method = request.method
    if method == 'GET' and path in (
            '/health', '/bmreports',
            '/elexonportal/file/download/BESTVIEWPRICES_FILE'):
        return

    if g.user is not None:
        role = g.user.user_role
        role_code = role.code

        if role_code == "viewer" and method in ("GET", "HEAD"):
            return
        elif role_code == "editor":
            return
        elif role_code == "party-viewer":
            if method in ("GET", "HEAD"):
                party = g.user.party
                market_role_code = party.market_role.code
                if market_role_code == 'C':
                    hhdc_contract_id = request.args["hhdc_contract_id"]
                    hhdc_contract = Contract.get_hhdc_by_id(
                        sess, hhdc_contract_id)
                    if hhdc_contract.party == party and \
                            request.full_path.startswith(
                                "/channel_snags?"):
                        return
                elif market_role_code == 'X':
                    if path.startswith(
                            "/supplier_contracts/" + party.id):
                        return

    if g.user is None and User.query.count() == 0:
        sess.rollback()
        set_read_write(sess)
        user_role = sess.query(UserRole).filter(
            UserRole.code == 'editor').one()
        User.insert(
            sess, 'admin@example.com', User.digest('admin'), user_role,
            None)
        sess.commit()
        return

    if g.user is None or auth is None:
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Chellow"'})

    return Response('Forbidden', 403)


el_dir = {
    'SYSPRICE': 'sysprice'
}


@app.route('/bmreports')
def bmreports():
    element = request.args['element']
    date_str = request.args['dT']
    fname = Datetime.strptime(date_str, '%Y-%M-%d'). \
        strftime('%Y_%M_%d') + '.xml'
    f = open(
        os.path.join(
            os.path.dirname(__file__), 'bmreports', el_dir[element], fname))

    return Response(f, status=200, mimetype='text/xml')


@app.route('/elexonportal/file/download/BESTVIEWPRICES_FILE')
def elexonportal():
    key = request.args['key']
    if key != 'xxx':
        raise Exception("The key should be 'xxx'")
    fname = os.path.join(
        os.path.dirname(__file__), 'elexonportal', 'prices.xls')
    return send_file(
        fname, mimetype='application/binary', as_attachment=True,
        attachment_filename='prices.xls')


@app.route('/health')
def health():
    return Response('healthy\n', mimetype='text/plain')


@app.route('/local_reports/<int:report_id>/output', methods=['GET', 'POST'])
def local_report_output_post(report_id):
    response = None
    report = Report.query.get(report_id)
    try:
        exec(
            report.script, {
                'report_id': report_id,
                'response': response,
                'template': report.template})
        return response
    except:
        return Response(traceback.format_exc(), status=500)


@app.route('/local_reports', methods=['GET'])
def local_reports_get():
    reports = Report.query.order_by(Report.id, Report.name).all()
    return render_template('local_reports.html', reports=reports)


@app.route('/local_reports', methods=['POST'])
def local_reports_post():
    sess = db.session()
    set_read_write(sess)
    name = req_str("name")
    report = Report(name, "", None)
    db.session.add(report)
    try:
        db.session.commit()
    except ProgrammingError as e:
        if 'duplicate key value violates unique constraint' in str(e):
            return Response(
                "There's already a report with that name.", status=400)
        else:
            raise
    return redirect('/local_reports/' + str(report.id), 303)


@app.route('/local_reports/<int:report_id>')
def local_report_get(report_id):
    sess = db.session()
    report = Report.get_by_id(sess, report_id)
    return render_template('local_report.html', report=report)


@app.route('/local_reports/<int:report_id>', methods=['POST'])
def local_report_post(report_id):
    sess = db.session()
    set_read_write(sess)
    report = Report.get_by_id(sess, report_id)
    name = req_str("name")
    script = req_str("script")
    template = req_str("template")
    report.update(name, script, template)
    try:
        sess.commit()
    except BadRequest as e:
        if 'duplicate key value violates unique constraint' in str(e):
            return Response(
                "There's already a report with that name.", status=400)
        else:
            raise
    return redirect('/local_reports/' + str(report.id), 303)


@app.route('/system')
def system_get():
    traces = []
    for thread_id, stack in sys._current_frames().items():
        traces.append("\n# ThreadID: %s" % thread_id)
        for filename, lineno, name, line in traceback.extract_stack(stack):
            traces.append(
                'File: "%s", line %d, in %s' % (filename, lineno, name))
            if line:
                traces.append("  %s" % (line.strip()))
    return render_template(
        'system.html', traces='\n'.join(traces),
        version_number=chellow.versions['version'],
        version_hash=chellow.versions['full-revisionid'])


@app.route('/')
def home_get():
    sess = db.session()
    config = Contract.get_non_core_by_name(sess, 'configuration')
    now = Datetime.now(pytz.utc)
    month_start = Datetime(now.year, now.month, 1) - \
        relativedelta(months=1)
    month_finish = Datetime(now.year, now.month, 1) - HH

    return render_template(
        'home.html', properties=config.make_properties(),
        month_start=month_start, month_finish=month_finish)


@app.errorhandler(500)
def error_500(error):
    return traceback.format_exc(), 500


@app.errorhandler(RuntimeError)
def error_runtime(error):
    return "called rtime handler " + str(error), 500


@app.route('/users', methods=['GET'])
def users_get():
    users = User.query.order_by(User.email_address).all()
    parties = Party.query.join(MarketRole).join(Participant).order_by(
        MarketRole.code, Participant.code).all()
    return render_template('users.html', users=users, parties=parties)


@app.route('/users', methods=['POST'])
def users_post():
    sess = db.session
    set_read_write(sess)
    email_address = req_str('email_address')
    password = req_str('password')
    user_role_code = req_str('user_role_code')
    role = UserRole.get_by_code(sess, user_role_code)
    try:
        party = None
        if role.code == 'party-viewer':
            party_id = req_int('party_id')
            party = sess.query(Party).get(party_id)
        user = User.insert(
            sess, email_address, User.digest(password), role, party)
        sess.commit()
        return redirect('/users/' + str(user.id), 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        users = sess.query(User).order_by(User.email_address).all()
        parties = sess.query(Party).join(MarketRole).join(Participant). \
            order_by(MarketRole.code, Participant.code).all()
        return make_response(
            render_template('users.html', users=users, parties=parties), 400)


@app.route('/users/<int:user_id>', methods=['DELETE'])
def user_delete(user_id):
    try:
        sess = db.session
        set_read_write(sess)
        user = User.get_by_id(sess, user_id)
        sess.delete(user)
        sess.commit()
        return redirect('/users', 303)
    except BadRequest as e:
        flash(e.description)
        parties = Party.query.join(MarketRole).join(Participant).order_by(
            MarketRole.code, Participant.code)
        return make_response(
            render_template('user.html',  parties=parties, user=user), 400)


@app.route('/users/<int:user_id>', methods=['POST'])
def user_post(user_id):
    try:
        sess = db.session
        set_read_write(sess)
        user = User.get_by_id(sess, user_id)
        if 'current_password' in request.values:
            current_password = req_str('current_password')
            new_password = req_str('new_password')
            confirm_new_password = req_str('confirm_new_password')
            if user.password_digest != User.digest(current_password):
                raise BadRequest("The current password is incorrect.")
            if new_password != confirm_new_password:
                raise BadRequest("The new passwords aren't the same.")
            if len(new_password) < 6:
                raise BadRequest(
                    "The password must be at least 6 characters long.")
            user.password_digest = User.digest(new_password)
            sess.commit()
            return redirect('/users/' + str(user.id), 303)
        else:
            email_address = req_str('email_address')
            user_role_code = req_str('user_role_code')
            user_role = UserRole.get_by_code(sess, user_role_code)
            party = None
            if user_role.code == 'party-viewer':
                party_id = req_int('party_id')
                party = Party.get_by_id(sess, party_id)
            user.update(email_address, user_role, party)
            sess.commit()
            return redirect('/users/' + str(user.id), 303)
    except BadRequest as e:
        flash(e.description)
        parties = Party.query.join(MarketRole).join(Participant).order_by(
            MarketRole.code, Participant.code)
        return make_response(
            render_template('user.html',  parties=parties, user=user), 400)


@app.route('/users/<int:user_id>')
def user_get(user_id):
    sess = db.session
    parties = Party.query.join(MarketRole).join(Participant).order_by(
        MarketRole.code, Participant.code)
    user = User.get_by_id(sess, user_id)
    return render_template('user.html', parties=parties, user=user)


@app.route('/general_imports')
def general_imports_get():
    return render_template(
        'general_imports.html',
        process_ids=sorted(
            chellow.general_import.get_process_ids(), reverse=True))


@app.route('/general_imports', methods=['POST'])
def general_imports_post():
    try:
        file_item = request.files["import_file"]
        file_name = file_item.filename
        if not file_name.endswith('.csv'):
            raise BadRequest(
                "The file name should have the extension '.csv'.")
        f = io.StringIO(str(file_item.stream.read(), 'utf-8'))
        f.seek(0)
        proc_id = chellow.general_import.start_process(f)
        return redirect('/general_imports/' + str(proc_id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template(
            'general_imports.html',
            process_ids=sorted(
                chellow.general_import.get_process_ids(), reverse=True))


@app.route('/general_imports/<int:import_id>')
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


@app.route('/sites/<int:site_id>/edit')
def site_edit_get(site_id):
    try:
        sess = db.session()
        site = Site.get_by_id(sess, site_id)
        sources = Source.query.order_by(Source.code)
        generator_types = GeneratorType.query.order_by(GeneratorType.code)
        gsp_groups = GspGroup.query.order_by(GspGroup.code)
        eras = Era.query.join(SiteEra).filter(
            SiteEra.site == site).order_by(Era.start_date.desc())
        mop_contracts = Contract.query.join(MarketRole).filter(
            MarketRole.code == 'M').order_by(Contract.name)
        hhdc_contracts = Contract.query.join(MarketRole).filter(
            MarketRole.code == 'C').order_by(Contract.name)
        supplier_contracts = Contract.query.join(MarketRole).filter(
            MarketRole.code == 'X').order_by(Contract.name)
        pcs = Pc.query.order_by(Pc.code)
        cops = Cop.query.order_by(Cop.code)
        return render_template(
            'site_edit.html', site=site, sources=sources,
            generator_types=generator_types, gsp_groups=gsp_groups, eras=eras,
            mop_contracts=mop_contracts, hhdc_contracts=hhdc_contracts,
            supplier_contracts=supplier_contracts, pcs=pcs, cops=cops)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        return render_template(
            'site_edit.html', site=site, sources=sources,
            generator_types=generator_types, gsp_groups=gsp_groups, eras=eras,
            mop_contracts=mop_contracts, hhdc_contracts=hhdc_contracts,
            supplier_contracts=supplier_contracts, pcs=pcs, cops=cops)


@app.route('/sites/<int:site_id>/edit', methods=['POST'])
def site_edit_post(site_id):
    try:
        sess = db.session()
        chellow.models.set_read_write(sess)
        site = Site.get_by_id(sess, site_id)
        if 'delete' in request.form:
            site.delete(sess)
            sess.commit()
            flash("Site deleted successfully.")
            return redirect('/sites/', 303)
        elif 'update' in request.form:
            code = req_str('code')
            name = req_str('site_name')
            site.update(code, name)
            sess.commit()
            flash("Site updated successfully.")
            return redirect('/sites/' + str(site.id), 303)
        elif 'insert' in request.form:
            name = req_str("name")
            source_id = req_int("source_id")
            source = Source.get_by_id(sess, source_id)
            gsp_group_id = req_int("gsp_group_id")
            gsp_group = GspGroup.get_by_id(sess, gsp_group_id)
            mop_contract_id = req_int("mop_contract_id")
            mop_contract = Contract.get_mop_by_id(sess, mop_contract_id)
            mop_account = req_str("mop_account")
            hhdc_contract_id = req_str("hhdc_contract_id")
            hhdc_contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)
            hhdc_account = req_str("hhdc_account")
            msn = req_str("msn")
            pc_id = req_int("pc_id")
            pc = Pc.get_by_id(sess, pc_id)
            mtc_code = req_str("mtc_code")
            cop_id = req_int("cop_id")
            cop = Cop.get_by_id(sess, cop_id)
            ssc_code = req_str("ssc_code")
            ssc_code = ssc_code.strip()
            if len(ssc_code) > 0:
                ssc = Ssc.get_by_code(sess, ssc_code)
            else:
                ssc = None
            start_date = req_date("start")
            if 'generator_type_id' in request.form:
                generator_type_id = req_int("generator_type_id")
                generator_type = GeneratorType.get_by_id(
                    sess, generator_type_id)
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
                    sess, imp_supplier_contract_id)
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
                    sess, exp_supplier_contract_id)
                exp_supplier_account = req_str("exp_supplier_account")
                exp_sc = req_int('exp_sc')
                exp_llfc_code = req_str("exp_llfc_code")

            supply = site.insert_supply(
                sess, source, generator_type, name, start_date, None,
                gsp_group, mop_contract, mop_account, hhdc_contract,
                hhdc_account, msn, pc, mtc_code, cop, ssc, imp_mpan_core,
                imp_llfc_code, imp_supplier_contract, imp_supplier_account,
                imp_sc, exp_mpan_core, exp_llfc_code, exp_supplier_contract,
                exp_supplier_account, exp_sc)
            sess.commit()
            return redirect("/supplies/" + str(supply.id), 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        sources = Source.query.order_by(Source.code)
        generator_types = GeneratorType.query.order_by(GeneratorType.code)
        gsp_groups = GspGroup.query.order_by(GspGroup.code)
        eras = Era.query.join(SiteEra).filter(
            SiteEra.site == site).order_by(Era.start_date.desc())
        mop_contracts = Contract.query.join(MarketRole).filter(
            MarketRole.code == 'M').order_by(Contract.name)
        hhdc_contracts = Contract.query.join(MarketRole).filter(
            MarketRole.code == 'C').order_by(Contract.name)
        supplier_contracts = Contract.query.join(MarketRole).filter(
            MarketRole.code == 'X').order_by(Contract.name)
        pcs = Pc.query.order_by(Pc.code)
        cops = Cop.query.order_by(Cop.code)
        return make_response(
            render_template(
                'site_edit.html', site=site, sources=sources,
                generator_types=generator_types, gsp_groups=gsp_groups,
                eras=eras, mop_contracts=mop_contracts,
                hhdc_contracts=hhdc_contracts,
                supplier_contracts=supplier_contracts, pcs=pcs, cops=cops),
            400)


@app.route('/sites/add', methods=['POST'])
def site_add_post():
    try:
        sess = db.session()
        set_read_write(sess)
        code = req_str("code")
        name = req_str("name")
        site = Site.insert(sess, code, name)
        sess.commit()
        return redirect("/sites/" + str(site.id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template('site_add.html')


@app.route('/sites/add')
def site_add_get():
    return render_template('site_add.html')


@app.route('/sites')
def sites_get():
    LIMIT = 50
    if 'pattern' in request.values:
        pattern = req_str("pattern")
        sites = Site.query.from_statement(
            text(
                "select * from site "
                "where lower(code || ' ' || name) like '%' || lower(:pattern) "
                "|| '%' order by code limit :lim")).params(
            pattern=pattern, lim=LIMIT).all()

        if len(sites) == 1:
            return redirect("/sites/" + str(sites[0].id))
        else:
            return render_template('sites.html', sites=sites, limit=LIMIT)
    else:
        return render_template('sites.html')


@app.route('/hhdc_contracts')
def hhdc_contracts_get():
    hhdc_contracts = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'C').order_by(Contract.name).all()
    return render_template(
        'hhdc_contracts.html', hhdc_contracts=hhdc_contracts)


@app.route('/hhdc_contracts/add', methods=['POST'])
def hhdc_contracts_add_post():
    try:
        sess = db.session()
        set_read_write(sess)
        participant_id = req_int('participant_id')
        name = req_str('name')
        start_date = req_date('start')
        participant = Participant.get_by_id(sess, participant_id)
        contract = Contract.insert_hhdc(
            sess, name, participant, '{}', '{}', start_date, None, '{}')
        sess.commit()
        chellow.hh_importer.startup_contract(contract.id)
        return redirect('/hhdc_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        initial_date = Datetime.utcnow().replace(tzinfo=pytz.utc)
        initial_date = Datetime(initial_date.year, initial_date.month, 1)
        parties = sess.query(Party).join(MarketRole).join(Participant). \
            filter(MarketRole.code == 'C').order_by(Participant.code).all()
        return render_template(
            'hhdc_contracts_add', initial_date=initial_date, parties=parties)


@app.route('/hhdc_contracts/add')
def hhdc_contracts_add_get():
    initial_date = Datetime.utcnow().replace(tzinfo=pytz.utc)
    initial_date = Datetime(initial_date.year, initial_date.month, 1)
    parties = Party.query.join(MarketRole).join(Participant).filter(
        MarketRole.code == 'C').order_by(Participant.code).all()
    return render_template(
        'hhdc_contracts_add.html', initial_date=initial_date, parties=parties)


@app.route('/hhdc_contracts/<int:hhdc_contract_id>')
def hhdc_contract_get(hhdc_contract_id):
    rate_scripts = None
    try:
        sess = db.session()
        contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)
        rate_scripts = RateScript.query.filter(
            RateScript.contract == contract).order_by(
            RateScript.start_date.desc()).all()
        now = Datetime.now(pytz.utc)
        last_month_finish = Datetime(now.year, now.month, 1) - \
            relativedelta(minutes=30)
        return render_template(
            'hhdc_contract.html', hhdc_contract=contract,
            rate_scripts=rate_scripts, last_month_finish=last_month_finish)
    except BadRequest as e:
        desc = e.description
        flash(desc)
        if desc.startswith("There isn't a contract"):
            raise e
        else:
            return render_template(
                'hhdc_contract.html', contract=contract,
                rate_scripts=rate_scripts, last_month_finish=last_month_finish)


@app.route('/parties/<int:party_id>')
def party_get(party_id):
    sess = db.session()
    party = Party.get_by_id(sess, party_id)
    return render_template('party.html', party=party)


@app.route('/parties')
def parties_get():
    return render_template(
        'parties.html',
        parties=Party.query.join(MarketRole).order_by(
            Party.name, MarketRole.code).all())


@app.route('/market_roles/<int:market_role_id>')
def market_role_get(market_role_id):
    sess = db.session()
    market_role = MarketRole.get_by_id(sess, market_role_id)
    return render_template('market_role.html', market_role=market_role)


@app.route('/market_roles')
def market_roles_get():
    market_roles = MarketRole.query.order_by(MarketRole.code).all()
    return render_template('market_roles.html', market_roles=market_roles)


@app.route('/participants/<int:participant_id>')
def participant_get(participant_id):
    sess = db.session()
    participant = Participant.get_by_id(sess, participant_id)
    return render_template('participant.html', participant=participant)


@app.route('/participants')
def participants_get():
    participants = Participant.query.order_by(Participant.code).all()
    return render_template('participants.html', participants=participants)


@app.route('/hhdc_contracts/<int:hhdc_contract_id>/edit')
def hhdc_contract_edit_get(hhdc_contract_id):
    sess = db.session()
    parties = Party.query.join(MarketRole).join(Participant).filter(
        MarketRole.code == 'C').order_by(Participant.code).all()
    hhdc_contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)
    initial_date = Datetime.now(pytz.utc)
    return render_template(
        'hhdc_contract_edit.html', parties=parties, initial_date=initial_date,
        hhdc_contract=hhdc_contract)


@app.route('/hhdc_contracts/<int:contract_id>/edit', methods=['POST'])
def hhdc_contract_edit_post(contract_id):
    sess = None
    contract = None
    try:
        sess = db.session()
        set_read_write(sess)
        contract = Contract.get_hhdc_by_id(sess, contract_id)
        if 'update_state' in request.form:
            state = req_str("state")
            contract.state = state
            sess.commit()
            return redirect('/hhdc_contracts/' + str(contract.id), 303)
        elif 'ignore_snags' in request.form:
            ignore_date = req_date('ignore')
            sess.execute(
                text(
                    "update snag set is_ignored = true from channel, era "
                    "where snag.channel_id = channel.id "
                    "and channel.era_id = era.id "
                    "and era.hhdc_contract_id = :contract_id "
                    "and snag.finish_date < :ignore_date"),
                params=dict(contract_id=contract.id, ignore_date=ignore_date))
            sess.commit()
            return redirect("/hhdc_contracts/" + str(contract.id), 303)
        elif 'delete' in request.form:
            contract.delete(sess)
            sess.commit()
            return redirect('/hhdc_contracts', 303)
        else:
            party_id = req_str('party_id')
            name = req_str("name")
            charge_script = req_str("charge_script")
            properties = req_str("properties")
            party = Party.get_by_id(sess, party_id)
            contract.update(False, name, party, charge_script, properties)
            sess.commit()
            return redirect('/hhdc_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        if contract is None:
            raise e
        else:
            parties = Party.query.join(MarketRole).join(Participant).filter(
                MarketRole.code == 'C').order_by(Participant.code).all()
            initial_date = Datetime.now(pytz.utc)
            return render_template(
                'hhdc_contract_edit.html', parties=parties,
                initial_date=initial_date)


@app.route('/hhdc_rate_scripts/<int:hhdc_rate_script_id>')
def hhdc_rate_script_get(hhdc_rate_script_id):
    sess = db.session()
    hhdc_rate_script = RateScript.get_hhdc_by_id(sess, hhdc_rate_script_id)
    return render_template(
        'hhdc_rate_script.html', hhdc_rate_script=hhdc_rate_script)


@app.route('/hhdc_rate_scripts/<int:hhdc_rate_script_id>/edit')
def hhdc_rate_script_edit_get(hhdc_rate_script_id):
    sess = db.session()
    hhdc_rate_script = RateScript.get_hhdc_by_id(sess, hhdc_rate_script_id)
    return render_template(
        'hhdc_rate_script_edit.html', hhdc_rate_script=hhdc_rate_script)


@app.route(
    '/hhdc_rate_scripts/<int:hhdc_rate_script_id>/edit', methods=['POST'])
def hhdc_rate_script_edit_post(hhdc_rate_script_id):
    try:
        sess = db.session()
        set_read_write(sess)
        hhdc_rate_script = RateScript.get_hhdc_by_id(sess, hhdc_rate_script_id)
        hhdc_contract = hhdc_rate_script.contract
        if 'delete' in request.form:
            hhdc_contract.delete_rate_script(sess, hhdc_rate_script)
            sess.commit()
            return redirect('/hhdc_contracts/' + str(hhdc_contract.id), 303)
        else:
            script = req_str('script')
            start_date = req_date('start')
            has_finished = req_bool('has_finished')
            finish_date = req_date('finish') if has_finished else None
            hhdc_contract.update_rate_script(
                sess, hhdc_rate_script, start_date, finish_date, script)
            sess.commit()
            return redirect(
                'hhdc_rate_scripts/' + str(hhdc_rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template(
            'hhdc_rate_script_edit.html', hhdc_rate_script=hhdc_rate_script)


@app.route('/supplier_contracts/<int:contract_id>/edit')
def supplier_contract_edit_get(contract_id):
    sess = db.session()
    contract = Contract.get_supplier_by_id(sess, contract_id)
    parties = Party.query.join(MarketRole, Participant).filter(
        MarketRole.code == 'X').order_by(Participant.code).all()
    return render_template(
        'supplier_contract_edit.html', contract=contract, parties=parties)


@app.route('/supplier_contracts/<int:contract_id>/edit', methods=['POST'])
def supplier_contract_edit_post(contract_id):
    try:
        sess = db.session()
        set_read_write(sess)
        contract = Contract.get_supplier_by_id(sess, contract_id)
        if 'delete' in request.form:
            contract.delete(sess)
            sess.commit()
            return redirect('/supplier_contracts', 303)
        else:
            party_id = req_int('party_id')
            party = Party.get_by_id(sess, party_id)
            name = req_str('name')
            charge_script = req_str('charge_script')
            properties = req_str('properties')
            contract.update(False, name, party, charge_script, properties)
            sess.commit()
            return redirect('/supplier_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        sess.rollback()
        description = e.description
        flash(description)
        if description.startswith("There isn't a contract"):
            raise
        else:
            parties = Party.query.join(MarketRole, Participant).filter(
                MarketRole.code == 'X').order_by(Participant.code).all()
            return make_response(
                render_template(
                    'supplier_contract_edit.html', contract=contract,
                    parties=parties), 400)


@app.route('/supplier_rate_scripts/<int:rate_script_id>')
def supplier_rate_script_get(rate_script_id):
    sess = db.session()
    rate_script = RateScript.get_supplier_by_id(sess, rate_script_id)
    return render_template(
        'supplier_rate_script.html', rate_script=rate_script)


@app.route('/supplier_rate_scripts/<int:rate_script_id>/edit')
def supplier_rate_script_edit_get(rate_script_id):
    sess = db.session()
    rate_script = RateScript.get_supplier_by_id(sess, rate_script_id)
    return render_template(
        'supplier_rate_script_edit.html', supplier_rate_script=rate_script)


@app.route(
    '/supplier_rate_scripts/<int:rate_script_id>/edit', methods=['POST'])
def supplier_rate_script_edit_post(rate_script_id):
    try:
        sess = db.session()
        set_read_write(sess)
        rate_script = RateScript.get_supplier_by_id(sess, rate_script_id)
        contract = rate_script.contract
        if 'delete' in request.form:
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            return redirect('/supplier_contracts/' + str(contract.id), 303)
        else:
            script = req_str('script')
            start_date = req_date('start')
            has_finished = req_bool('has_finished')
            finish_date = req_date('finish') if has_finished else None
            contract.update_rate_script(
                sess, rate_script, start_date, finish_date, script)
            sess.commit()
            return redirect(
                '/supplier_rate_script/' + str(rate_script.id), 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        rate_script = RateScript.get_supplier_by_id(sess, rate_script_id)
        return make_response(render_template(
            'supplier_rate_script_edit.html',
            supplier_rate_script=rate_script), 400)


@app.route('/supplier_contracts')
def supplier_contracts_get():
    contracts = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'X').order_by(Contract.name)
    return render_template(
        'supplier_contracts.html', supplier_contracts=contracts)


@app.route('/supplier_contracts/add', methods=['POST'])
def supplier_contract_add_post():
    try:
        sess = db.session()
        set_read_write(sess)
        participant_id = req_str("participant_id")
        participant = Participant.get_by_id(sess, participant_id)
        name = req_str("name")
        start_date = req_date("start")
        charge_script = req_str("charge_script")
        properties = req_str("properties")
        contract = Contract.insert_supplier(
            sess, name, participant, charge_script, properties, start_date,
            None, '{}')
        sess.commit()
        return redirect("/supplier_contracts/" + str(contract.id), 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        contracts = sess.query(Contract).join(MarketRole).filter(
            MarketRole.code == 'X').order_by(Contract.name)
        parties = sess.query(Party).join(MarketRole, Participant).filter(
            MarketRole.code == 'X').order_by(Participant.code)
        return make_response(
            render_template(
                'supplier_contract_add.html', contracts=contracts,
                parties=parties), 400)


@app.route('/supplier_contracts/add')
def supplier_contract_add_get():
    contracts = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'X').order_by(Contract.name)
    parties = Party.query.join(MarketRole, Participant).filter(
        MarketRole.code == 'X').order_by(Participant.code)
    return render_template(
        'supplier_contract_add.html', contracts=contracts, parties=parties)


@app.route('/supplier_contracts/<int:contract_id>')
def supplier_contract_get(contract_id):
    sess = db.session()
    contract = Contract.get_supplier_by_id(sess, contract_id)
    rate_scripts = RateScript.query.filter(
        RateScript.contract == contract).order_by(RateScript.start_date).all()

    now = Datetime.utcnow() - relativedelta(months=1)
    month_start = Datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH

    return render_template(
        'supplier_contract.html', contract=contract, month_start=month_start,
        month_finish=month_finish, rate_scripts=rate_scripts)


@app.route('/supplier_contracts/<int:contract_id>/add_rate_script')
def supplier_rate_script_add_get(contract_id):
    now = Datetime.now(pytz.utc)
    initial_date = Datetime(now.year, now.month, 1, tzinfo=pytz.utc)
    sess = db.session()
    contract = Contract.get_supplier_by_id(sess, contract_id)
    return render_template(
        'supplier_rate_script_add.html', now=now, contract=contract,
        initial_date=initial_date)


@app.route(
    '/supplier_contracts/<int:contract_id>/add_rate_script', methods=['POST'])
def supplier_rate_script_add_post(contract_id):
    try:
        sess = db.session()
        set_read_write(sess)
        contract = Contract.get_supplier_by_id(sess, contract_id)
        start_date = req_date('start')
        rate_script = contract.insert_rate_script(sess, start_date, '')
        sess.commit()
        return redirect('/supplier_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = Datetime.now(pytz.utc)
        initial_date = Datetime(now.year, now.month, 1, tzinfo=pytz.utc)
        return render_template(
            'supplier_rate_script_add.html', now=now, contract=contract,
            initial_date=initial_date)


@app.route('/mop_contracts/<int:contract_id>/edit')
def mop_contract_edit_get(contract_id):
    parties = Party.query.join(MarketRole).join(Participant).filter(
        MarketRole.code == 'M').order_by(Participant.code).all()
    initial_date = Datetime.now(pytz.utc)
    sess = db.session()
    contract = Contract.get_mop_by_id(sess, contract_id)
    return render_template(
        'mop_contract_edit.html', contract=contract, parties=parties,
        initial_date=initial_date)


@app.route('/mop_contracts/<int:contract_id>/edit', methods=['POST'])
def mop_contract_edit_post(contract_id):
    try:
        sess = db.session()
        set_read_write(sess)
        contract = Contract.get_mop_by_id(sess, contract_id)
        if 'update_state' in request.form:
            state = req_str('state')
            contract.state = state
            sess.commit()
            return redirect("/mop_contracts/" + str(contract.id), 303)
        elif 'ignore_snags' in request.form:
            ignore_date = req_date('ignore')
            sess.execute(
                text(
                    "update snag set is_ignored = true from channel, era "
                    "where snag.channel_id = channel.id "
                    "and channel.era_id = era.id "
                    "and era.hhdc_contract_id = :contract_id "
                    "and snag.finish_date < :ignore_date"),
                params=dict(contract_id=contract.id, ignore_date=ignore_date))
            sess.commit()
            return redirect('/mop_contracts/' + str(contract.id), 303)
        elif 'delete' in request.form:
            contract.delete(sess)
            sess.commit()
            return redirect('/mop_contracts', 303)
        else:
            party_id = req_int("party_id")
            name = req_str("name")
            charge_script = req_str("charge_script")
            properties = req_str("properties")
            party = Party.get_by_id(sess, party_id)
            contract.update(False, name, party, charge_script, properties)
            sess.commit()
            return redirect('/mop_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        parties = Party.query.join(MarketRole).join(Participant).filter(
            MarketRole.code == 'M').order_by(Participant.code).all()
        initial_date = Datetime.now(pytz.utc)
        contract = Contract.get_mop_by_id(sess, contract_id)
        return make_response(
            render_template(
                'mop_contract_edit.html', contract=contract, parties=parties,
                initial_date=initial_date), 400)


@app.route('/mop_rate_scripts/<int:rate_script_id>')
def mop_rate_script_get(rate_script_id):
    sess = db.session()
    rate_script = RateScript.get_mop_by_id(sess, rate_script_id)
    return render_template('mop_rate_script.html', rate_script=rate_script)


@app.route('/mop_rate_scripts/<int:rate_script_id>/edit')
def mop_rate_script_edit_get(rate_script_id):
    sess = db.session()
    rate_script = RateScript.get_mop_by_id(sess, rate_script_id)
    return render_template(
        'mop_rate_script_edit.html', rate_script=rate_script)


@app.route('/mop_rate_scripts/<int:rate_script_id>/edit', methods=['POST'])
def mop_rate_script_edit_post(rate_script_id):
    sess = db.session()
    set_read_write(sess)
    rate_script = RateScript.get_mop_by_id(sess, rate_script_id)
    contract = rate_script.contract
    if 'delete' in request.form:
        contract.delete_rate_script(sess, rate_script)
        sess.commit()
        return redirect('mop_contracts/' + str(contract.id), 303)
    else:
        try:
            script = req_str('script')
            start_date = req_date('start')
            if 'has_finished' in request.form:
                finish_date = req_date('finish')
            else:
                finish_date = None
            contract.update_rate_script(
                sess, rate_script, start_date, finish_date, script)
            sess.commit()
            return redirect('/mop_rate_scripts/' + str(rate_script.id), 303)
        except BadRequest as e:
            flash(e.description)
            return make_response(
                render_template(
                    'mop_rate_script_edit.html', rate_script=rate_script), 400)


@app.route('/mop_contracts')
def mop_contracts_get():
    mop_contracts = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'M').order_by(Contract.name).all()
    return render_template('mop_contracts.html', mop_contracts=mop_contracts)


@app.route('/mop_contracts/add', methods=['POST'])
def mop_contract_add_post():
    try:
        sess = db.session()
        set_read_write(sess)
        participant_id = req_int('participant_id')
        name = req_str('name')
        start_date = req_date('start')
        participant = Participant.get_by_id(sess, participant_id)
        contract = Contract.insert_mop(
            sess, name, participant, '{}', '{}', start_date, None, '{}')
        sess.commit()
        return redirect('/mop_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        initial_date = Datetime.utcnow().replace(tzinfo=pytz.utc)
        initial_date = Datetime(initial_date.year, initial_date.month, 1)
        parties = Party.query.join(MarketRole).join(Participant).filter(
            MarketRole.code == 'C').order_by(Participant.code).all()
        return make_response(
            render_template(
                'mop_contract_add.html', inital_date=initial_date,
                parties=parties), 400)


@app.route('/mop_contracts/add')
def mop_contract_add_get():
    initial_date = Datetime.utcnow().replace(tzinfo=pytz.utc)
    initial_date = Datetime(initial_date.year, initial_date.month, 1)
    parties = Party.query.join(MarketRole).join(Participant).filter(
        MarketRole.code == 'C').order_by(Participant.code).all()
    return render_template(
        'mop_contract_add.html', inital_date=initial_date, parties=parties)


@app.route('/mop_contracts/<int:contract_id>')
def mop_contract_get(contract_id):
    sess = db.session()
    contract = Contract.get_mop_by_id(sess, contract_id)
    rate_scripts = RateScript.query.filter(
        RateScript.contract == contract).order_by(
        RateScript.start_date.desc()).all()
    now = Datetime.utcnow().replace(tzinfo=pytz.utc)
    last_month_start = Datetime(
        now.year, now.month, 1, tzinfo=pytz.utc) - relativedelta(months=1)
    last_month_finish = last_month_start + relativedelta(months=1) - HH
    party = contract.party
    return render_template(
        'mop_contract.html', contract=contract, rate_scripts=rate_scripts,
        last_month_start=last_month_start, last_month_finish=last_month_finish,
        party=party)


@app.route('/mop_rate_scripts/add')
def mop_rate_script_add_get():
    sess = db.session()
    contract_id = req_str('mop_contract_id')
    contract = Contract.get_mop_by_id(sess, contract_id)
    now = Datetime.now(pytz.utc)
    initial_date = Datetime(now.year, now.month, 1, tzinfo=pytz.utc)
    return render_template(
        'mop_rate_script_add.html', contract=contract,
        initial_date=initial_date)


@app.route('/mop_rate_scripts/add', methods=['POST'])
def mop_rate_script_add_post():
    try:
        sess = db.session()
        set_read_write(sess)
        contract_id = req_str('mop_contract_id')
        contract = Contract.get_mop_by_id(sess, contract_id)
        start_date = req_date('start')
        rate_script = contract.insert_rate_script(sess, start_date, '')
        sess.commit()
        return redirect('/mop_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = Datetime.now(pytz.utc)
        initial_date = Datetime(now.year, now.month, 1, tzinfo=pytz.utc)
        return make_response(
            render_template(
                'mop_rate_script_add.html', contract=contract,
                initial_date=initial_date), 400)


@app.route('/supplies/<int:supply_id>/months')
def supply_months_get(supply_id):
    sess = db.session()
    supply = Supply.get_by_id(sess, supply_id)

    is_import = req_bool("is_import")
    year = req_int('year')
    years = req_int('years')

    month_start = Datetime(year - years + 1, 1, 1, tzinfo=pytz.utc)
    months = []
    for i in range(12 * years):
        next_month_start = month_start + relativedelta(months=1)
        month_finish = next_month_start - HH

        month_data = {}
        months.append(month_data)

        era = supply.find_era_at(sess, month_finish)
        if era is not None:
            mpan_core = era.imp_mpan_core if is_import else era.exp_mpan_core
            if mpan_core is not None:
                month_data['mpan_core'] = mpan_core
                month_data['sc'] = era.imp_sc if is_import else era.exp_sc

        md_kvah = 0
        for kwh, kvarh, hh_date in sess.execute(
                "select cast(max(hh_ac.value) as double precision), "
                "cast(max(hh_re.value) as double precision), "
                "hh_ac.start_date "
                "from hh_datum as hh_ac join channel as channel_ac "
                "on (hh_ac.channel_id = channel_ac.id) "
                "join era as era_ac on (channel_ac.era_id = era_ac.id) "
                "join hh_datum as hh_re "
                "on (hh_ac.start_date = hh_re.start_date) "
                "join channel as channel_re "
                "on (hh_re.channel_id = channel_re.id) "
                "join era as era_re on (channel_re.era_id = era_re.id) "
                "where era_ac.supply_id = :supply_id "
                "and era_re.supply_id = :supply_id "
                "and channel_ac.imp_related = :is_import "
                "and channel_re.imp_related = :is_import "
                "and channel_ac.channel_type = 'ACTIVE' "
                "and channel_re.channel_type "
                "in ('REACTIVE_IMP', 'REACTIVE_EXP') "
                "and hh_ac.start_date >= :month_start "
                "and hh_ac.start_date <= :month_finish "
                "and hh_re.start_date >= :month_start "
                "and hh_re.start_date <= :month_finish "
                "group by hh_ac.start_date",
                params={
                    'month_start': month_start, 'month_finish': month_finish,
                    'is_import': is_import, 'supply_id': supply.id}):
            kvah = (kwh ** 2 + kvarh ** 2) ** 0.5
            if kvah > md_kvah:
                md_kvah = kvah
                month_data['md_kva'] = 2 * md_kvah
                month_data['md_kvar'] = kvarh * 2
                month_data['md_kw'] = kwh * 2
                month_data['md_pf'] = float(kwh) / kvah
                month_data['md_date'] = hh_date

        total_kwh = sess.query(func.sum(HhDatum.value)).join(Channel) \
            .join(Era).filter(
                Era.supply == supply, Channel.channel_type == 'ACTIVE',
                Channel.imp_related == is_import,
                HhDatum.start_date >= month_start,
                HhDatum.start_date <= month_finish).one()[0]

        if total_kwh is not None:
            month_data['total_kwh'] = float(total_kwh)

        month_data['start_date'] = month_start
        month_start = next_month_start

    return render_template(
        'supply_months.html', supply=supply, months=months,
        is_import=is_import, now=Datetime.now(pytz.utc))


@app.route('/supplies/<int:supply_id>/edit')
def supply_edit_get(supply_id):
    sess = db.session()
    supply = Supply.get_by_id(sess, supply_id)
    sources = Source.query.order_by(Source.code)
    generator_types = GeneratorType.query.order_by(GeneratorType.code)
    gsp_groups = GspGroup.query.order_by(GspGroup.code)
    eras = Era.query.filter(
        Era.supply == supply).order_by(Era.start_date.desc())
    return render_template(
        'supply_edit.html', supply=supply, sources=sources,
        generator_types=generator_types, gsp_groups=gsp_groups, eras=eras)


@app.route('/supplies/<int:supply_id>/edit', methods=['POST'])
def supply_edit_post(supply_id):
    try:
        sess = db.session()
        set_read_write(sess)
        supply = Supply.get_by_id(sess, supply_id)

        if 'delete' in request.form:
            supply.delete(sess)
            sess.commit()
            return redirect("/supplies", 303)
        elif 'insert_era' in request.form:
            start_date = req_date('start')
            supply.insert_era_at(sess, start_date)
            sess.commit()
            return redirect("/supplies/" + str(supply.id), 303)
        else:
            name = req_str("name")
            source_id = req_int("source_id")
            gsp_group_id = req_int("gsp_group_id")
            source = Source.get_by_id(sess, source_id)
            if source.code in ('gen', 'gen-net'):
                generator_type_id = req_int("generator_type_id")
                generator_type = GeneratorType.get_by_id(
                    sess, generator_type_id)
            else:
                generator_type = None
            gsp_group = GspGroup.get_by_id(sess, gsp_group_id)
            supply.update(
                name, source, generator_type, gsp_group, supply.dno_contract)
            sess.commit()
            return redirect("/supplies/" + str(supply.id), 303)
    except BadRequest as e:
        flash(e.description)
        sources = Source.query.order_by(Source.code)
        generator_types = GeneratorType.query.order_by(GeneratorType.code)
        gsp_groups = GspGroup.query.order_by(GspGroup.code)
        eras = Era.query.filter(
            Era.supply == supply).order_by(Era.start_date.desc())
        return make_response(
            render_template(
                'supply_edit.html', supply=supply, sources=sources,
                generator_types=generator_types, gsp_groups=gsp_groups,
                eras=eras), 400)


@app.route('/eras/<int:era_id>/edit')
def era_edit_get(era_id):
    sess = db.session()
    era = Era.get_by_id(sess, era_id)
    pcs = Pc.query.order_by(Pc.code)
    cops = Cop.query.order_by(Cop.code)
    gsp_groups = GspGroup.query.order_by(GspGroup.code)
    mop_contracts = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'M').order_by(Contract.name)
    hhdc_contracts = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'C').order_by(Contract.name)
    supplier_contracts = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'X').order_by(Contract.name)
    site_eras = SiteEra.query.join(Site).filter(
        SiteEra.era == era).order_by(Site.code).all()
    return render_template(
        'era_edit.html', era=era, pcs=pcs, cops=cops, gsp_groups=gsp_groups,
        mop_contracts=mop_contracts, hhdc_contracts=hhdc_contracts,
        supplier_contracts=supplier_contracts, site_eras=site_eras)


@app.route('/eras/<int:era_id>/edit', methods=['POST'])
def era_edit_post(era_id):
    try:
        sess = db.session()
        set_read_write(sess)
        era = Era.get_by_id(sess, era_id)

        if 'delete' in request.form:
            supply = era.supply
            supply.delete_era(sess, era)
            sess.commit()
            return redirect("/supplies/" + str(supply.id), 303)
        elif 'attach' in request.form:
            site_code = req_str("site_code")
            site = Site.get_by_code(sess, site_code)
            era.attach_site(sess, site)
            sess.commit()
            return redirect("/supplies/" + str(era.supply.id), 303)
        elif 'detach' in request.form:
            site_id = req_int("site_id")
            site = Site.get_by_id(sess, site_id)
            era.detach_site(sess, site)
            sess.commit()
            return redirect("/supplies/" + str(era.supply.id), 303)
        elif 'locate' in request.form:
            site_id = req_int("site_id")
            site = Site.get_by_id(sess, site_id)
            era.set_physical_location(sess, site)
            sess.commit()
            return redirect("/supplies/" + str(era.supply.id), 303)
        else:
            start_date = req_date('start')
            is_ended = req_bool("is_ended")
            if is_ended:
                finish_date = req_hh_date("finish")
            else:
                finish_date = None
            mop_contract_id = req_int("mop_contract_id")
            mop_contract = Contract.get_mop_by_id(sess, mop_contract_id)
            mop_account = req_str("mop_account")
            hhdc_contract_id = req_int("hhdc_contract_id")
            hhdc_contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)
            hhdc_account = req_str("hhdc_account")
            msn = req_str("msn")
            pc_id = req_int("pc_id")
            pc = Pc.get_by_id(sess, pc_id)
            mtc_code = req_str("mtc_code")
            mtc = Mtc.get_by_code(
                sess, era.supply.dno_contract.party, mtc_code)
            cop_id = req_int("cop_id")
            cop = Cop.get_by_id(sess, cop_id)
            ssc_code = req_str("ssc_code")
            ssc_code = ssc_code.strip()
            if len(ssc_code) == 0:
                ssc = None
            else:
                ssc = Ssc.get_by_code(sess, ssc_code)

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
                    sess, imp_supplier_contract_id)
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
                    sess, exp_supplier_contract_id)
                exp_supplier_account = req_str('exp_supplier_account')

            era.supply.update_era(
                sess, era, start_date, finish_date, mop_contract, mop_account,
                hhdc_contract, hhdc_account, msn, pc, mtc, cop, ssc,
                imp_mpan_core, imp_llfc_code, imp_supplier_contract,
                imp_supplier_account, imp_sc, exp_mpan_core, exp_llfc_code,
                exp_supplier_contract, exp_supplier_account, exp_sc)
            sess.commit()
            return redirect("/supplies/" + str(era.supply.id), 303)
    except BadRequest as e:
        flash(e.description)
        pcs = Pc.query.order_by(Pc.code)
        cops = Cop.query.order_by(Cop.code)
        gsp_groups = GspGroup.query.order_by(GspGroup.code)
        mop_contracts = Contract.query.join(MarketRole).filter(
            MarketRole.code == 'M').order_by(Contract.name)
        hhdc_contracts = Contract.query.join(MarketRole).filter(
            MarketRole.code == 'C').order_by(Contract.name)
        supplier_contracts = Contract.query.join(MarketRole).filter(
            MarketRole.code == 'X').order_by(Contract.name)
        site_eras = SiteEra.query.join(Site).filter(
            SiteEra.era == era).order_by(Site.code).all()
        return make_response(
            render_template(
                'era_edit.html', era=era, pcs=pcs, cops=cops,
                gsp_groups=gsp_groups, mop_contracts=mop_contracts,
                hhdc_contracts=hhdc_contracts,
                supplier_contracts=supplier_contracts, site_eras=site_eras),
            400)


@app.route('/supplies')
def supplies_get():
    if 'search_pattern' in request.args:
        pattern = req_str('search_pattern')
        pattern = pattern.strip()
        reduced_pattern = pattern.replace(" ", "")
        if 'max_results' in request.args:
            max_results = req_int('max_results')
        else:
            max_results = 50
        eras = Era.query.from_statement(
            text(
                "select e1.* from era as e1 "
                "inner join (select e2.supply_id, max(e2.start_date) "
                "as max_start_date from era as e2 "
                "where replace(lower(e2.imp_mpan_core), ' ', '') "
                "like lower(:reducedPattern) "
                "or lower(e2.imp_supplier_account) like lower(:pattern) "
                "or replace(lower(e2.exp_mpan_core), ' ', '') "
                "like lower(:reducedPattern) "
                "or lower(e2.exp_supplier_account) like lower(:pattern) "
                "or lower(e2.hhdc_account) like lower(:pattern) "
                "or lower(e2.mop_account) like lower(:pattern) "
                "or lower(e2.msn) like lower(:pattern) "
                "group by e2.supply_id) as sq "
                "on e1.supply_id = sq.supply_id "
                "and e1.start_date = sq.max_start_date limit :max_results")
            ).params(
            pattern="%" + pattern + "%",
            reducedPattern="%" + reduced_pattern + "%",
            max_results=max_results).all()
        if len(eras) == 1:
            return redirect("/supplies/" + str(eras[0].supply.id), 307)
        else:
            return render_template(
                'supplies.html', eras=eras, max_results=max_results)
    else:
        return render_template('supplies.html')


@app.route('/supplies/<int:supply_id>')
def supply_get(supply_id):
    debug = ''
    sess = db.session()
    era_bundles = []
    supply = Supply.get_by_id(sess, supply_id)
    eras = Era.query.filter(Era.supply == supply).order_by(
        Era.start_date.desc()).all()
    for era in eras:
        imp_mpan_core = era.imp_mpan_core
        exp_mpan_core = era.exp_mpan_core
        physical_site = Site.query.join(SiteEra).filter(
            SiteEra.is_physical == true(), SiteEra.era == era).one()
        other_sites = Site.query.join(SiteEra).filter(
            SiteEra.is_physical != true(), SiteEra.era == era).all()
        imp_channels = Channel.query.filter(
            Channel.era == era, Channel.imp_related == true()).order_by(
            Channel.channel_type).all()
        exp_channels = Channel.query.filter(
            Channel.era == era, Channel.imp_related == false()).order_by(
            Channel.channel_type).all()
        era_bundle = {
            'era': era, 'physical_site': physical_site,
            'other_sites': other_sites, 'imp_channels': imp_channels,
            'exp_channels': exp_channels, 'imp_bills': {'bill_dicts': []},
            'exp_bills': {'bill_dicts': []},
            'hhdc_bills': {'bill_dicts': []}, 'mop_bills': {'bill_dicts': []}}
        era_bundles.append(era_bundle)

        if imp_mpan_core is not None:
            era_bundle['imp_shared_supplier_accounts'] = \
                Supply.query.distinct().join(Era).filter(
                    Supply.id != supply.id,
                    Era.imp_supplier_account == era.imp_supplier_account,
                    Era.imp_supplier_contract == era.imp_supplier_contract) \
                .all()
        if exp_mpan_core is not None:
            era_bundle['exp_shared_supplier_accounts'] = \
                sess.query(Supply).join(Era).filter(
                    Era.supply != supply,
                    Era.exp_supplier_account == era.exp_supplier_account,
                    Era.exp_supplier_contract == era.exp_supplier_contract) \
                .all()
        if era.pc.code != '00':
            inner_headers = [
                tpr for tpr in Tpr.query.join(MeasurementRequirement)
                .filter(
                    MeasurementRequirement.ssc == era.ssc).order_by(Tpr.code)]
            if era.pc.code in ['05', '06', '07', '08']:
                inner_headers.append(None)
            era_bundle['imp_bills']['inner_headers'] = inner_headers
            inner_header_codes = [
                tpr.code if tpr is not None else 'md' for tpr in inner_headers]

        bills = Bill.query.filter(Bill.supply == supply).order_by(
            Bill.start_date.desc(), Bill.issue_date.desc(),
            Bill.reference.desc())
        if era.finish_date is not None:
            bills = bills.filter(Bill.start_date <= era.finish_date)
        if era != eras[-1]:
            bills = bills.filter(Bill.start_date >= era.start_date)

        num_outer_cols = 0
        for bill in bills:
            bill_contract = bill.batch.contract
            bill_role_code = bill_contract.party.market_role.code
            if bill_role_code == 'X':
                if exp_mpan_core is not None and \
                        bill_contract == era.exp_supplier_contract:
                    bill_group_name = 'exp_bills'
                else:
                    bill_group_name = 'imp_bills'

            elif bill_role_code == 'C':
                bill_group_name = 'hhdc_bills'
            elif bill_role_code == 'M':
                bill_group_name = 'mop_bills'
            else:
                raise BadRequest(
                    "bill group name not found for bill_contract_id " +
                    str(bill_contract.id))

            bill_group = era_bundle[bill_group_name]
            rows_high = 1
            bill_dict = {'bill': bill}
            bill_group['bill_dicts'].append(bill_dict)

            if bill_group_name == 'imp_bills' and era.pc.code != '00':
                inner_tpr_map = dict((code, []) for code in inner_header_codes)
                outer_tpr_map = defaultdict(list)

                for read, tpr in sess.query(
                        RegisterRead, Tpr).join(Tpr).filter(
                        RegisterRead.bill == bill).order_by(
                        Tpr.id, RegisterRead.present_date.desc()):
                    tpr_code = 'md' if tpr is None else tpr.code
                    try:
                        inner_tpr_map[tpr_code].append(read)
                    except KeyError:
                        outer_tpr_map[tpr_code].append(read)

                rows_high = max(
                    chain(
                        map(
                            len, chain(
                                inner_tpr_map.values(),
                                outer_tpr_map.values())),
                        [rows_high]))

                read_rows = []
                bill_dict['read_rows'] = read_rows

                for i in range(rows_high):
                    inner_reads = []
                    row_dict = {'inner_reads': inner_reads, 'outer_reads': []}
                    read_rows.append(row_dict)
                    for tpr_code in inner_header_codes:
                        try:
                            inner_reads.append(inner_tpr_map[tpr_code][i])
                        except IndexError:
                            row_dict['inner_reads'].append(None)

                    for tpr_code, read_list in outer_tpr_map.items():
                        try:
                            row_dict['outer_reads'].append(read_list[i])
                        except IndexError:
                            row_dict['outer_reads'].append(None)

                num_outer_cols = max(num_outer_cols, len(outer_tpr_map))

                bill_dict['rows_high'] = rows_high

        era_bundle['imp_bills']['num_outer_cols'] = num_outer_cols
        era_bundle['exp_bills']['num_outer_cols'] = 0

        for bill_group_name in (
                'imp_bills', 'exp_bills', 'hhdc_bills', 'mop_bills'):
            b_dicts = list(reversed(era_bundle[bill_group_name]['bill_dicts']))
            for i, b_dict in enumerate(b_dicts):
                if i < (len(b_dicts) - 1):
                    bill = b_dict['bill']
                    next_b_dict = b_dicts[i+1]
                    next_bill = next_b_dict['bill']
                    if (
                            bill.start_date, bill.finish_date, bill.kwh,
                            bill.net) == (
                            next_bill.start_date, next_bill.finish_date,
                            -1 * next_bill.kwh, -1 * next_bill.net) and \
                            'collapsible' not in b_dict:
                        b_dict['collapsible'] = True
                        next_b_dict['first_collapsible'] = True
                        next_b_dict['collapsible'] = True
                        b_dict['collapse_id'] = next_b_dict['collapse_id'] = \
                            bill.id

    RELATIVE_YEAR = relativedelta(years=1)

    now = Datetime.utcnow()
    triad_year = (now - RELATIVE_YEAR).year if now.month < 3 else now.year
    this_month_start = Datetime(now.year, now.month, 1)
    last_month_start = this_month_start - relativedelta(months=1)
    last_month_finish = this_month_start - relativedelta(minutes=30)

    batch_reports = []
    config_contract = Contract.get_non_core_by_name(sess, 'configuration')
    properties = config_contract.make_properties()
    if 'supply_reports' in properties:
        for report_id in properties['supply_reports']:
            batch_reports.append(Report.get_by_id(sess, report_id))

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


@app.route('/channels/<int:channel_id>')
def channel_get(channel_id):
    sess = db.session()
    channel = Channel.get_by_id(sess, channel_id)
    if 'start_year' in request.values:
        start_year = req_int('start_year')
        start_month = req_int('start_month')
        try:
            start_date = Datetime(start_year, start_month, 1, tzinfo=pytz.utc)
        except ValueError as e:
            raise BadRequest("Invalid date: " + str(e))
    else:
        era_finish = channel.era.finish_date
        if era_finish is None:
            start_date = Datetime.utcnow().replace(tzinfo=pytz.utc)
        else:
            start_date = Datetime(
                era_finish.year, era_finish.month, 1, tzinfo=pytz.utc)

    if start_date is not None:
        finish_date = start_date + relativedelta(months=1) - HH
        era = channel.era
        if hh_after(finish_date, era.finish_date):
            flash("The finish date is after the end of the era.")
        if start_date < era.start_date:
            flash("The start date is before the start of the era.")
        hh_data = HhDatum.query.filter(
            HhDatum.channel == channel, HhDatum.start_date >= start_date,
            HhDatum.start_date <= finish_date).order_by(HhDatum.start_date)
        snags = Snag.query.filter(Snag.channel == channel).order_by(
            Snag.start_date)
    else:
        hh_data = snags = None

    return render_template(
        'channel.html', channel=channel, start_date=start_date,
        hh_data=hh_data, snags=snags)


@app.route('/hhdc_contracts/<int:contract_id>/hh_imports')
def hhdc_contracts_hh_imports_get(contract_id):
    sess = db.session()
    contract = Contract.get_hhdc_by_id(sess, contract_id)
    processes = chellow.hh_importer.get_hh_import_processes(contract.id)
    return render_template(
        'hhdc_contract_hh_imports.html', contract=contract,
        processes=processes)


@app.route('/hhdc_contracts/<int:contract_id>/hh_imports', methods=['POST'])
def hhdc_contracts_hh_imports_post(contract_id):
    try:
        sess = db.session()
        contract = Contract.get_hhdc_by_id(sess, contract_id)

        file_item = request.files["import_file"]
        f = io.StringIO(str(file_item.stream.read(), 'utf-8'))
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        f.seek(0)
        hh_import_process = chellow.hh_importer.start_hh_import_process(
            contract_id, f, file_item.filename, file_size)
        return redirect(
            "/hhdc_contracts/" + str(contract.id) + "/hh_imports/" +
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
                    'hhdc_contract_hh_imports.html', contract=contract,
                    processes=processes), 400)


@app.route('/hhdc_contracts/<int:contract_id>/hh_imports/<int:import_id>')
def hhdc_contracts_hh_import_get(contract_id, import_id):
    sess = db.session()
    contract = Contract.get_hhdc_by_id(sess, contract_id)
    process = chellow.hh_importer.get_hh_import_processes(
        contract_id)[import_id]
    return render_template(
        'hhdc_contract_hh_import.html', contract=contract, process=process)


@app.route('/site_snags')
def site_snags_get():
    snags = Snag.query.filter(
        Snag.is_ignored == false(), Snag.site_id != null()).order_by(
        Snag.start_date.desc(), Snag.id).all()
    site_count = Snag.query.join(Site).filter(
        Snag.is_ignored == false()).distinct(Site.id).count()
    return render_template(
        'site_snags.html', snags=snags, site_count=site_count)


@app.route('/site_snags/edit')
def site_snags_edit_get():
    return render_template('site_snags_edit.html')


@app.route('/site_snags/edit', methods=['POST'])
def site_snags_edit_post():
    try:
        sess = db.session()
        set_read_write(sess)
        finish_date = req_date('ignore')
        sess.execute(
            "update snag set is_ignored = true "
            "where snag.site_id is not null and "
            "snag.finish_date < :finish_date", {'finish_date': finish_date})
        sess.commit()
        return redirect('/site_snags', 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(render_template('site_snags_edit.html'), 400)


@app.route('/channel_snags/<int:snag_id>')
def channel_snag_get(snag_id):
    sess = db.session()
    snag = Snag.get_by_id(sess, snag_id)
    return render_template('channel_snag.html', snag=snag)


@app.route('/channels/<int:channel_id>/edit')
def channel_edit_get(channel_id):
    sess = db.session()
    channel = Channel.get_by_id(sess, channel_id)
    now = Datetime.utcnow().replace(tzinfo=pytz.utc)
    return render_template('channel_edit.html', channel=channel, now=now)


@app.route('/channels/<int:channel_id>/edit', methods=['DELETE'])
def channel_edit_delete(channel_id):
    try:
        sess = db.session()
        set_read_write(sess)
        channel = Channel.get_by_id(sess, channel_id)
        supply_id = channel.era.supply.id
        channel.era.delete_channel(
            sess, channel.imp_related, channel.channel_type)
        sess.commit()
        return redirect('/supplies/' + str(supply_id), 303)
    except BadRequest as e:
        flash(e.description)
        now = Datetime.utcnow().replace(tzinfo=pytz.utc)
        return render_template('channel_edit.html', channel=channel, now=now)


@app.route('/channels/<int:channel_id>/edit', methods=['POST'])
def channel_edit_post(channel_id):
    try:
        sess = db.session()
        set_read_write(sess)
        channel = Channel.get_by_id(sess, channel_id)
        if 'delete' in request.values:
            supply_id = channel.era.supply.id
            channel.era.delete_channel(
                sess, channel.imp_related, channel.channel_type)
            sess.commit()
            return redirect('/supplies/' + str(supply_id), 303)
        elif 'delete_data' in request.values:
            start_date = req_hh_date('start')
            finish_date = req_hh_date('finish')
            channel.delete_data(sess, start_date, finish_date)
            sess.commit()
            flash("Data successfully deleted.")
            return redirect('/channels/' + str(channel_id) + '/edit', 303)
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
            hh_datum = HhDatum.query.filter(
                HhDatum.channel == channel,
                HhDatum.start_date == start_date).first()
            if hh_datum is not None:
                raise BadRequest(
                    "There's already a datum in this channel at this time.")
            mpan_core = channel.era.imp_mpan_core
            if mpan_core is None:
                mpan_core = channel.era.exp_mpan_core
            HhDatum.insert(
                sess, [
                    {
                        'start_date': start_date, 'value': value,
                        'status': status, 'mpan_core': mpan_core,
                        'channel_type': channel.channel_type}])
            sess.commit()
            now = Datetime.utcnow().replace(tzinfo=pytz.utc)
            return redirect(
                '/channels/' + str(channel_id) + "/start_year=" +
                str(now.year) + "&start_month=" + str(now.month), 303)
    except BadRequest as e:
        flash(e.description)
        now = Datetime.utcnow().replace(tzinfo=pytz.utc)
        return render_template('channel_edit.html', channel=channel, now=now)


@app.route('/eras/<int:era_id>/add_channel')
def add_channel_get(era_id):
    sess = db.session()
    era = Era.get_by_id(sess, era_id)
    channels = Channel.query.filter(
        Channel.era == era).order_by(Channel.imp_related, Channel.channel_type)
    return render_template('channel_add.html', era=era, channels=channels)


@app.route('/eras/<int:era_id>/add_channel', methods=['POST'])
def add_channel_post(era_id):
    try:
        sess = db.session()
        set_read_write(sess)
        imp_related = req_bool('imp_related')
        channel_type = req_str('channel_type')
        era = Era.get_by_id(sess, era_id)
        channel = era.insert_channel(sess, imp_related, channel_type)
        sess.commit()
        return redirect('/channels/' + str(channel.id), 303)
    except BadRequest as e:
        flash(e.description)
        channels = Channel.query.filter(
            Channel.era == era).order_by(
                Channel.imp_related, Channel.channel_type)
        return render_template('channel_add.html', era=era, channels=channels)


@app.route('/site_snags/<int:snag_id>')
def site_snag_post(snag_id):
    sess = db.session()
    snag = Snag.get_by_id(sess, snag_id)
    return render_template('site_snag.html', snag=snag)


@app.route('/reports/<int:report_id>')
def report_get(report_id):
    report_module = importlib.import_module(
        "chellow.reports.report_" + str(report_id))
    return report_module.do_get(db.session())


@app.route('/reports/<int:report_id>', methods=['POST'])
def report_post(report_id):
    report_module = importlib.import_module(
        "chellow.reports.report_" + str(report_id))
    return report_module.do_post(db.session())


@app.route('/supplier_contracts/<int:contract_id>/add_batch')
def supplier_batch_add_get(contract_id):
    sess = db.session()
    contract = Contract.get_supplier_by_id(sess, contract_id)
    batches = Batch.query.filter(
        Batch.contract == contract).order_by(Batch.reference.desc())
    return render_template(
        'supplier_batch_add.html', contract=contract, batches=batches)


@app.route('/supplier_contracts/<int:contract_id>/add_batch', methods=['POST'])
def supplier_batch_add_post(contract_id):
    sess = db.session()
    set_read_write(sess)
    contract = Contract.get_supplier_by_id(sess, contract_id)
    try:
        reference = req_str("reference")
        description = req_str("description")

        batch = contract.insert_batch(sess, reference, description)
        sess.commit()
        return redirect("/supplier_batches/" + str(batch.id), 303)

    except BadRequest as e:
        flash(e.description)
        sess.rollback()
        batches = Batch.query.filter(
            Batch.contract == contract).order_by(Batch.reference.desc())
        return make_response(
            render_template(
                'supplier_batch_add.html', contract=contract, batches=batches),
            400)


@app.route('/supplier_bill_imports')
def supplier_bill_imports_get():
    sess = db.session()
    batch_id = req_int('supplier_batch_id')
    batch = Batch.get_by_id(sess, batch_id)
    importer_ids = sorted(
        chellow.bill_importer.get_bill_import_ids(batch.id), reverse=True)
    return render_template(
        'supplier_bill_imports.html', batch=batch, importer_ids=importer_ids,
        parser_names=chellow.bill_importer.find_parser_names())


@app.route('/supplier_bill_imports', methods=['POST'])
def supplier_bill_imports_post():
    try:
        sess = db.session()
        batch_id = req_int('supplier_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        file_item = request.files["import_file"]
        f = io.StringIO(str(file_item.stream.read(), 'utf-8'))
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        f.seek(0)
        import_id = chellow.bill_importer.start_bill_import(
            sess, batch.id, file_item.filename, file_size, f)
        return redirect("/supplier_bill_imports/" + str(import_id), 303)
    except BadRequest as e:
        flash(e.description)
        importer_ids = sorted(
            chellow.bill_importer.get_bill_import_ids(batch.id), reverse=True)
        return make_response(
            render_template(
                'supplier_bill_imports.html', batch=batch,
                importer_ids=importer_ids,
                parser_names=chellow.bill_importer.find_parser_names()), 400)


@app.route('/supplier_bill_imports/<int:import_id>')
def supplier_bill_import_get(import_id):
    sess = db.session()
    importer = chellow.bill_importer.get_bill_import(import_id)
    batch = Batch.get_by_id(sess, importer.batch_id)
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


@app.route('/supplier_batches')
def supplier_batches_get():
    sess = db.session()
    contract_id = req_int('supplier_contract_id')
    contract = Contract.get_supplier_by_id(sess, contract_id)
    batches = Batch.query.filter(Batch.contract == contract) \
        .order_by(Batch.reference.desc())
    return render_template(
        'supplier_batches.html', contract=contract, batches=batches)


@app.route('/supplier_batches/<int:batch_id>')
def supplier_batch_get(batch_id):
    sess = db.session()
    batch = Batch.get_by_id(sess, batch_id)
    bills = Bill.query.filter(Bill.batch == batch).order_by(
        Bill.reference, Bill.start_date).all()
    config_contract = Contract.get_non_core_by_name(sess, 'configuration')
    properties = config_contract.make_properties()
    fields = {'batch': batch, 'bills': bills}
    if 'batch_reports' in properties:
        batch_reports = []
        for report_id in properties['batch_reports']:
            batch_reports.append(Report.get_by_id(sess, report_id))
        fields['batch_reports'] = batch_reports
    return render_template('supplier_batch.html', **fields)


@app.route('/hh_data/<int:datum_id>/edit')
def hh_datum_edit_get(datum_id):
    sess = db.session()
    hh = HhDatum.get_by_id(sess, datum_id)
    return render_template('hh_datum_edit.html', hh=hh)


@app.route('/hh_data/<int:datum_id>/edit', methods=['POST'])
def hh_datum_edit_post(datum_id):
    try:
        sess = db.session()
        set_read_write(sess)
        hh = HhDatum.get_by_id(sess, datum_id)
        channel_id = hh.channel.id
        if 'delete' in request.values:
            hh.channel.delete_data(sess, hh.start_date, hh.start_date)
            sess.commit()
            return redirect('/channels/' + str(channel_id), 303)
        else:
            value = req_decimal('value')
            status = req_str('status')
            channel = hh.channel
            era = channel.era
            imp_mpan_core = era.imp_mpan_core
            exp_mpan_core = era.exp_mpan_core
            mpan_core = imp_mpan_core if channel.imp_related else exp_mpan_core
            HhDatum.insert(
                sess, [
                    {
                        'mpan_core': mpan_core,
                        'channel_type': channel.channel_type,
                        'start_date': hh.start_date, 'value': value,
                        'status': status}])
            sess.commit()
            return redirect('/channels/' + str(channel_id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(render_template('hh_datum_edit.html', hh=hh), 400)


@app.route('/sites/<int:site_id>/hh_data')
def site_hh_data_get(site_id):
    sess = db.session()
    site = Site.get_by_id(sess, site_id)

    year = req_int('year')
    month = req_int('month')
    start_date = Datetime(year, month, 1, tzinfo=pytz.utc)
    finish_date = start_date + relativedelta(months=1) - HH
    groups = []

    for group in site.groups(sess, start_date, finish_date, True):
        sup_ids = sorted(supply.id for supply in group.supplies)
        group_dict = {
            'supplies': [Supply.get_by_id(sess, id) for id in sup_ids]}
        groups.append(group_dict)

        data = iter(
            HhDatum.query.join(Channel, Era, Supply, Source).filter(
                Channel.channel_type == 'ACTIVE', Supply.id.in_(sup_ids),
                HhDatum.start_date >= group.start_date,
                HhDatum.start_date <= group.finish_date).order_by(
                HhDatum.start_date, Supply.id))
        datum = next(data, None)

        hh_date = group.start_date

        hh_data = []
        group_dict['hh_data'] = hh_data

        while not hh_date > group.finish_date:
            sups = []
            hh_dict = {
                'start_date': hh_date, 'supplies': sups, 'export_kwh': 0,
                'import_kwh': 0, 'parasitic_kwh': 0, 'generated_kwh': 0,
                'third_party_import_kwh': 0, 'third_party_export_kwh': 0}
            hh_data.append(hh_dict)
            for sup_id in sup_ids:
                sup_hh = {}
                sups.append(sup_hh)
                while datum is not None and datum.start_date == hh_date and \
                        datum.channel.era.supply.id == sup_id:
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
                        hh_dict['third_party_import'] += hh_float_value
                    if (not imp_related and source_code == '3rd-party') or \
                            (imp_related and
                                source_code == '3rd-party-reverse'):
                        hh_dict['third_party_export'] += hh_float_value
                    datum = next(data, None)

            hh_dict['displaced_kwh'] = hh_dict['generated_kwh'] - \
                hh_dict['export_kwh'] - hh_dict['parasitic_kwh']
            hh_dict['used_kwh'] = hh_dict['import_kwh'] + \
                hh_dict['displaced_kwh']
            hh_date = hh_date + HH

    return render_template('site_hh_data.html', site=site, groups=groups)


@app.route('/sites/<int:site_id>')
def site_get(site_id):
    sess = db.session()
    configuration_contract = Contract.get_non_core_by_name(
        sess, 'configuration')
    site = Site.get_by_id(sess, site_id)

    eras = Era.query.join(SiteEra).filter(SiteEra.site == site).order_by(
        Era.supply_id, Era.start_date.desc()).all()

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

    groups = sorted(
        groups, key=operator.itemgetter('is_ongoing'), reverse=True)

    now = Datetime.now(pytz.utc)
    month_start = Datetime(now.year, now.month, 1)
    month_finish = month_start + relativedelta(months=1) - HH
    last_month_start = month_start - relativedelta(months=1)
    last_month_finish = month_start - HH

    properties = configuration_contract.make_properties()
    other_sites = [
        s for s in site.groups(sess, now, now, False)[0].sites if s != site]
    scenarios = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'X', Contract.name.like('scenario_%')).order_by(
        Contract.name).all()
    return render_template(
        'site.html', site=site, groups=groups, properties=properties,
        other_sites=other_sites, month_start=month_start,
        month_finish=month_finish, last_month_start=last_month_start,
        last_month_finish=last_month_finish, scenarios=scenarios)


@app.route('/downloads')
def downloads_get():
    files = []
    download_path = chellow.dloads.download_path

    for fl in sorted(os.listdir(download_path), reverse=True):
        statinfo = os.stat(os.path.join(download_path, fl))
        files.append(
            {
                'name': fl,
                'last_modified': Datetime.utcfromtimestamp(statinfo.st_mtime),
                'size': statinfo.st_size,
                'creation_date': Datetime.utcfromtimestamp(statinfo.st_ctime)})

    return render_template('downloads.html', files=files)


@app.route('/downloads/<fname>')
def download_get(fname):
    head, name = os.path.split(os.path.normcase(os.path.normpath(fname)))

    download_path = os.path.join(chellow.app.instance_path, 'downloads')

    full_name = os.path.join(download_path, name)

    def content():
        try:
            with open(full_name, 'rb') as fl:
                yield fl.read()
        except:
            yield traceback.format_exc()

    return send_response(content, file_name=name)


@app.route('/downloads/<fname>', methods=['POST'])
def download_post(fname):
    head, name = os.path.split(os.path.normcase(os.path.normpath(fname)))

    download_path = os.path.join(chellow.app.instance_path, 'downloads')
    full_name = os.path.join(download_path, name)
    os.remove(full_name)
    return redirect("/downloads", 303)


@app.route('/channel_snags')
def channel_snags_get():
    sess = db.session()
    contract_id = req_int('hhdc_contract_id')
    contract = Contract.get_hhdc_by_id(sess, contract_id)
    days_hidden = req_int('days_hidden')
    is_ignored = req_bool('is_ignored')

    total_snags = Snag.query.join(Channel).join(Era).filter(
        Snag.is_ignored == false(), Era.hhdc_contract == contract,
        Snag.start_date < Datetime.now(pytz.utc) -
        relativedelta(days=days_hidden)).count()
    snags = Snag.query.join(Channel).join(Era).join(
        Era.site_eras).join(SiteEra.site).filter(
        Snag.is_ignored == is_ignored, Era.hhdc_contract == contract,
        Snag.start_date < Datetime.now(pytz.utc) -
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
                'sites': sess.query(Site).join(Site.site_eras).filter(
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


@app.route('/non_core_contracts')
def non_core_contracts_get():
    non_core_contracts = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'Z').order_by(Contract.name).all()
    return render_template(
        'non_core_contracts.html', non_core_contracts=non_core_contracts)


@app.route('/non_core_contracts/<int:contract_id>')
def non_core_contract_get(contract_id):
    sess = db.session()
    contract = Contract.get_non_core_by_id(sess, contract_id)
    rate_scripts = RateScript.query.filter(
        RateScript.contract == contract).order_by(
        RateScript.start_date.desc()).all()
    return render_template(
        'non_core_contract.html', contract=contract, rate_scripts=rate_scripts)


@app.route('/sites/<int:site_id>/used_graph')
def site_used_graph_get(site_id):
    sess = db.session()

    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    months = req_int("months")

    finish_date = Datetime(finish_year, finish_month, 1, tzinfo=pytz.utc) + \
        relativedelta(months=1) - HH
    start_date = Datetime(finish_year, finish_month, 1, tzinfo=pytz.utc) - \
        relativedelta(months=months-1)

    site = Site.get_by_id(sess, site_id)
    supplies = Supply.query.join(Era).join(Source).join(SiteEra).filter(
        SiteEra.site == site, not_(Source.code.in_(('sub', 'gen-net')))). \
        distinct().all()

    result = iter(
        sess.execute(
            "select hh_datum.value, hh_datum.start_date, hh_datum.status, "
            "channel.imp_related, source.code from hh_datum, channel, era, "
            "supply, source where hh_datum.channel_id = channel.id and "
            "channel.era_id = era.id and era.supply_id = supply.id and "
            "supply.source_id = source.id and "
            "channel.channel_type = 'ACTIVE' and "
            "hh_datum.start_date >= :start_date and "
            "hh_datum.start_date <= :finish_date and supply.id in "
            "(" + ','.join(str(sup.id) for sup in supplies) +
            ") order by hh_datum.start_date",
            params={'start_date': start_date, 'finish_date': finish_date}))

    hh_date = start_date
    max_scale = 2
    min_scale = 0
    result_data = []
    days = []
    month_list = []
    step = 1

    try:
        row = next(result)
        hh_channel_value = float(row.value)
        hh_channel_start_date = row.start_date
        is_import = row.imp_related
        source_code = row.code

        while hh_date <= finish_date:
            complete = None
            hh_value = 0

            while hh_channel_start_date == hh_date:
                if (is_import and source_code != '3rd-party-reverse') or \
                        (not is_import and source_code == '3rd-party-reverse'):
                    hh_value += hh_channel_value
                else:
                    hh_value -= hh_channel_value
                if row.status == 'A':
                    if complete is None:
                        complete = True
                else:
                    complete = False
                try:
                    row = next(result)
                    hh_channel_value = float(row.value)
                    hh_channel_start_date = row.start_date
                    is_import = row.imp_related
                except StopIteration:
                    hh_channel_start_date = None

            result_data.append(
                {
                    'value': hh_value, 'start_date': hh_date,
                    'is_complete': complete is True})
            max_scale = max(max_scale, int(math.ceil(hh_value)))
            min_scale = min(min_scale, int(math.floor(hh_value)))
            hh_date += HH

        # System.err.println('ooostep is max scale' + str(maxScale) +
        # ' min scale ' + str(minScale))

        # raise Exception('pppstep is max scale' + str(maxScale) +
        # ' min scale ' + str(minScale))
        step = 10**int(math.floor(math.log10(max_scale - min_scale)))
        # raise Exception('step is ' + str(step))

        # System.err.println('kkstep is ' + str(step) + ' max scale' +
        # str(maxScale) + ' min scale ' + str(minScale))

        # if step > (maxScale - minScale) / 2:
        #    step = int(float(step) / 4)
    except StopIteration:
        pass

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
            range(0, max_scale, step), range(0, min_scale, step * -1)):
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


@app.route('/supplies/<int:supply_id>/hh_data')
def supply_hh_data_get(supply_id):
    sess = db.session()
    months = req_int('months')
    finish_year = req_int("finish_year")
    finish_month = req_int("finish_month")
    supply = Supply.get_by_id(sess, supply_id)

    finish_date = Datetime(
        finish_year, finish_month, 1, tzinfo=pytz.utc) + \
        relativedelta(months=1) - HH
    start_date = Datetime(
        finish_year, finish_month, 1, tzinfo=pytz.utc) - \
        relativedelta(months=months-1)

    era = Era.query.filter(
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

    hh_data = iter(HhDatum.query.join(Channel).join(Era).filter(
        Era.supply == supply, HhDatum.start_date >= start_date,
        HhDatum.start_date <= finish_date).order_by(HhDatum.start_date))
    hh_lines = []

    hh_date = start_date
    try:
        hh_datum = next(hh_data)
    except StopIteration:
        hh_datum = None
    while hh_date <= finish_date:
        hh_line = {'timestamp': hh_date}
        hh_lines.append(hh_line)
        while hh_datum is not None and hh_datum.start_date == hh_date:
            channel = hh_datum.channel
            hh_line[keys[channel.imp_related][channel.channel_type]] = \
                hh_datum
            try:
                hh_datum = next(hh_data)
            except StopIteration:
                hh_datum = None

        hh_date += HH
    return render_template(
        'supply_hh_data.html', supply=supply, era=era, hh_lines=hh_lines,
        start_date=start_date, finish_date=finish_date)


@app.route('/dno_contracts/<int:contract_id>/add_rate_script')
def add_rate_script_get(contract_id):
    now = Datetime.now(pytz.utc)
    initial_date = Datetime(now.year, now.month, 1, tzinfo=pytz.utc)
    sess = db.session()
    contract = Contract.get_dno_by_id(sess, contract_id)
    return render_template(
        'dno_rate_script_add.html', contract=contract,
        initial_date=initial_date)


@app.route(
    '/dno_contracts/<int:contract_id>/add_rate_script', methods=['POST'])
def add_rate_script_post(contract_id):
    try:
        sess = db.session()
        set_read_write(sess)
        contract = Contract.get_dno_by_id(sess, contract_id)
        start_date = req_date('start')
        rate_script = contract.insert_rate_script(sess, start_date, '')
        sess.commit()
        return redirect('/dno_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = Datetime.now(pytz.utc)
        initial_date = Datetime(now.year, now.month, 1, tzinfo=pytz.utc)
        return make_response(
            render_template(
                'dno_rate_script_add.html', contract=contract,
                initial_date=initial_date), 400)


@app.route('/dno_rate_scripts/<int:rs_id>/edit')
def rate_script_edit_get(rs_id):
    sess = db.session()
    rs = RateScript.get_dno_by_id(sess, rs_id)
    return render_template('dno_rate_script_edit.html', rate_script=rs)


@app.route('/dno_rate_scripts/<int:rs_id>/edit', methods=['POST'])
def rate_script_edit_post(rs_id):
    try:
        sess = db.session()
        set_read_write(sess)
        rate_script = RateScript.get_dno_by_id(sess, rs_id)
        contract = rate_script.contract
        if 'delete' in request.values:
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            return redirect('/dno_rate_scripts/' + str(contract.id), 303)
        else:
            script = req_str('script')
            start_date = req_date('start')
            if 'has_finished' in request.values:
                finish_date = req_date('finish')
            else:
                finish_date = None
            contract.update_rate_script(
                sess, rate_script, start_date, finish_date, script)
            sess.commit()
            return redirect('/dno_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template(
                'dno_rate_script_edit.html', rate_script=rate_script), 400)


@app.route('/non_core_contracts/<int:contract_id>/edit')
def non_core_contract_edit_get(contract_id):
    sess = db.session()
    contract = Contract.get_non_core_by_id(sess, contract_id)
    return render_template('non_core_contract_edit.html', contract=contract)


@app.route('/non_core_contracts/<int:contract_id>/edit', methods=['POST'])
def non_core_contract_edit_post(contract_id):
    try:
        sess = db.session()
        set_read_write(sess)
        contract = Contract.get_non_core_by_id(sess, contract_id)
        if 'delete' in request.values:
            contract.delete(sess)
            sess.commit()
            return redirect('/non_core_contracts', 303)
        if 'update_state' in request.values:
            state = req_str("state")
            contract.state = state
            sess.commit()
            return redirect('/non_core_contracts/' + str(contract.id), 303)
        else:
            properties = req_str('properties')
            contract.update_properties(properties)
            sess.commit()
            return redirect('/non_core_contracts/' + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template(
                'non_core_contract_edit.html', contract=contract), 400)


@app.route('/sites/<int:site_id>/months')
def site_months_get(site_id):
    sess = db.session()
    finish_year = req_int('finish_year')
    finish_month = req_int('finish_month')
    start_date = Datetime(finish_year, finish_month, 1, tzinfo=pytz.utc)
    start_date -= relativedelta(months=11)
    site = Site.get_by_id(sess, site_id)

    typs = (
        'imp_net', 'exp_net', 'used', 'displaced', 'imp_gen', 'exp_gen')

    months = []
    month_start = start_date
    for i in range(12):
        month_finish = month_start + relativedelta(months=1) - HH
        month = dict(
            (typ, {'md': 0, 'md_date': None, 'kwh': 0}) for typ in typs)
        month['start_date'] = month_start
        months.append(month)

        for group in site.groups(sess, month_start, month_finish, True):
            for hh in group.hh_data(sess):
                for tp in typs:
                    if hh[tp] * 2 > month[tp]['md']:
                        month[tp]['md'] = hh[tp] * 2
                        month[tp]['md_date'] = hh['start_date']
                    month[tp]['kwh'] += hh[tp]

        has_snags = sess.query(Snag).filter(
            Snag.site == site, Snag.start_date <= month_finish,
            or_(
                Snag.finish_date is None,
                Snag.finish_date > month_start)).count() > 0
        month['has_site_snags'] = has_snags

        month_start += relativedelta(months=1)

    totals = dict(
        (typ, {'md': 0, 'md_date': None, 'kwh': 0}) for typ in typs)

    for month in months:
        for typ in typs:
            if month[typ]['md'] > totals[typ]['md']:
                totals[typ]['md'] = month[typ]['md']
                totals[typ]['md_date'] = month[typ]['md_date']
            totals[typ]['kwh'] += month[typ]['kwh']

    months.append(totals)

    return render_template('site_months.html', site=site, months=months)


@app.route('/supplier_bills/<int:bill_id>')
def supplier_bill_get(bill_id):
    sess = db.session()
    bill = Bill.get_by_id(sess, bill_id)
    register_reads = RegisterRead.query.filter(
        RegisterRead.bill == bill).order_by(
        RegisterRead.present_date.desc())
    fields = {'bill': bill, 'register_reads': register_reads}
    try:
        breakdown_dict = eval(bill.breakdown, {})

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
                    grid[row_name][col_name] = v
                    del breakdown_dict[k]
                    break

        for k, v in breakdown_dict.items():
            pair = k.split('-')
            row_name = '-'.join(pair[:-1])
            column_name = pair[-1]
            rows.add(row_name)
            columns.add(column_name)
            grid[row_name][column_name] = v

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


@app.route('/reads/<int:read_id>/edit')
def read_edit_get(read_id):
    sess = db.session()
    read = RegisterRead.get_by_id(sess, read_id)
    read_types = ReadType.query.order_by(ReadType.code).all()
    tprs = Tpr.query.order_by(Tpr.code).all()
    return render_template(
        'read_edit.html', read=read, read_types=read_types, tprs=tprs)


@app.route('/reads/<int:read_id>/edit', methods=['POST'])
def read_edit_post(read_id):
    try:
        sess = db.session()
        set_read_write(sess)
        read = RegisterRead.get_by_id(sess, read_id)
        if 'update' in request.values:
            tpr_id = req_int('tpr_id')
            tpr = Tpr.get_by_id(sess, tpr_id)
            coefficient = req_decimal('coefficient')
            units = req_str('units')
            msn = req_str('msn')
            mpan_str = req_str('mpan')
            previous_date = req_date('previous')
            previous_value = req_decimal('previous_value')
            previous_type_id = req_int('previous_type_id')
            previous_type = ReadType.get_by_id(sess, previous_type_id)
            present_date = req_date('present')
            present_value = req_decimal('present_value')
            present_type_id = req_int('present_type_id')
            present_type = ReadType.get_by_id(sess, present_type_id)

            read.update(
                tpr, coefficient, units, msn, mpan_str, previous_date,
                previous_value, previous_type, present_date, present_value,
                present_type)
            sess.commit()
            return redirect("/supplier_bills/" + str(read.bill.id), 303)
        elif 'delete' in request.values:
            read.delete()
            sess.commit()
            return redirect("supplier_bills/" + str(read.bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        read_types = ReadType.query.order_by(ReadType.code).all()
        tprs = Tpr.query.order_by(Tpr.code).all()
        return make_response(
            render_template(
                'read_edit.html', read=read, read_types=read_types, tprs=tprs),
            400)


@app.route('/hhdc_batches')
def hhdc_batches_get():
    sess = db.session()
    contract_id = req_int('hhdc_contract_id')
    contract = Contract.get_hhdc_by_id(sess, contract_id)
    batches = Batch.query.filter(Batch.contract == contract).order_by(
        Batch.reference.desc()).all()
    return render_template(
        'hhdc_batches.html', contract=contract, batches=batches)


@app.route('/hhdc_batches/<int:batch_id>')
def hhdc_batch_get(batch_id):
    sess = db.session()
    batch = Batch.get_by_id(sess, batch_id)
    bills = Bill.query.filter(Bill.batch == batch).order_by(
        Bill.reference).all()

    config_contract = Contract.get_non_core_by_name(sess, 'configuration')
    properties = config_contract.make_properties()
    fields = {'batch': batch, 'bills': bills}
    if 'batch_reports' in properties:
        batch_reports = []
        for report_id in properties['batch_reports']:
            batch_reports.append(Report.get_by_id(sess, report_id))
        fields['batch_reports'] = batch_reports
    return render_template('hhdc_batch.html', **fields)


@app.route('/supplier_bills/<int:bill_id>/edit')
def supplier_bill_edit_get(bill_id):
    bill_types = BillType.query.order_by(BillType.code).all()
    sess = db.session()
    bill = Bill.get_by_id(sess, bill_id)
    return render_template(
        'supplier_bill_edit.html', bill=bill, bill_types=bill_types)


@app.route('/supplier_bills/<int:bill_id>/edit', methods=['POST'])
def supplier_bill_edit_post(bill_id):
    try:
        sess = db.session()
        set_read_write(sess)
        bill = Bill.get_by_id(sess, bill_id)
        if 'delete' in request.values:
            bill.delete(sess)
            sess.commit()
            return redirect("/supplier_batches/" + str(bill.batch.id), 303)
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
            breakdown = ast.literal_eval(breakdown_str)
            bill_type = BillType.get_by_id(sess, type_id)

            bill.update(
                account, reference, issue_date, start_date, finish_date, kwh,
                net, vat, gross, bill_type, breakdown)
            sess.commit()
            return redirect("/supplier_bills/" + str(bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        bill_types = BillType.query.order_by(BillType.code).all()
        return make_response(
            render_template(
                'supplier_bill_edit.html', bill=bill, bill_types=bill_types),
            400)


@app.route('/hhdc_contracts/<int:contract_id>/add_batch')
def hhdc_batch_add_get(contract_id):
    sess = db.session()
    contract = Contract.get_hhdc_by_id(sess, contract_id)
    batches = Batch.query.filter(Batch.contract == contract).order_by(
        Batch.reference.desc())
    return render_template(
        'hhdc_batch_add.html', contract=contract, batches=batches)


@app.route('/hhdc_contracts/<int:contract_id>/add_batch', methods=['POST'])
def hhdc_batch_add_post(contract_id):
    try:
        sess = db.session()
        set_read_write(sess)
        contract = Contract.get_hhdc_by_id(sess, contract_id)
        reference = req_str('reference')
        description = req_str('description')
        batch = contract.insert_batch(sess, reference, description)
        sess.commit()
        return redirect("/hhdc_batches/" + str(batch.id), 303)
    except BadRequest as e:
        flash(e.description)
        batches = Batch.query.filter(Batch.contract == contract).order_by(
            Batch.reference.desc())
        return make_response(
            render_template(
                'hhdc_batch_add.html', contract=contract, batches=batches),
            400)


@app.route('/hhdc_batches/<int:batch_id>/edit')
def hhdc_batch_edit_get(batch_id):
    sess = db.session()
    batch = Batch.get_by_id(sess, batch_id)
    return render_template('hhdc_batch_edit.html', batch=batch)


@app.route('/hhdc_batches/<int:batch_id>/edit', methods=['POST'])
def hhdc_batch_edit_post(batch_id):
    try:
        sess = db.session()
        set_read_write(sess)
        batch = Batch.get_by_id(sess, batch_id)
        reference = req_str('reference')
        description = req_str('description')
        batch.update(sess, reference, description)
        sess.commit()
        return redirect("/hhdc_batches/" + str(batch.id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template('hhdc_batch_edit.html', batch=batch), 400)


@app.route('/hhdc_batches/<int:batch_id>/edit', methods=['DELETE'])
def hhdc_batch_edit_delete(batch_id):
    try:
        sess = db.session()
        set_read_write(sess)
        batch = Batch.get_by_id(sess, batch_id)
        contract = batch.contract
        batch.delete(sess)
        sess.commit()
        return redirect("/hhdc_contracts/" + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template('hhdc_batch_edit.html', batch=batch), 400)


@app.route('/hhdc_bill_imports')
def hhdc_bill_imports_get():
    sess = db.session()
    batch_id = req_int('hhdc_batch_id')
    batch = Batch.get_by_id(sess, batch_id)
    return render_template(
        'hhdc_bill_imports.html', importer_ids=sorted(
            chellow.bill_importer.get_bill_import_ids(batch.id),
            reverse=True), batch=batch)


@app.route('/hhdc_bill_imports', methods=['POST'])
def hhdc_bill_imports_post():
    try:
        sess = db.session()
        batch_id = req_int('hhdc_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        file_item = request.files["import_file"]

        f = io.StringIO(str(file_item.stream.read(), 'utf8'))
        f.seek(0, os.SEEK_END)
        file_size = f.tell()

        f.seek(0)
        import_id = chellow.bill_importer.start_bill_import(
            sess, batch.id, file_item.filename, file_size, f)
        return redirect("/hhdc_bill_imports/" + str(import_id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template(
                'hhdc_bill_imports.html', importer_ids=sorted(
                    chellow.bill_importer.get_bill_import_ids(batch.id),
                    reverse=True), batch=batch), 400)


@app.route('/hhdc_bill_imports/<int:import_id>')
def hhdc_bill_import_get(import_id):
    sess = db.session()
    importer = chellow.bill_importer.get_bill_import(import_id)
    batch = Batch.get_by_id(sess, importer.batch_id)
    fields = {'batch': batch}
    if importer is not None:
        imp_fields = importer.make_fields()
        if 'successful_bills' in imp_fields and \
                len(imp_fields['successful_bills']) > 0:
            fields['successful_max_registers'] = \
                max(
                    len(bill['reads']) for bill in imp_fields[
                        'successful_bills'])
        fields.update(imp_fields)
        fields['status'] = importer.status()
    return render_template('hhdc_bill_import.html', **fields)


@app.route('/mop_contracts/<int:contract_id>/add_batch')
def mop_batch_add_get(contract_id):
    sess = db.session()
    contract = Contract.get_mop_by_id(sess, contract_id)
    batches = Batch.query.filter(Batch.contract == contract).order_by(
        Batch.reference.desc())
    return render_template(
        'mop_batch_add.html', contract=contract, batches=batches)


@app.route('/mop_contracts/<int:contract_id>/add_batch', methods=['POST'])
def mop_batch_add_post(contract_id):
    try:
        sess = db.session()
        set_read_write(sess)
        contract = Contract.get_mop_by_id(sess, contract_id)
        reference = req_str("reference")
        description = req_str("description")

        batch = contract.insert_batch(sess, reference, description)
        sess.commit()
        return redirect("/mop_batches/" + str(batch.id), 303)
    except BadRequest as e:
        flash(e.description)
        batches = Batch.query.filter(Batch.contract == contract).order_by(
            Batch.reference.desc())
        return make_response(
            render_template(
                'mop_batch_add.html', contract=contract, batches=batches), 303)


@app.route('/mop_batches/<int:batch_id>/edit')
def mop_batch_edit_get(batch_id):
    sess = db.session()
    batch = Batch.get_by_id(sess, batch_id)
    return render_template('mop_batch_edit.html', batch=batch)


@app.route('/mop_batches/<int:batch_id>/add_batch', methods=['POST'])
def mop_batch_edit_post(batch_id):
    try:
        sess = db.session()
        set_read_write(sess)
        batch = Batch.get_by_id(sess, batch_id)
        if 'update' in request.values:
            reference = req_str('reference')
            description = req_str('description')
            batch.update(sess, reference, description)
            sess.commit()
            return redirect("/mop_batches/" + str(batch.id), 303)
        elif 'delete' in request.values:
            contract = batch.contract
            batch.delete(sess)
            sess.commit()
            return redirect("/mop_contracts/" + str(contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        return render_template('mop_batch_edit.html', batch=batch)


@app.route('/mop_batches/<int:batch_id>')
def mop_batch_get(batch_id):
    sess = db.session()
    batch = Batch.get_by_id(sess, batch_id)
    bills = Bill.query.filter(Bill.batch == batch).order_by(
        Bill.reference).all()

    config_contract = Contract.get_non_core_by_name(sess, 'configuration')
    properties = config_contract.make_properties()
    fields = {'batch': batch, 'bills': bills}
    if 'batch_reports' in properties:
        batch_reports = []
        for report_id in properties['batch_reports']:
            batch_reports.append(Report.get_by_id(sess, report_id))
        fields['batch_reports'] = batch_reports
    return render_template('mop_batch.html', **fields)


@app.route('/mop_bill_imports')
def mop_bill_imports_get():
    sess = db.session()
    batch_id = req_int('mop_batch_id')
    batch = Batch.get_by_id(sess, batch_id)
    return render_template(
        'mop_bill_imports.html', importer_ids=sorted(
            chellow.bill_importer.get_bill_importer_ids(batch.id),
            reverse=True),
        batch=batch)


@app.route('/mop_bill_imports', methods=['POST'])
def mop_bill_imports_post():
    try:
        sess = db.session()
        batch_id = req_int('mop_batch_id')
        batch = Batch.get_by_id(sess, batch_id)
        file_item = request.files["import_file"]
        f = io.StringIO(str(file_item.stream.read(), 'utf8'))
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        f.seek(0)
        iid = chellow.bill_importer.start_bill_import(
            sess, batch.id, file_item.filename, file_size, f)
        return redirect("/mop_bill_imports/" + str(iid), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template(
                'mop_bill_imports.html', importer_ids=sorted(
                    chellow.bill_importer.get_bill_import_ids(batch.id),
                    reverse=True), batch=batch), 400)


@app.route('/mop_bill_imports/<int:import_id>')
def mop_bill_import_get(import_id):
    sess = db.session()
    bill_import = chellow.bill_importer.get_bill_import(import_id)
    batch = Batch.get_by_id(sess, bill_import.batch_id)
    fields = {'batch': batch}
    if bill_import is not None:
        imp_fields = bill_import.make_fields()
        if 'successful_bills' in imp_fields and \
                len(imp_fields['successful_bills']) > 0:
            fields['successful_max_registers'] = \
                max(
                    len(bill['reads']) for bill in imp_fields[
                        'successful_bills'])
        fields.update(imp_fields)
        fields['status'] = bill_import.status()
    return render_template('mop_bill_import.html', **fields)


@app.route('/meter_payment_types')
def meter_payment_types_get():
    meter_payment_types = MeterPaymentType.query.order_by(
        MeterPaymentType.code).all()
    return render_template(
        'meter_payment_types.html', meter_payment_types=meter_payment_types)


@app.route('/meter_payment_types/<int:type_id>')
def meter_payment_type_get(type_id):
    sess = db.session()
    meter_payment_type = MeterPaymentType.get_by_id(sess, type_id)
    return render_template(
        'meter_payment_type.html', meter_payment_type=meter_payment_type)


@app.route('/non_core_contracts/<int:contract_id>/add_rate_script')
def non_core_rate_script_add_get(contract_id):
    now = Datetime.now(pytz.utc)
    initial_date = Datetime(now.year, now.month, 1, tzinfo=pytz.utc)
    sess = db.session()
    contract = Contract.get_non_core_by_id(sess, contract_id)
    return render_template(
        'non_core_rate_script_add.html', now=now, initial_date=initial_date,
        contract=contract)


@app.route(
    '/non_core_contracts/<int:contract_id>/add_rate_script', methods=['POST'])
def non_core_rate_script_add_post(contract_id):
    try:
        sess = db.session()
        set_read_write(sess)
        contract = Contract.get_non_core_by_id(sess, contract_id)
        start_date = req_date('start')
        rate_script = contract.insert_rate_script(sess, start_date, '')
        sess.commit()
        return redirect('/non_core_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        flash(e.description)
        now = Datetime.now(pytz.utc)
        initial_date = Datetime(now.year, now.month, 1, tzinfo=pytz.utc)
        return make_response(
            render_template(
                'non_core_rate_script_add.html', now=now,
                initial_date=initial_date, contract=contract), 400)


@app.route('/non_core_rate_scripts/<int:rs_id>')
def non_core_rate_script_get(rs_id):
    sess = db.session()
    rate_script = RateScript.get_non_core_by_id(sess, rs_id)
    return render_template(
        'non_core_rate_script.html', rate_script=rate_script)


@app.route('/non_core_rate_scripts/<int:rs_id>/edit')
def non_core_rate_script_edit_get(rs_id):
    sess = db.session()
    rate_script = RateScript.get_non_core_by_id(sess, rs_id)
    return render_template(
        'non_core_rate_script_edit.html', rate_script=rate_script)


@app.route('/non_core_rate_scripts/<int:rs_id>/edit', methods=['POST'])
def non_core_rate_script_edit_post(rs_id):
    try:
        sess = db.session()
        set_read_write(sess)
        rate_script = RateScript.get_non_core_by_id(sess, rs_id)
        contract = rate_script.contract
        if 'delete' in request.values:
            contract.delete_rate_script(sess, rate_script)
            sess.commit()
            return redirect('/non_core_contracts/' + str(contract.id), 303)
        else:
            script = req_str('script')
            start_date = req_hh_date('start')
            if 'has_finished' in request.values:
                finish_date = req_date('finish')
            else:
                finish_date = None
            contract.update_rate_script(
                sess, rate_script, start_date, finish_date, script)
            sess.commit()
            return redirect(
                '/non_core_rate_scripts/' + str(rate_script.id), 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        return make_response(
            render_template(
                'non_core_rate_script_edit.html', rate_script=rate_script),
            400)


@app.route('/supplier_batches/<int:batch_id>/add_bill')
def supplier_bill_add_get(batch_id):
    sess = db.session()
    batch = Batch.get_by_id(sess, batch_id)
    bill_types = BillType.query.order_by(BillType.code)
    bills = Bill.query.filter(Bill.batch == batch).order_by(Bill.start_date)
    return render_template(
        'supplier_bill_add.html', batch=batch, bill_types=bill_types,
        bills=bills)


@app.route('/supplier_batches/<int:batch_id>/add_bill', methods=['POST'])
def supplier_bill_add_post(batch_id):
    try:
        sess = db.session()
        set_read_write(sess)
        batch = Batch.get_by_id(sess, batch_id)
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
        bill_type = BillType.get_by_id(sess, bill_type_id)
        breakdown_str = req_str('breakdown')
        breakdown = eval(breakdown_str)
        bill_type = BillType.get_by_id(sess, bill_type_id)
        bill = batch.insert_bill(
            sess, account, reference, issue_date, start_date, finish_date, kwh,
            net, vat, gross, bill_type, breakdown,
            Supply.get_by_mpan_core(sess, mpan_core))
        sess.commit()
        return redirect('/supplier_bills/' + str(bill.id), 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        bill_types = BillType.query.order_by(BillType.code)
        bills = Bill.query.filter(Bill.batch == batch).order_by(
            Bill.start_date)
        return make_response(
            render_template(
                'supplier_bill_add.html', batch=batch, bill_types=bill_types,
                bills=bills), 400)


@app.route('/supplier_batches/<int:batch_id>/edit')
def supplier_batch_edit_get(batch_id):
    sess = db.session()
    batch = Batch.get_by_id(sess, batch_id)
    return render_template('supplier_batch_edit.html', batch=batch)


@app.route('/supplier_batches/<int:batch_id>/edit', methods=['POST'])
def supplier_batch_edit_post(batch_id):
    try:
        sess = db.session()
        set_read_write(sess)
        batch = Batch.get_by_id(sess, batch_id)
        if 'update' in request.values:
            reference = req_str('reference')
            description = req_str('description')
            batch.update(sess, reference, description)
            sess.commit()
            return redirect("/supplier_batches/" + str(batch.id), 303)
        elif 'delete' in request.values:
            contract_id = batch.contract.id
            batch.delete(sess)
            sess.commit()
            return redirect('supplier_contracts/' + str(contract_id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template('supplier_batch_edit.html', batch=batch), 400)


@app.route('/mop_batches')
def mop_batches_get():
    sess = db.session()
    contract_id = req_int('mop_contract_id')
    contract = Contract.get_mop_by_id(sess, contract_id)
    batches = Batch.query.filter(Batch.contract == contract).order_by(
        Batch.reference.desc()).all()
    return render_template(
        'mop_batches.html', contract=contract, batches=batches)


@app.route('/supplies/<int:supply_id>/notes')
def supply_notes_get(supply_id):
    sess = db.session()
    supply = Supply.get_by_id(sess, supply_id)

    if len(supply.note.strip()) > 0:
        note_str = supply.note
    else:
        note_str = "{'notes': []}"
    supply_note = eval(note_str)

    return render_template(
        'supply_notes.html', supply=supply, supply_note=supply_note)


@app.route('/supplies/<int:supply_id>/notes/add')
def supply_note_add_get(supply_id):
    sess = db.session()
    supply = Supply.get_by_id(sess, supply_id)
    return render_template('supply_note_add.html', supply=supply)


@app.route('/supplies/<int:supply_id>/notes/add', methods=['POST'])
def supply_note_add_post(supply_id):
    try:
        sess = db.session()
        set_read_write(sess)
        supply = Supply.get_by_id(sess, supply_id)
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
        sess.commit()
        return redirect('/supplies/' + str(supply_id), 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template('supply_note_add.html', supply=supply), 400)


@app.route('/hhdc_contracts/<int:contract_id>/auto_importer')
def hhdc_auto_importer_get(contract_id):
    sess = db.session()
    contract = Contract.get_hhdc_by_id(sess, contract_id)
    task = chellow.hh_importer.get_hh_import_task(contract)
    return render_template(
        'hhdc_auto_importer.html', contract=contract, task=task)


@app.route('/hhdc_contracts/<int:contract_id>/auto_importer', methods=['POST'])
def hhdc_auto_importer_post(contract_id):
    try:
        sess = db.session()
        contract = Contract.get_hhdc_by_id(sess, contract_id)
        task = chellow.hh_importer.get_hh_import_task(contract)
        task.go()
        return redirect(
            '/hhdc_contracts/' + str(contract.id) + '/auto_importer', 303)
    except BadRequest as e:
        flash(e.description)
        return make_response(
            render_template(
                'hhdc_auto_importer.html', contract=contract, task=task), 400)


@app.route('/non_core_contracts/<int:contract_id>/auto_importer')
def non_core_auto_importer_get(contract_id):
    sess = db.session()
    contract = Contract.get_non_core_by_id(sess, contract_id)
    importer = import_module('chellow.' + contract.name).get_importer()
    return render_template(
        'non_core_auto_importer.html', importer=importer, contract=contract)


@app.route(
    '/non_core_contracts/<int:contract_id>/auto_importer', methods=['POST'])
def non_core_auto_importer_post(contract_id):
    try:
        sess = db.session()
        contract = Contract.get_non_core_by_id(sess, contract_id)
        importer = import_module('chellow.' + contract.name).get_importer()
        importer.go()
        return redirect(
            '/non_core_contracts/' + str(contract.id) + '/auto_importer', 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        return make_response(
            render_template(
                'non_core_auto_importer.html', importer=importer,
                contract=contract), 400)


@app.route('/mop_bills/<int:bill_id>')
def mop_bill_get(bill_id):
    sess = db.session()
    bill = Bill.get_by_id(sess, bill_id)
    register_reads = RegisterRead.query.filter(
        RegisterRead.bill == bill).order_by(RegisterRead.present_date.desc())
    fields = {'bill': bill, 'register_reads': register_reads}
    try:
        breakdown_dict = eval(bill.breakdown, {})

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

        for k, v in breakdown_dict.items():
            if k.endswith('-gbp'):
                columns.add('gbp')
                row_name = k[:-4]
                rows.add(row_name)
                grid[row_name]['gbp'] = v
                del breakdown_dict[k]

        for k, v in breakdown_dict.items():
            for row_name in sorted(list(rows), key=len, reverse=True):
                if k.startswith(row_name + '-'):
                    col_name = k[len(row_name) + 1:]
                    columns.add(col_name)
                    grid[row_name][col_name] = v
                    del breakdown_dict[k]
                    break

        for k, v in breakdown_dict.items():
            pair = k.split('-')
            row_name = '-'.join(pair[:-1])
            column_name = pair[-1]
            rows.add(row_name)
            columns.add(column_name)
            grid[row_name][column_name] = v

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


@app.route('/csv_sites_triad')
def csv_sites_triad_get():
    now = Datetime.utcnow()
    if now.month < 3:
        now += relativedelta(year=1)
    return render_template('csv_sites_triad.html', year=now.year)


@app.route('/csv_sites_hh_data')
def csv_sites_hh_data_get():
    now = Datetime.utcnow()
    start_date = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    finish_date = Datetime(now.year, now.month, 1) - HH
    return render_template(
        'csv_sites_hh_data.html', start_date=start_date,
        finish_date=finish_date)


@app.route('/csv_sites_monthly_duration')
def csv_sites_monthly_duration_get():
    now = Datetime.utcnow()
    month_start = Datetime(now.year, now.month, 1) - relativedelta(months=1)
    month_finish = Datetime(now.year, now.month, 1) - HH
    return render_template(
        'csv_sites_monthly_duration.html', month_start=month_start,
        month_finish=month_finish)


@app.route('/csv_register_reads')
def csv_register_reads_get():
    init = Datetime.utcnow()
    init = Datetime(init.year, init.month, 1) - relativedelta(months=1)
    return render_template('csv_register_reads.html', init=init)


@app.route('/csv_supplies_duration')
def csv_supplies_duration_get():
    last_month = Datetime.now(pytz.utc) - relativedelta(months=1)
    last_month_start = Datetime(
        last_month.year, last_month.month, 1, tzinfo=pytz.utc)
    last_month_finish = last_month_start + relativedelta(months=1) - HH
    return render_template(
        'csv_supplies_duration.html', last_month_start=last_month_start,
        last_month_finish=last_month_finish)


@app.route('/csv_bills')
def csv_bills_get():
    init = Datetime.utcnow()
    init = Datetime(init.year, init.month, 1) - relativedelta(months=1)
    return render_template('csv_bills.html', init=init)


@app.route('/tprs')
def tprs_get():
    tprs = Tpr.query.order_by(Tpr.code).all()
    return render_template('tprs.html', tprs=tprs)


@app.route('/tprs/<int:tpr_id>')
def tpr_get(tpr_id):
    sess = db.session()
    tpr = Tpr.get_by_id(sess, tpr_id)
    clock_intervals = ClockInterval.query.filter(
        ClockInterval.tpr == tpr).order_by(ClockInterval.id)
    return render_template(
        'tpr.html', tpr=tpr, clock_intervals=clock_intervals)


@app.route('/user_roles')
def user_roles_get():
    user_roles = UserRole.query.order_by(UserRole.code)
    return render_template('user_roles.html', user_roles=user_roles)


@app.route('/bill_types/<int:type_id>')
def bill_type_get(type_id):
    sess = db.session()
    bill_type = BillType.get_by_id(sess, type_id)
    return render_template('bill_type.html', bill_type=bill_type)


@app.route('/ods_scenario_runner')
def ods_scenario_runner_get():
    sess = db.session()
    contracts = [
        Contract.get_non_core_by_name(sess, name)
        for name in sorted(('ccl', 'aahedc', 'bsuos', 'tlms', 'rcrc'))]
    scenarios = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'X', Contract.name.like('scenario_%')).order_by(
        Contract.name).all()
    return render_template(
        'ods_scenario_runner.html', contracts=contracts, scenarios=scenarios)


@app.route('/site_snags/<int:snag_id>/edit')
def site_snag_edit_get(snag_id):
    sess = db.session()
    snag = Snag.get_by_id(sess, snag_id)
    return render_template('site_snag_edit.html', snag=snag)


@app.route('/site_snags/<int:snag_id>/edit', methods=['POST'])
def site_snag_edit_post(snag_id):
    try:
        sess = db.session()
        set_read_write(sess)
        ignore = req_bool('ignore')
        snag = Snag.get_by_id(sess, snag_id)
        snag.is_ignored = ignore
        sess.commit()
        return redirect("/site_snags/" + str(snag.id), 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        return make_response(
            render_template('site_snag_edit.html', snag=snag), 400)


@app.route('/supplies/<int:supply_id>/virtual_bill')
def supply_virtual_bill_get(supply_id):
    sess = db.session()
    supply = Supply.get_by_id(sess, supply_id)
    start_date = req_date('start')
    finish_date = req_date('finish')
    forecast_date = chellow.computer.forecast_date()

    net_gbp = 0
    caches = {}
    meras = []
    debug = ''

    month_start = Datetime(
        start_date.year, start_date.month, 1, tzinfo=pytz.utc)

    while not month_start > finish_date:
        month_finish = month_start + relativedelta(months=1) - HH

        chunk_start = start_date if start_date > month_start else month_start

        if finish_date < month_finish:
            chunk_finish = finish_date
        else:
            chunk_finish = month_finish

        for era in Era.query.filter(
                Era.supply == supply, Era.imp_mpan_core != null(),
                Era.start_date <= chunk_finish, or_(
                    Era.finish_date == null(),
                    Era.finish_date >= chunk_start)):
            if era.start_date > chunk_start:
                block_start = era.start_date
            else:
                block_start = chunk_start

            debug += 'found an era'

            if hh_before(chunk_finish, era.finish_date):
                block_finish = chunk_finish
            else:
                block_finish = era.finish_date

            contract = era.imp_supplier_contract
            data_source = chellow.computer.SupplySource(
                sess, block_start, block_finish, forecast_date, era, True,
                None, caches)
            headings = [
                'id', 'supplier_contract', 'account', 'start date',
                'finish date']
            data = [
                data_source.id, contract.name, data_source.supplier_account,
                data_source.start_date, data_source.finish_date]
            mera = {'headings': headings, 'data': data, 'skip': False}

            meras.append(mera)
            chellow.computer.contract_func(
                caches, contract, 'virtual_bill', None)(data_source)
            bill = data_source.supplier_bill
            net_gbp += bill['net-gbp']

            for title in chellow.computer.contract_func(
                    caches, contract, 'virtual_bill_titles', None)():
                if title == 'consumption-info':
                    del bill[title]
                    continue
                headings.append(title)
                data.append(bill[title])
                if title in bill:
                    del bill[title]

            for k in sorted(bill.keys()):
                headings.append(k)
                data.append(bill[k])

            if len(meras) > 1 and meras[-2]['headings'] == mera['headings']:
                mera['skip'] = True

        month_start += relativedelta(months=1)

    return render_template(
        'supply_virtual_bill.html', supply=supply, start_date=start_date,
        finish_date=finish_date, meras=meras, net_gbp=net_gbp)


@app.route('/mtcs')
def mtcs_get():
    sess = db.session()
    mtcs = sess.query(Mtc, Contract).outerjoin(Mtc.dno).outerjoin(
        Contract).order_by(Mtc.code, Party.dno_code).all()
    return render_template('mtcs.html', mtcs=mtcs)


@app.route('/mtcs/<int:mtc_id>')
def mtc_get(mtc_id):
    sess = db.session()
    mtc, dno_contract = sess.query(Mtc, Contract).outerjoin(Mtc.dno) \
        .outerjoin(Contract).filter(Mtc.id == mtc_id).one()
    return render_template('mtc.html', mtc=mtc, dno_contract=dno_contract)


@app.route('/csv_crc')
def csv_crc_get():
    start_date = Datetime.now(pytz.utc)
    if start_date.month < 3:
        start_date = start_date - relativedelta(years=1)
    return render_template('csv_crc.html', start_date=start_date)


@app.route('/dno_contracts')
def dno_contracts_get():
    dno_contracts = Contract.query.join(MarketRole).filter(
        MarketRole.code == 'R').order_by(Contract.name).all()
    return render_template('dno_contracts.html', dno_contracts=dno_contracts)


@app.route('/dno_contracts/<int:contract_id>')
def dno_contract_get(contract_id):
    sess = db.session()
    contract = Contract.get_dno_by_id(sess, contract_id)
    rate_scripts = RateScript.query.filter(
        RateScript.contract == contract).order_by(
        RateScript.start_date.desc()).all()
    reports = []
    return render_template(
        'dno_contract.html', contract=contract, rate_scripts=rate_scripts,
        reports=reports)


@app.route('/sscs')
def sscs_get():
    sscs = Ssc.query.options(
        joinedload(Ssc.measurement_requirements, MeasurementRequirement.tpr)
        ).order_by(Ssc.code)
    return render_template('sscs.html', sscs=sscs)


@app.route('/csv_supplies_triad')
def csv_supplies_triad_get():
    now = Datetime.utcnow()
    return render_template('csv_supplies_triad.html', year=now.year - 1)


@app.route('/supplier_bills/<int:bill_id>/add_read')
def read_add_get(bill_id):
    read_types = ReadType.query.order_by(ReadType.code)
    tprs = Tpr.query.order_by(Tpr.code)
    sess = db.session()
    bill = Bill.get_by_id(sess, bill_id)
    return render_template(
        'read_add.html', bill=bill, read_types=read_types, tprs=tprs)


@app.route('/supplier_bills/<int:bill_id>/add_read', methods=["POST"])
def read_add_post(bill_id):
    try:
        sess = db.session()
        set_read_write(sess)
        bill = Bill.get_by_id(sess, bill_id)
        tpr_id = req_int("tpr_id")
        tpr = Tpr.get_by_id(sess, tpr_id)
        coefficient = req_decimal("coefficient")
        units_str = req_str("units")
        msn = req_str("msn")
        mpan_str = req_str("mpan")
        previous_date = req_date("previous")
        previous_value = req_decimal("previous_value")
        previous_type_id = req_int("previous_type_id")
        previous_type = ReadType.get_by_id(sess, previous_type_id)
        present_date = req_date("present")
        present_value = req_decimal("present_value")
        present_type_id = req_int("present_type_id")
        present_type = ReadType.get_by_id(sess, present_type_id)

        bill.insert_read(
            sess, tpr, coefficient, units_str, msn, mpan_str, previous_date,
            previous_value, previous_type, present_date, present_value,
            present_type)
        sess.commit()
        return redirect("/supplier_bills/" + str(bill.id), 303)
    except BadRequest as e:
        flash(e.description)
        read_types = ReadType.query.order_by(ReadType.code)
        tprs = Tpr.query.order_by(Tpr.code)
        return make_response(
            render_template(
                'read_add.html', bill=bill, read_types=read_types, tprs=tprs),
            400)


@app.route('/hhdc_batches/<int:batch_id>/add_bill')
def hhdc_bill_add_get(batch_id):
    sess = db.session()
    batch = Batch.get_by_id(sess, batch_id)
    bill_types = BillType.query.order_by(BillType.code)
    bills = Bill.query.filter(Bill.batch == batch).order_by(Bill.start_date)
    return render_template(
        'hhdc_bill_add.html', batch=batch, bill_types=bill_types, bills=bills)


@app.route('/hhdc_batches/<int:batch_id>/add_bill', methods=['POST'])
def hhdc_bill_add_post(batch_id):
    try:
        sess = db.session()
        set_read_write(sess)
        batch = Batch.get_by_id(sess, batch_id)
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
        bill_type = BillType.get_by_id(sess, bill_type_id)
        breakdown_str = req_str("breakdown")

        breakdown = eval(breakdown_str)
        bill_type = BillType.get_by_id(sess, bill_type_id)
        bill = batch.insert_bill(
            sess, account, reference, issue_date, start_date, finish_date, kwh,
            net, vat, gross, bill_type, breakdown,
            Supply.get_by_mpan_core(sess, mpan_core))
        sess.commit()
        return redirect("/hhdc_bills/" + str(bill.id), 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        bill_types = BillType.query.order_by(BillType.code)
        bills = Bill.query.filter(Bill.batch == batch).order_by(
            Bill.start_date)
        return make_response(
            render_template(
                'hhdc_bill_add.html', batch=batch, bill_types=bill_types,
                bills=bills), 400)


@app.route('/pcs')
def pcs_get():
    return render_template('pcs.html', pcs=Pc.query.order_by(Pc.code))


@app.route('/pcs/<int:pc_id>')
def pc_get(pc_id):
    sess = db.session()
    pc = Pc.get_by_id(sess, pc_id)
    return render_template('pc.html', pc=pc)


@app.route('/gsp_groups')
def gsp_groups_get():
    return render_template(
        'gsp_groups.html', groups=GspGroup.query.order_by(GspGroup.code).all())


@app.route('/gsp_groups/<int:group_id>')
def gsp_group_get(group_id):
    sess = db.session()
    group = GspGroup.get_by_id(sess, group_id)
    return render_template('gsp_group.html', gsp_group=group)


@app.route('/sites/<int:site_id>/gen_graph')
def site_gen_graph_get(site_id):
    sess = db.session()
    year = req_int("finish_year")
    month = req_int("finish_month")
    months = req_int("months")

    finish_date = Datetime(year, month, 1)
    site = Site.get_by_id(sess, site_id)

    return render_template(
        'site_gen_graph.html', year=year, month=month, months=months,
        site=site, finish_date=finish_date)
    '''
    import sys
    from net.sf.chellow.monad import Monad
    import utils
    import db
    Monad.getUtils()['impt'](globals(), 'utils', 'db')
    inv, template = globals()['inv'], globals()['template']
    hh_format = utils.hh_format

    if sys.platform.startswith('java'):
        from java.awt.image import BufferedImage
        from javax.imageio import ImageIO
        from java.awt import Color, Font
        from java.lang import System
        import math
        import datetime
        import pytz
        from dateutil.relativedelta import relativedelta

        HH = utils.HH
        Site = db.Site

        colour_list = [
            Color.BLUE, Color.GREEN, Color.RED, Color.YELLOW, Color.MAGENTA,
            Color.CYAN, Color.PINK, Color.ORANGE]

        def set_colour(graphics, supplies, id):
            graphics.setColor(supplies[id][0])

        def add_colour(supplies, id, name, source_code):
            if id not in supplies:
                supplies[id] = [len(supplies), name, source_code]

        def sort_colour(supplies):
            keys = supplies.keys()
            keys.sort()
            for i in range(len(keys)):
                supplies[keys[i]][0] = colour_list[i]

        def paint_legend(supplies, graph_top):
            i = 0
            keys = supplies.keys()
            keys.sort()
            for key in keys:
                supply = supplies[key]
                graphics.setColor(supply[0])
                graphics.fillRect(12, int(graph_top + 15 + (10 * i)), 8, 8)
                graphics.setColor(Color.BLACK)
                graphics.drawString(
                    supply[2] + ' ' + supply[1], 25,
                    int(graph_top + 22 + (10 * i)))
                i = i + 1

        def minimum_scale(min_scale, max_scale):
            if min_scale == 0 and max_scale == 0:
                min_scale = 0
                max_scale = 10
            if min_scale < 0 and min_scale > -10:
                min_scale = -10
            if max_scale > 0 and max_scale < 10:
                max_scale = 10
            return min_scale, max_scale

        sess = None
        try:
            sess = db.session()

            start = System.currentTimeMillis()
            inv.getResponse().setContentType("image/png")
            site_id = inv.getLong("site_id")
            finish_date_year = inv.getInteger("finish_year")
            finish_date_month = inv.getInteger("finish_month")
            months = inv.getInteger("months")

            finish_date = datetime.datetime(
                finish_date_year, finish_date_month, 1,
                tzinfo=pytz.utc) + relativedelta(months=1) - HH

            start_date = datetime.datetime(
                finish_date_year, finish_date_month, 1,
                tzinfo=pytz.utc) - relativedelta(months=months-1)

            generated_supplies = {}
            imported_supplies = {}
            exported_supplies = {}
            maxHeight = 80
            pxStep = 10
            maxOverallScale = 0
            minOverallScale = 0
            maxExportedScale = 0
            minExportedScale = 0
            maxImportedScale = 0
            minImportedScale = 0
            maxGeneratedScale = 0
            maxParasiticScale = 0
            maxDisplacedScale = 0
            minDisplacedScale = 0
            maxUsedScale = 0
            minUsedScale = 0
            resultData = []
            actualStatus = 'A'

            site = Site.get_by_id(sess, site_id)
            groups = site.groups(sess, start_date, finish_date, True)
            for group in groups:
                rs = iter(
                    sess.execute(
                        "select hh_datum.value, hh_datum.start_date, "
                        "hh_datum.status, channel.imp_related, supply.name, "
                        "source.code, supply.id as supply_id "
                        "from hh_datum, channel, era, supply, source "
                        "where hh_datum.channel_id = channel.id "
                        "and channel.era_id = era.id "
                        "and era.supply_id = supply.id "
                        "and supply.source_id = source.id "
                        "and channel.channel_type = 'ACTIVE' "
                        "and hh_datum.start_date >= :start_date "
                        "and hh_datum.start_date <= :finish_date "
                        "and supply.id = any(:supply_ids) "
                        "order by hh_datum.start_date, supply.id",
                        params={
                            'start_date': group.start_date,
                            'finish_date': group.finish_date,
                            'supply_ids': [s.id for s in group.supplies]}))
                hh_date = group.start_date
                try:
                    row = rs.next()
                    hhChannelValue = float(row.value)
                    hhChannelStartDate = row.start_date
                    imp_related = row.imp_related
                    status = row.status
                    source_code = row.code
                    supply_name = row.name
                    supply_id = row.supply_id

                    while hh_date <= group.finish_date:
                        complete = "blank"
                        exportedValue = 0
                        importedValue = 0
                        parasiticValue = 0
                        generatedValue = 0
                        third_party_import = 0
                        third_party_export = 0
                        supplyList = []
                        while hhChannelStartDate == hh_date:
                            if not imp_related and \
                                    source_code in ('net', 'gen-net'):
                                exportedValue += hhChannelValue
                                add_colour(
                                    exported_supplies, supply_id, supply_name,
                                    source_code)
                            if imp_related and source_code in (
                                    'net', 'gen-net'):
                                importedValue += hhChannelValue
                                add_colour(
                                    imported_supplies, supply_id, supply_name,
                                    source_code)
                            if (imp_related and source_code == 'gen') or \
                                    (
                                            not imp_related and
                                            source_code == 'gen-net'):
                                generatedValue += hhChannelValue
                                add_colour(
                                    generated_supplies, supply_id, supply_name,
                                    source_code)
                            if (not imp_related and source_code == 'gen') or \
                                    (imp_related and source_code == 'gen-net'):
                                parasiticValue += hhChannelValue
                                add_colour(
                                    generated_supplies, supply_id, supply_name,
                                    source_code)
                            supplyList.append(
                                [
                                    supply_name, source_code, imp_related,
                                    hhChannelValue, supply_id])
                            if (
                                    imp_related and
                                    source_code == '3rd-party') or (
                                    not imp_related and
                                    source_code == '3rd-party-reverse'):
                                third_party_import += hhChannelValue
                            if (
                                    not imp_related and
                                    source_code == '3rd-party') or \
                                    (
                                        imp_related and
                                        source_code == '3rd-party-reverse'):
                                third_party_export += hhChannelValue
                            try:
                                row = rs.next()
                                source_code = row.code
                                supply_name = row.name
                                hhChannelValue = float(row.value)
                                hhChannelStartDate = row.start_date
                                imp_related = row.imp_related
                                status = row.status
                                supply_id = row.supply_id
                            except StopIteration:
                                hhChannelStartDate = None

                        maxExportedScale = max(maxExportedScale, exportedValue)
                        minExportedScale = min(minExportedScale, exportedValue)
                        maxImportedScale = max(maxImportedScale, importedValue)
                        minImportedScale = min(minImportedScale, importedValue)
                        maxGeneratedScale = max(
                            maxGeneratedScale, generatedValue)
                        maxParasiticScale = max(
                            maxParasiticScale, parasiticValue)
                        displacedValue = generatedValue - parasiticValue - \
                            exportedValue
                        maxDisplacedScale = max(
                            maxDisplacedScale, displacedValue)
                        minDisplacedScale = min(
                            minDisplacedScale, displacedValue)
                        usedValue = importedValue + displacedValue + \
                            third_party_import - third_party_export
                        maxUsedScale = max(maxUsedScale, usedValue)
                        minUsedScale = min(minUsedScale, usedValue)
                        resultData.append(
                            [hh_date, supplyList, usedValue, displacedValue])
                        hh_date += HH
                except StopIteration:
                    pass

                sort_colour(generated_supplies)
                sort_colour(imported_supplies)
                sort_colour(exported_supplies)
                minimized_scale = minimum_scale(
                    minExportedScale, maxExportedScale)
                minExportedScale = minimized_scale[0]
                maxExportedScale = minimized_scale[1]
                minimized_scale = minimum_scale(
                    minImportedScale, maxImportedScale)
                minImportedScale = minimized_scale[0]
                maxImportedScale = minimized_scale[1]
                if maxGeneratedScale == 0 and maxParasiticScale == 0:
                    maxGeneratedScale = 10
                    maxParasiticScale = 10
                minimized_scale = minimum_scale(minUsedScale, maxUsedScale)
                minUsedScale = minimized_scale[0]
                maxUsedScale = minimized_scale[1]
                minimized_scale = minimum_scale(
                    minDisplacedScale, maxDisplacedScale)
                minDisplacedScale = minimized_scale[0]
                maxDisplacedScale = minimized_scale[1]
                maxOverallScale = max(
                    maxExportedScale, maxImportedScale, maxGeneratedScale,
                    maxDisplacedScale, maxUsedScale)
                minOverallScale = min(
                    minExportedScale, minImportedScale, minDisplacedScale,
                    minUsedScale)
                rawStepOverall = (maxOverallScale * 2) / (maxHeight / pxStep)
                factorOverall = 10**int(math.floor(math.log10(rawStepOverall)))
                endOverall = rawStepOverall / factorOverall
                newEndOverall = 1
                if endOverall >= 2:
                    newEndOverall = 2
                if endOverall >= 5:
                    newEndOverall = 5
                stepOverall = newEndOverall * factorOverall
            if len(resultData) > 0:
                graphLeft = 180
                scaleFactorOverall = float(maxHeight) / maxOverallScale
                graphOrderExported = 5
                graphOrderImported = 4
                graphOrderGenerated = 3
                graphOrderUsed = 1
                graphOrderDisplaced = 2
                minUsed = 0
                minDisplaced = 0
                minParasitic = 0
                for i in range(0, int(minUsedScale), stepOverall * -1):
                    minUsed = min(minUsed, i)
                for i in range(0, int(minDisplacedScale), stepOverall * -1):
                    minDisplaced = min(minDisplaced, i)
                for i in range(0, int(maxParasiticScale), stepOverall):
                    minParasitic = max(minParasitic, i)
                minUsed = int(abs(minUsed) * scaleFactorOverall)
                minDisplaced = int(abs(minDisplaced) * scaleFactorOverall)
                minParasitic = int(abs(minParasitic) * scaleFactorOverall)
                graphTopExported = (
                    (graphOrderExported - 1) * (maxHeight + 22)) \
                    + 30 + minUsed + minDisplaced + minParasitic
                graphTopImported = (
                    (graphOrderImported - 1) * (maxHeight + 22)) + 30 + \
                    minUsed + minDisplaced + minParasitic
                graphTopGenerated = (
                    (graphOrderGenerated - 1) * (maxHeight + 22)) + 30 + \
                    minUsed + minDisplaced
                graphTopUsed = ((graphOrderUsed - 1) * (maxHeight + 22)) + 30
                graphTopDisplaced = (
                    (graphOrderDisplaced - 1) * (maxHeight + 22)) + 30 + \
                    minUsed
                image = BufferedImage(
                    graphLeft + len(resultData) + 100,
                    ((maxHeight + 22) * 5) + 60 + minUsed + minDisplaced +
                    minParasitic, BufferedImage.TYPE_4BYTE_ABGR)
                graphics = image.createGraphics()
                defaultFont = graphics.getFont()
                smallFont = Font(
                    defaultFont.getName(), defaultFont.getStyle(), 10)
                keyFont = Font(
                    defaultFont.getName(), defaultFont.getStyle(), 9)
                xAxisExported = int(
                    graphTopExported + maxOverallScale * scaleFactorOverall)
                xAxisImported = int(
                    graphTopImported + maxOverallScale * scaleFactorOverall)
                xAxisGenerated = int(
                    graphTopGenerated + maxOverallScale * scaleFactorOverall)
                xAxisUsed = int(
                    graphTopUsed + maxOverallScale * scaleFactorOverall)
                xAxisDisplaced = int(
                    graphTopDisplaced + maxOverallScale * scaleFactorOverall)
                monthPoints = []
                for i, dataHh in enumerate(resultData):
                    date = dataHh[0]
                    usedValue = dataHh[2]
                    displacedValue = dataHh[3]
                    dataHhSupplyList = dataHh[1]

                    hour = date.hour
                    minute = date.minute
                    graphics.setColor(Color.BLUE)
                    usedHeight = int(round(usedValue * scaleFactorOverall))
                    if usedHeight < 0:
                        graphics.fillRect(
                            graphLeft + i, xAxisUsed, 1, abs(usedHeight))
                    else:
                        graphics.fillRect(
                            graphLeft + i, xAxisUsed - usedHeight, 1,
                            usedHeight)
                    displacedHeight = int(
                        round(displacedValue * scaleFactorOverall))
                    if displacedHeight < 0:
                        graphics.fillRect(
                            graphLeft + i, xAxisDisplaced, 1,
                            abs(displacedHeight))
                    else:
                        graphics.fillRect(
                            graphLeft + i, xAxisDisplaced - displacedHeight,
                            1, displacedHeight)
                    generatedTotal = 0
                    parasiticTotal = 0
                    importedTotal = 0
                    exportedTotal = 0
                    for j in dataHhSupplyList:
                        name = j[0]
                        source = j[1]
                        isImport = j[2]
                        value = j[3]
                        id = j[4]
                        height = int(round(value * scaleFactorOverall))
                        if source in ('net', 'gen-net') and not isImport:
                            set_colour(graphics, exported_supplies, id)
                            exportedTotal = exportedTotal + height
                            graphics.fillRect(
                                graphLeft + i, xAxisExported - exportedTotal,
                                1, height)
                        if source in ('net', 'gen-net') and isImport:
                            set_colour(graphics, imported_supplies, id)
                            importedTotal = importedTotal + height
                            graphics.fillRect(
                                graphLeft + i, xAxisImported - importedTotal,
                                1, height)
                        if (isImport and source == 'gen') or \
                                (not isImport and source == 'gen-net'):
                            set_colour(graphics, generated_supplies, id)
                            generatedTotal = generatedTotal + height
                            graphics.fillRect(
                                graphLeft + i,
                                xAxisGenerated - generatedTotal, 1, height)
                        if (not isImport and source == 'gen') or \
                                (isImport and source == 'gen-net'):
                            set_colour(graphics, generated_supplies, id)
                            parasiticTotal = parasiticTotal + height
                            graphics.fillRect(
                                graphLeft + i, xAxisGenerated, 1, height)
                    if hour == 0 and minute == 0:
                        day = date.day
                        dayOfWeek = date.weekday()
                        if dayOfWeek > 4:
                            graphics.setColor(Color.RED)
                        else:
                            graphics.setColor(Color.BLACK)
                        graphics.drawString(
                            str(day), graphLeft + i + 16,
                            ((maxHeight + 22) * 5) + 30 + minUsed + \
                            minDisplaced + minParasitic)
                        graphics.setColor(Color.BLACK)
                        graphics.fillRect(
                            graphLeft + i, graphTopExported + maxHeight, 1, 5)
                        graphics.fillRect(
                            graphLeft + i, graphTopImported + maxHeight, 1, 5)
                        graphics.fillRect(
                            graphLeft + i, graphTopGenerated + maxHeight, 1, 5)
                        graphics.fillRect(
                            graphLeft + i, graphTopUsed + maxHeight, 1, 5)
                        graphics.fillRect(
                            graphLeft + i, graphTopDisplaced + maxHeight, 1, 5)
                        if day == 15:
                            graphics.drawString(
                                date.strftime("%B"), graphLeft + i + 16,
                                ((maxHeight + 22) * 5) + 50 + minUsed +
                                minDisplaced + minParasitic)
                            monthPoints.append(i)
                graphics.setColor(Color.BLACK)
                graphics.fillRect(graphLeft, graphTopExported, 1, maxHeight)
                graphics.fillRect(graphLeft, graphTopImported, 1, maxHeight)
                graphics.fillRect(
                    graphLeft, graphTopGenerated, 1, maxHeight + minParasitic)
                graphics.fillRect(
                    graphLeft, graphTopUsed, 1, maxHeight + minUsed)
                graphics.fillRect(
                    graphLeft, graphTopDisplaced, 1, maxHeight + minDisplaced)
                scalePointsExported = []
                for i in range(0, int(maxOverallScale), stepOverall):
                    scalePointsExported.append(i)
                graphics.setColor(Color.BLACK)
                for point in scalePointsExported:
                    graphics.fillRect(
                        graphLeft - 5,
                        int(xAxisExported - point * scaleFactorOverall),
                        len(resultData) + 5, 1)
                    graphics.drawString(
                        str(point * 2), graphLeft - 40,
                        int(xAxisExported - point * scaleFactorOverall + 5))
                    for monthPoint in monthPoints:
                        graphics.drawString(
                            str(point * 2), graphLeft + monthPoint + 16,
                            int(
                                xAxisExported - point *
                                scaleFactorOverall - 2))
                scalePointsImported = []
                for i in range(0, int(maxOverallScale), stepOverall):
                    scalePointsImported.append(i)
                graphics.setColor(Color.BLACK)
                for point in scalePointsImported:
                    graphics.fillRect(
                        graphLeft - 5,
                        int(xAxisImported - point * scaleFactorOverall),
                        len(resultData) + 5, 1)
                    graphics.drawString(
                        str(point * 2), graphLeft - 40,
                        int(xAxisImported - point * scaleFactorOverall + 5))
                    for monthPoint in monthPoints:
                        graphics.drawString(
                            str(point * 2), graphLeft + monthPoint + 16,
                            int(
                                xAxisImported - point *
                                scaleFactorOverall - 2))
                scalePointsGenerated = []
                for i in range(0, int(maxOverallScale), stepOverall):
                    scalePointsGenerated.append(i)
                for i in range(0, int(maxParasiticScale), stepOverall):
                    scalePointsGenerated.append(i * -1)
                graphics.setColor(Color.BLACK)
                for point in scalePointsGenerated:
                    graphics.fillRect(
                        graphLeft - 5,
                        int(xAxisGenerated - point * scaleFactorOverall),
                        len(resultData) + 5, 1)
                    graphics.drawString(
                        str(point * 2), graphLeft - 40,
                        int(xAxisGenerated - point * scaleFactorOverall + 5))
                    for monthPoint in monthPoints:
                        graphics.drawString(
                            str(point * 2), graphLeft + monthPoint + 16,
                            int(
                                xAxisGenerated - point * scaleFactorOverall -
                                2))
                scalePointsUsed = []
                for i in range(0, int(maxOverallScale), stepOverall):
                    scalePointsUsed.append(i)
                for i in range(0, int(minUsedScale), stepOverall * -1):
                    scalePointsUsed.append(i)
                for point in scalePointsUsed:
                    graphics.fillRect(
                        graphLeft - 5, int(
                            xAxisUsed - point * scaleFactorOverall),
                        len(resultData) + 5, 1)
                    graphics.drawString(
                        str(point * 2), graphLeft - 40,
                        int(xAxisUsed - point * scaleFactorOverall + 5))
                    for monthPoint in monthPoints:
                        graphics.drawString(
                            str(point * 2), graphLeft + monthPoint + 16,
                            int(xAxisUsed - point * scaleFactorOverall - 2))
                scalePointsDisplaced = []
                for i in range(0, int(maxOverallScale), stepOverall):
                    scalePointsDisplaced.append(i)
                for i in range(0, int(minDisplacedScale), stepOverall * -1):
                    scalePointsDisplaced.append(i)
                for point in scalePointsDisplaced:
                    graphics.fillRect(
                        graphLeft - 5,
                        int(xAxisDisplaced - point * scaleFactorOverall),
                        len(resultData) + 5, 1)
                    graphics.drawString(
                        str(point * 2), graphLeft - 40,
                        int(xAxisDisplaced - point * scaleFactorOverall + 5))
                    for monthPoint in monthPoints:
                        graphics.drawString(
                            str(point * 2), graphLeft + monthPoint + 16,
                            int(
                                xAxisDisplaced - point * scaleFactorOverall -
                                2))
                graphics.drawString(
                    "kW", graphLeft - 90, graphTopExported + 10)
                graphics.drawString(
                    "kW", graphLeft - 90, graphTopImported + 10)
                graphics.drawString(
                    "kW", graphLeft - 90, graphTopGenerated + 10)
                graphics.drawString("kW", graphLeft - 90, graphTopUsed + 10)
                graphics.drawString(
                    "kW", graphLeft - 90, graphTopDisplaced + 10)
                title = "Electricity at site " + site.code + " " + \
                    site.name + " for " + str(months) + " month"
                if months > 1:
                    title = title + "s"
                title += " up to and including " + \
                    (finish_date - HH).strftime("%B %Y")
                graphics.drawString(title, 30, 20)
                graphics.drawString("Imported", 10, graphTopImported + 10)
                graphics.drawString("Exported", 10, graphTopExported + 10)
                graphics.drawString("Generated", 10, graphTopGenerated + 10)
                graphics.drawString("Used", 10, graphTopUsed + 10)
                graphics.drawString("Displaced", 10, graphTopDisplaced + 10)
                graphics.setFont(smallFont)
                graphics.drawString(
                    "Poor data is denoted by a grey background and black "
                    "foreground.", 30,
                    ((maxHeight + 22) * 5) + 50 + minUsed + minDisplaced +
                    minParasitic)
                graphics.setFont(keyFont)
                paint_legend(exported_supplies, graphTopExported)
                paint_legend(imported_supplies, graphTopImported)
                paint_legend(generated_supplies, graphTopGenerated)
            else:
                image = BufferedImage(400, 400, BufferedImage.TYPE_4BYTE_ABGR)
                graphics = image.createGraphics()
                graphics.setColor(Color.BLACK)
                graphics.drawString(
                    "No data available for this period.", 30, 10)

            os = inv.getResponse().getOutputStream()
            graphics.setColor(Color.BLACK)
            ImageIO.write(image, "png", os)
            os.close()
        finally:
            if sess is not None:
                sess.close()
    else:
        from flask import Response

        inv.response = Response("Stub", status=200)
    '''
