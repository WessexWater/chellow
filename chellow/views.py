import sys
import hashlib
from flask import request, session
from chellow import app
from chellow.model import User, Report, Contract
import logging


@app.before_first_request
def check_permissions(*args, **kwargs):
    app.logger.error("checking permissions")
    method = request.method
    path = request.path

    if method == "GET" and path in ('/', '/static/style.css'):
        return None
    
    user = None
    is_default = False
    auth = request.authorization
    if auth is not None:
        pword_digest = hashlib.md5(auth.password).hexdigest() 
        user = User.query.filter(User.email_address==auth.username,
            User.password_digest==pword_digest).first()

    if user is None:
        config_contract = Contract.get_non_core_by_name('configuration')
        email = config_contract.make_properties()['ips'][request.remote_addr]
        user = User.query.filter(User.email_address==email).first()
        is_default = True

    if user is None:
        user_count = User.query.count()
        if user_count is None or user_count == 0 and \
                ipaddress.ip_address(request.remote_addr).is_loopback():
            return None
    else:
        role = user.role
        role_code = role.code
        if role_code == "viewer":
            if path_info.startswith("/reports/") and \
                    path_info.endswith("/output/") and \
                    request.method in ("GET", "HEAD"):
                return
        elif role_code == "editor":
            return
        elif role_code == "party-viewer":
            if request.method in ("GET", "HEAD"):
                party = user.party
                market_role_code = party.market_role.code
                if market_role_code == 'C':
                    hhdc_contract_id = args_int(request, "hhdc_contract_id")
                    hhdc_contract = Contract.get_non_core_by_id(
                        hhdc_contract_id)
                    if hhdc_contract.party == party and (
                            request.path_info + "?" + request.query_string) \
                            .startswith(
                                "/reports/37/output/?hhdc_contract_id="
                                + hhdc_contract.id):
                        return
                elif market_role_code == 'X':
                    if path_info.startswith(
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
def index():
    app.logger.error("hello")
    #n = 1 / 0
    return 'Hello World'

@app.route('/chellow/reports/<int:report_id>/output/', methods=['GET', 'POST'])
def show_report(report_id):
    report = Report.query.get(report_id)
    exec(report.script, {'request': request, 'template': report.template})

@app.route('/add_user', methods=['POST'])
def add_user_post():
    return 'Hello Worlds'
