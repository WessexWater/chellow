import hashlib
from flask import request, Response, g, redirect, render_template, send_file
from werkzeug.exceptions import BadRequest
from chellow import app
from chellow.models import Contract, Report, User, set_read_write, db
from sqlalchemy.exc import ProgrammingError
import traceback
import datetime
import os
import subprocess


def GET_str(name):
    args = request.args
    if name in args:
        return request.args[name]
    else:
        raise BadRequest("The GET arg " + name + " is required.")


def GET_int(name):
    val_str = GET_str(name)
    return int(val_str)


def POST_str(name):
    return request.form[name]


def POST_bool(name):
    return POST_has_param(name) and request.form[name] == 'true'


def POST_has_param(name):
    return name in request.form


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
        config_contract = Contract.get_non_core_by_name('configuration')
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
                    hhdc_contract_id = GET_int("hhdc-contract-id")
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


@app.route('/')
def home():
    return chellow_redirect("/chellow/reports/1/output/")


el_dir = {
    'SYSPRICE': 'sysprice'
}


@app.route('/bmreports')
def bmreports():
    element = GET_str('element')
    date_str = GET_str('dT')
    fname = datetime.datetime.strptime(date_str, '%Y-%M-%d'). \
        strftime('%Y_%M_%d') + '.xml'
    f = open(
        os.path.join(
            os.path.dirname(__file__), 'bmreports', el_dir[element], fname))

    return Response(f, status=200, mimetype='text/xml')


@app.route('/elexonportal/file/download/BESTVIEWPRICES_FILE')
def elexonportal():
    key = GET_str('key')
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


class ChellowRequest():
    def __init__(self, request):
        self.request = request

    def getMethod(self):
        return self.request.method

    def getParameter(self, name):
        vals = self.request.values
        return vals[name] if name in vals else None


class Invocation():
    def __init__(self, request, user):
        self.request = request
        self.user = user
        self.req = ChellowRequest(request)

    def getUser(self):
        return self.user

    def hasParameter(self, name):
        return name in self.request.values

    def getString(self, name):
        if name in self.request.values:
            return self.request.values[name]
        else:
            return None

    def getBoolean(self, name):
        vals = self.request.values
        return name in vals and vals[name] == 'true'

    def getLong(self, name):
        return int(self.getString(name))

    def getInteger(self, name):
        return int(self.getString(name))

    def getRequest(self):
        return self.req

    def getResponse(self):
        return self.res

    def sendSeeOther(self, location):
        self.response = chellow_redirect(''.join(('/chellow', location)), 303)

    def sendTemporaryRedirect(self, location):
        self.response = chellow_redirect(''.join(('/chellow', location)), 307)

    def sendNotFound(self, message):
        self.response = Response(message, status=404)

    def getFileItem(self, name):
        return ChellowFileItem(self.request.files[name])

    def getMethod(self):
        return self.request.method


@app.route('/chellow/reports/<int:report_id>/output/', methods=['GET', 'POST'])
def show_report(report_id):
    report = Report.query.get(report_id)
    inv = Invocation(request, g.user)
    try:
        exec(report.script, {'inv': inv, 'template': report.template})
        return inv.response
    except:
        return Response(traceback.format_exc(), status=500)


@app.route('/chellow/reports/', methods=['GET'])
def show_reports():
    reports = Report.query.order_by(Report.id % 2, Report.name).all()
    return render_template('reports.html', reports=reports)


@app.route('/chellow/reports/', methods=['POST'])
def add_report():
    set_read_write()
    is_core = POST_bool('is_core')
    name = POST_str("name")
    report = Report(None, is_core, name, "", None)
    db.session.add(report)
    try:
        db.session.commit()
    except ProgrammingError as e:
        if 'duplicate key value violates unique constraint' in str(e):
            return Response(
                "There's already a report with that name.", status=400)
        else:
            raise
    return chellow_redirect('/chellow/reports/' + str(report.id) + '/', 303)


@app.route('/chellow/reports/<int:report_id>/', methods=['GET'])
def show_edit_report(report_id):
    report = Report.query.get(report_id)
    return render_template('report.html', report=report)


@app.route('/chellow/reports/<int:report_id>/', methods=['POST'])
def edit_report(report_id):
    try:
        set_read_write()
        name = POST_str("name")
        script = POST_str("script")
        template = POST_str("template")
        report = Report.query.get(report_id)
        report.update(name, script, template)
        db.session.commit()
        return chellow_redirect(
            '/chellow/reports/' + str(report.id) + '/', 303)
    except:
        return render_template(
            'report.html', report=report, message=traceback.format_exc())


@app.route('/system/', methods=['GET'])
def system_get():
    return render_template('system.html')


@app.route('/system/', methods=['POST'])
def system_post():
    if POST_has_param('upgrade'):
        out = subprocess.check_output(
            ["pip", "install", "--upgrade", "chellow"],
            stderr=subprocess.STDOUT)
        return render_template('system.html', subprocess=out)
    elif POST_has_param('restart'):
        restart_path = os.path.join(app.instance_path, 'restart')
        with open(restart_path, 'a'):
            os.utime(restart_path, None)
        flag_path = os.path.join(app.instance_path, 'keep_running')
        if os.path.exists(flag_path):
            os.remove(flag_path)
        return render_template('system.html', messages=["Restart requested."])


@app.errorhandler(500)
def error_500(error):
    return traceback.format_exc(), 500


@app.errorhandler(RuntimeError)
def error_runtime(error):
    return "called rtime handler " + str(error), 500
