import hashlib
from flask import request, Response, g, redirect, render_template
from werkzeug.exceptions import BadRequest
from chellow import app
from chellow.models import Contract, Report, User, set_read_write, db
from sqlalchemy.exc import ProgrammingError
import traceback


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
    fm = request.form
    return name in fm and fm[name] == 'true'


@app.before_request
def check_permissions(*args, **kwargs):
    path = request.path

    g.user = None
    user = None
    auth = request.authorization
    if auth is not None:
        pword_digest = hashlib.md5(auth.password).hexdigest()
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
            if path.startswith("/reports/") and \
                    path.endswith("/output/") and \
                    request.method in ("GET", "HEAD"):
                return
        elif role_code == "editor":
            return
        elif role_code == "party-viewer":
            if request.method in ("GET", "HEAD"):
                party = user.party
                market_role_code = party.market_role.code
                if market_role_code == 'C':
                    hhdc_contract_id = GET_int("hhdc-contract-id")
                    hhdc_contract = Contract.get_hhdc_by_id(hhdc_contract_id)
                    if hhdc_contract.party == party and (
                            request.path + "?" + request.query_string) \
                            .startswith(
                                "/chellow/reports/37/output/?hhdc-contract-id="
                                + str(hhdc_contract.id)):
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
    return redirect("/chellow/reports/1/output/")


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
        self.response = redirect(
            ''.join((request.url_root, 'chellow', location)), 303)

    def sendTemporaryRedirect(self, location):
        self.response = redirect(
            ''.join((request.url_root, 'chellow', location)), 307)

    def sendNotFound(self, message):
        self.response = Response(message, status=404)

    def getFileItem(self, name):
        return ChellowFileItem(self.request.files[name])


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
    is_core = POST_bool('is-core')
    name = POST_str("name")
    report = Report(None, is_core, name, "", None)
    db.session.add(report)
    try:
        db.session.commit()
    except ProgrammingError, e:
        if 'duplicate key value violates unique constraint' in str(e):
            return Response(
                "There's already a report with that name.", status=400)
        else:
            raise
    return redirect('/chellow/reports/' + str(report.id) + '/', 303)


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
        return redirect('/chellow/reports/' + str(report.id) + '/', 303)
    except:
        return render_template(
            'report.html', report=report, message=traceback.format_exc())


@app.errorhandler(500)
def error_500(error):
    return traceback.format_exc(), 500


@app.errorhandler(RuntimeError)
def error_runtime(error):
    #return traceback.format_exc(), 500
    return "called rtime handler " + str(error), 500
