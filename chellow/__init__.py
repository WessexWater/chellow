import os
from datetime import datetime as Datetime

import chellow.bank_holidays
import chellow.bsuos
import chellow.dloads
import chellow.g_cv
import chellow.hh_importer
import chellow.rcrc
import chellow.system_price
import chellow.tlms
import chellow.utils
import chellow.views
from chellow.models import (
    Contract, Session, User, UserRole, db_upgrade, start_sqlalchemy)
from chellow.utils import to_ct, utc_datetime_now

from flask import Flask, Response, g, make_response, render_template, request

from werkzeug.exceptions import NotFound

from zish import dumps

from ._version import get_versions


TEMPLATE_FORMATS = {
    'year': '%Y', 'month': '%m', 'day': '%d', 'hour': '%H',
    'minute': '%M', 'full': '%Y-%m-%d %H:%M', 'date': '%Y-%m-%d'}


def create_app(testing=False):
    app = Flask('chellow', instance_relative_config=True)
    app.secret_key = os.urandom(24)
    start_sqlalchemy()

    app.register_blueprint(chellow.views.views)
    chellow.utils.root_path = app.root_path

    if not testing:
        db_upgrade(app.root_path)
        chellow.rcrc.startup()
        chellow.bsuos.startup()
        chellow.system_price.startup()
        chellow.hh_importer.startup()
        chellow.tlms.startup()
        chellow.bank_holidays.startup()
        chellow.dloads.startup(app.instance_path)
        chellow.g_cv.startup()

    @app.before_first_request
    def before_first_request():
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

        chellow.utils.url_root = f'{scheme}://{host}/'

    @app.before_request
    def before_request():
        g.sess = Session()

        msg = ' '.join(
            '-' if v is None else v for v in (
                request.remote_addr, str(request.user_agent),
                request.remote_user,
                f"[{Datetime.now().strftime('%d/%b/%Y:%H:%M:%S')}]",
                f'"{request.method} {request.path} '
                f'{request.environ.get("SERVER_PROTOCOL")}"', None, None))
        print(msg)

    @app.before_request
    def check_permissions(*args, **kwargs):
        g.user = None
        config_contract = Contract.get_non_core_by_name(
            g.sess, 'configuration')
        props = config_contract.make_properties()
        ad_props = props.get('ad_authentication', {})
        ad_auth_on = ad_props.get('on', False)
        if ad_auth_on:
            username = request.headers['X-Isrw-Proxy-Logon-User'].upper()
            user = g.sess.query(User).filter(
                User.email_address == username).first()
            if user is None:
                try:
                    username = ad_props['default_user']
                    user = g.sess.query(User).filter(
                        User.email_address == username).first()
                except KeyError:
                    user = None
            if user is not None:
                g.user = user
        else:
            auth = request.authorization

            if auth is None:
                try:
                    ips = props['ips']
                    if request.remote_addr in ips:
                        key = request.remote_addr
                    elif '*.*.*.*' in ips:
                        key = '*.*.*.*'
                    else:
                        key = None

                    email = ips[key]
                    g.user = g.sess.query(User).filter(
                        User.email_address == email).first()
                except KeyError:
                    pass
            else:
                user = g.sess.query(User).filter(
                    User.email_address == auth.username).first()
                if user is not None and user.password_matches(auth.password):
                    g.user = user

        # Got our user
        path = request.path
        method = request.method
        if path in (
                '/health', '/nationalgrid/sf_bsuos.xls',
                '/nationalgrid/cv.csv',
                '/elexonportal/file/download/BESTVIEWPRICES_FILE', '/ecoes',
                '/elexonportal/file/download/TLM_FILE',
                '/elexonportal/file/download/RCRC_FILE',
                '/ecoes/NonDomesticCustomer/ExportPortfolioMPANs', '/hh_api'):
            return

        if g.user is not None:
            if 'X-Isrw-Proxy-Logon-User' in request.headers:
                g.user.proxy_username = \
                    request.headers['X-Isrw-Proxy-Logon-User'].upper()

            role = g.user.user_role
            role_code = role.code

            if role_code == "viewer" and (
                    method in ("GET", "HEAD") or path in (
                        '/reports/169', '/reports/187')):
                return
            elif role_code == "editor":
                return
            elif role_code == "party-viewer":
                if method in ("GET", "HEAD"):
                    party = g.user.party
                    market_role_code = party.market_role.code
                    if market_role_code in ('C', 'D'):
                        dc_contract_id = request.args["dc_contract_id"]
                        dc_contract = Contract.get_dc_by_id(
                            g.sess, dc_contract_id)
                        if dc_contract.party == party and \
                                request.full_path.startswith(
                                    "/channel_snags?"):
                            return
                    elif market_role_code == 'X':
                        if path.startswith("/supplier_contracts/" + party.id):
                            return

        if g.user is None and g.sess.query(User).count() == 0:
            g.sess.rollback()
            user_role = g.sess.query(UserRole).filter(
                UserRole.code == 'editor').one()
            User.insert(g.sess, 'admin@example.com', 'admin', user_role, None)
            g.sess.commit()
            return

        if g.user is None or (not ad_auth_on and auth is None):
            return Response(
                'Could not verify your access level for that URL.\n'
                'You have to login with proper credentials', 401,
                {'WWW-Authenticate': 'Basic realm="Chellow"'})

        config = Contract.get_non_core_by_name(g.sess, 'configuration')
        return make_response(
            render_template('403.html', properties=config.make_properties()),
            403)

    @app.context_processor
    def chellow_context_processor():
        global_alerts = []
        for task in chellow.hh_importer.tasks.values():
            if task.is_error:
                try:
                    contract = Contract.get_by_id(g.sess, task.contract_id)
                    global_alerts.append(
                        f"There's a problem with the automatic HH data "
                        f"importer for contract '{contract.name}'.")
                except NotFound:
                    pass

        for importer in (
                chellow.bsuos.bsuos_importer, chellow.g_cv.g_cv_importer):
            if importer is not None and importer.global_alert is not None:
                global_alerts.append(importer.global_alert)

        return {'current_user': g.user, 'global_alerts': global_alerts}

    @app.teardown_request
    def shutdown_session(exception=None):
        if getattr(g, 'sess', None) is not None:
            g.sess.close()

    @app.template_filter('hh_format')
    def hh_format_filter(dt, modifier='full'):
        if dt is None:
            return "Ongoing"
        else:
            return to_ct(dt).strftime(TEMPLATE_FORMATS[modifier])

    @app.template_filter('now_if_none')
    def now_if_none(dt):
        return utc_datetime_now() if dt is None else dt

    @app.template_filter('to_ct')
    def to_ct_filter(dt):
        return to_ct(dt)

    @app.template_filter('dumps')
    def dumps_filter(d):
        return dumps(d)

    return app


versions = get_versions()
__version__ = versions['version']
del get_versions
