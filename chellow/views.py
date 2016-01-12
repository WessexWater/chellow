import hashlib
from flask import (
    request, Response, g, redirect, render_template, send_file, flash,
    make_response)
from chellow import app
from chellow.models import (
    Contract, Report, User, set_read_write, db, Party, MarketRole, Participant,
    UserRole, Site, Source, GeneratorType, GspGroup, Era, SiteEra, Pc, Cop,
    Ssc, RateScript, Supply, Mtc, Channel, Tpr, MeasurementRequirement, Bill,
    RegisterRead, HhDatum, Snag, Batch)
from sqlalchemy.exc import ProgrammingError
import traceback
from datetime import datetime as Datetime
import os
import subprocess
import pytz
from dateutil.relativedelta import relativedelta
from chellow.utils import (
    HH, req_str, req_int, req_date, parse_mpan_core, req_bool, req_hh_date,
    hh_after, req_decimal)
from werkzeug.exceptions import BadRequest
import chellow.general_import
import io
import chellow.hh_importer
import chellow.bill_importer
from sqlalchemy import text, true, false, null
from collections import defaultdict
from itertools import chain
import importlib


APPLICATION_ROOT = app.config['APPLICATION_ROOT']
CONTEXT_PATH = '' if APPLICATION_ROOT is None else APPLICATION_ROOT


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
    # sys.stderr.write("about to check permissions sys\n")
    path = request.path
    method = request.method
    if method == 'GET' and path in (
            '/health', '/bmreports',
            '/elexonportal/file/download/BESTVIEWPRICES_FILE'):
        return

    g.user = None
    user = None
    auth = request.authorization
    if auth is not None:
        pword_digest = hashlib.md5(auth.password.encode()).hexdigest()
        user = User.query.filter(
            User.email_address == auth.username,
            User.password_digest == pword_digest).first()

    if user is None:
        config_contract = Contract.get_non_core_by_name(
            db.session, 'configuration')
        try:
            email = config_contract.make_properties()['ips'][
                request.remote_addr]
            user = User.query.filter(User.email_address == email).first()
        except KeyError:
            pass

    if user is not None:
        g.user = user
        role = user.user_role
        role_code = role.code
        path = request.path

        if role_code == "viewer":
            if path.startswith("/chellow/reports/") and \
                    path.endswith("/output/") and method in ("GET", "HEAD"):
                return
        elif role_code == "editor":
            return
        elif role_code == "party-viewer":
            if method in ("GET", "HEAD"):
                party = user.party
                market_role_code = party.market_role.code
                if market_role_code == 'C':
                    hhdc_contract_id = request.args["hhdc-contract-id"]
                    hhdc_contract = Contract.get_hhdc_by_id(hhdc_contract_id)
                    if hhdc_contract.party == party and (
                            request.full_path).startswith(
                                "/chellow/reports/37/output/?"
                                "hhdc-contract-id=" + str(hhdc_contract.id)):
                        return
                elif market_role_code == 'X':
                    if path.startswith(
                            "/supplier_contracts/" + party.id):
                        return

    if user is None:
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Chellow"'})
    else:
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
    return 'healthy\n'


class ChellowFileItem():
    def __init__(self, f):
        self.f = f

    def getName(self):
        return self.f.filename


@app.route('/local_reports/<int:report_id>/output/', methods=['POST'])
def show_local_report(report_id):
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
def show_reports():
    reports = Report.query.order_by(Report.id, Report.name).all()
    return render_template('reports.html', reports=reports)


@app.route('/local_reports', methods=['POST'])
def add_local_report():
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


@app.route('/system')
def system_get():
    return render_template('system.html')


@app.route('/system', methods=['POST'])
def system_post():
    if 'upgrade' in request.values:
        out = subprocess.check_output(
            ["pip", "install", "--upgrade", "chellow"],
            stderr=subprocess.STDOUT)
        return render_template('system.html', subprocess=out)
    elif 'restart' in request.values:
        restart_path = os.path.join(app.instance_path, 'restart')
        with open(restart_path, 'a'):
            os.utime(restart_path, None)
        flag_path = os.path.join(app.instance_path, 'keep_running')
        if os.path.exists(flag_path):
            os.remove(flag_path)
        return render_template('system.html', messages=["Restart requested."])


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
        return redirect('/chellow/users/' + str(user.id), 303)
    except BadRequest as e:
        sess.rollback()
        flash(e.description)
        users = sess.query(User).order_by(User.email_address).all()
        parties = sess.query(Party).join(MarketRole).join(Participant). \
            order_by(MarketRole.code, Participant.code).all()
        return make_response(
            render_template('users.html', users=users, parties=parties), 400)


@app.route('/users/<int:user_id>', methods=['POST'])
def user_post(user_id):
    try:
        sess = db.session
        set_read_write(sess)
        user = User.get_by_id(sess, user_id)
        if 'delete' in request.values:
            sess.delete(user)
            sess.commit()
            return redirect('/users/', 303)
        elif 'current_password' in request.values:
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
            return redirect('/sites/' + str(site.id))
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
        return render_template(
            'site_edit.html', site=site, sources=sources,
            generator_types=generator_types, gsp_groups=gsp_groups, eras=eras,
            mop_contracts=mop_contracts, hhdc_contracts=hhdc_contracts,
            supplier_contracts=supplier_contracts, pcs=pcs, cops=cops)


@app.route('/sites/add', methods=['POST'])
def sites_add_post():
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
        return render_template('sites_add.html')


@app.route('/sites/add')
def sites_add_get():
    return render_template('sites_add.html')


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


@app.route('/hhdc_contracts/<int:hhdc_contract_id>/edit', methods=['POST'])
def hhdc_contract_edit_post(hhdc_contract_id):
    sess = None
    hhdc_contract = None
    try:
        sess = db.session()
        set_read_write(sess)
        hhdc_contract = Contract.get_hhdc_by_id(sess, hhdc_contract_id)
        if 'update_state' in request.form:
            state = req_str("state")
            hhdc_contract.state = state
            sess.commit()
            return redirect('/hhdc_contracts/' + str(hhdc_contract.id), 303)
        elif 'ignore_snags' in request.form:
            ignore_date = req_date('ignore')
            sess.execute(
                text(
                    "update snag set is_ignored = true from channel, era "
                    "where snag.channel_id = channel.id "
                    "and channel.era_id = era.id "
                    "and era.hhdc_contract_id = :contract_id "
                    "and snag.finish_date < :ignore_date"),
                params=dict(
                    hhdc_contract_id=hhdc_contract.id,
                    ignore_date=ignore_date))
            sess.commit()
            return redirect("/hhdc_contracts/" + str(hhdc_contract.id), 303)
        elif 'delete' in request.form:
            hhdc_contract.delete(sess)
            sess.commit()
            return redirect('/hhdc_contracts', 303)
        else:
            party_id = req_str('party_id')
            name = req_str("name")
            charge_script = req_str("charge_script")
            properties = req_str("properties")
            party = Party.get_by_id(sess, party_id)
            hhdc_contract.update(False, name, party, charge_script, properties)
            sess.commit()
            return redirect('/hhdc_contracts/' + str(hhdc_contract.id), 303)
    except BadRequest as e:
        flash(e.description)
        if hhdc_contract is None:
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
            return redirect(
                '/supplier_contracts/' + str(contract.id))
    except BadRequest as e:
        sess.rollback()
        description = e.description
        flash(description)
        if description.startswith("There isn't a contract"):
            raise
        else:
            parties = Party.query.join(MarketRole, Participant).filter(
                MarketRole.code == 'X').order_by(Participant.code).all()
            return render_template(
                'supplier_contract_edit_get.html',
                contract=contract, parties=parties)


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


@app.route('/supplier_rate_scripts/add')
def supplier_rate_script_add_get():
    now = Datetime.now(pytz.utc)
    initial_date = Datetime(now.year, now.month, 1, tzinfo=pytz.utc)
    sess = db.session()
    contract_id = req_int('supplier_contract_id')
    contract = Contract.get_supplier_by_id(sess, contract_id)
    return render_template(
        'supplier_rate_script_add.html', now=now, contract=contract,
        initial_date=initial_date)


@app.route('/supplier_rate_scripts/add', methods=['POST'])
def supplier_rate_script_add_post():
    try:
        sess = db.session()
        set_read_write(sess)
        contract_id = req_int('supplier_contract_id')
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

            if 'imp_mpan_core':
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
            "and e1.start_date = sq.max_start_date limit :max_results").params(
            pattern="%" + pattern + "%",
            reducedPattern="%" + reduced_pattern + "%",
            max_results=max_results).all()
        if len(eras) == 1:
            return redirect("/supplies/" + str(eras[0].supply.id))
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
